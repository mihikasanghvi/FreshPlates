"""
FastAPI service for AI Meal Planner
Integrates SageMaker endpoint inference + Amazon Fresh shopping links
and serves the frontend (HTML + CSS + JS).
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import sys
import json
from sagemaker.predictor import Predictor
from sagemaker.serializers import JSONSerializer
from sagemaker.deserializers import JSONDeserializer

# --- Import ingredient mapper ---
base_path = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(base_path)
from integration.ingredient_mapper import IngredientMapper


# --------------------------------------------------------------------
# App initialization
# --------------------------------------------------------------------
app = FastAPI(title="AI Meal Planner API", version="1.0.0")

# CORS (so frontend JS can call API endpoints)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, set specific domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from frontend/
#frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend')
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
print(f"📁 Frontend path: {frontend_path}")
print(f"📁 Frontend exists: {os.path.exists(frontend_path)}")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# --------------------------------------------------------------------
# Global variables
# --------------------------------------------------------------------
sagemaker_endpoint_name = os.environ.get("SAGEMAKER_ENDPOINT_NAME")
predictor = None
ingredient_mapper = None


# --------------------------------------------------------------------
# Data models
# --------------------------------------------------------------------
class MealPlanRequest(BaseModel):
    query: str
    constraints: Optional[List[str]] = None
    include_shopping_links: bool = True


class RecipeRequest(BaseModel):
    ingredients: List[str]
    constraints: Optional[List[str]] = None
    include_shopping_links: bool = True


class ShoppingListRequest(BaseModel):
    ingredients: List[str]


# --------------------------------------------------------------------
# Startup event
# --------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    """Initialize SageMaker predictor + ingredient mapper."""
    global predictor, ingredient_mapper

    # Connect to SageMaker endpoint
    if sagemaker_endpoint_name:
        try:
            predictor = Predictor(
                endpoint_name=sagemaker_endpoint_name,
                serializer=JSONSerializer(),
                deserializer=JSONDeserializer(),
            )
            print(f"✅ Connected to SageMaker endpoint: {sagemaker_endpoint_name}")
        except Exception as e:
            print(f"⚠️ Warning: Could not connect to SageMaker endpoint: {e}")

    # Initialize Ingredient Mapper
    try:
        ingredient_mapper = IngredientMapper()
        print("✅ Ingredient mapper initialized successfully")
    except Exception as e:
        print(f"⚠️ Warning: Could not initialize ingredient mapper: {e}")
        ingredient_mapper = None


# --------------------------------------------------------------------
# Helper functions
# --------------------------------------------------------------------
def call_sagemaker_endpoint(prompt: str) -> str:
    """Send inference request to SageMaker model."""
    if not predictor:
        raise HTTPException(
            status_code=503,
            detail="SageMaker endpoint not configured. Set SAGEMAKER_ENDPOINT_NAME environment variable.",
        )

    try:
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 400,
                "temperature": 0.7,
                "top_p": 0.9,
                "do_sample": True,
            },
        }

        response = predictor.predict(payload)

        # Extract generated text
        if isinstance(response, list) and len(response) > 0:
            if isinstance(response[0], dict):
                return response[0].get("generated_text", "")
            return str(response[0])
        elif isinstance(response, dict):
            return response.get("generated_text", "")
        else:
            return str(response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SageMaker call failed: {str(e)}")


def extract_ingredients_from_response(response_text: str) -> List[str]:
    """Parse ingredients from model output text."""
    ingredients = []
    lines = response_text.split("\n")
    in_section = False

    for line in lines:
        line_lower = line.lower()
        if "ingredient" in line_lower and ("**" in line or ":" in line):
            in_section = True
            continue

        if in_section:
            if line.strip().startswith("-") or line.strip()[0:1].isdigit():
                item = (
                    line.strip()
                    .lstrip("-")
                    .lstrip("0123456789. ")
                    .strip()
                )
                if item:
                    ingredients.append(item)
            if "instruction" in line_lower or "step" in line_lower:
                break

    return ingredients


# --------------------------------------------------------------------
# API routes
# --------------------------------------------------------------------
@app.post("/plan")
async def generate_meal_plan(request: MealPlanRequest):
    """Generate a meal plan from a natural language query."""
    constraints_text = ", ".join(request.constraints) if request.constraints else ""
    if constraints_text:
        prompt = f"User: {request.query} Constraints: {constraints_text}\nAssistant:"
    else:
        prompt = f"User: {request.query}\nAssistant:"

    response_text = call_sagemaker_endpoint(prompt)
    ingredients = extract_ingredients_from_response(response_text)

    shopping_links = {}
    if request.include_shopping_links and ingredient_mapper and ingredients:
        try:
            urls = ingredient_mapper.map_ingredients_to_urls(ingredients)
            for name, url_info in urls.items():
                shopping_links[name] = {
                    "url": url_info.get("amazon_fresh_url"),
                    "ingredient": url_info.get("ingredient"),
                }
        except Exception as e:
            print(f"⚠️ Shopping link generation failed: {e}")

    return {
        "meal_plan": response_text,
        "ingredients": ingredients,
        "shopping_links": shopping_links or None,
    }


@app.post("/recipe")
async def generate_recipe(request: RecipeRequest):
    """Generate a recipe using specific ingredients."""
    ingredients_text = ", ".join(request.ingredients)
    constraints_text = ", ".join(request.constraints) if request.constraints else ""
    if constraints_text:
        prompt = f"User: Generate a recipe using {ingredients_text}. Constraints: {constraints_text}\nAssistant:"
    else:
        prompt = f"User: Generate a recipe using {ingredients_text}\nAssistant:"

    response_text = call_sagemaker_endpoint(prompt)

    shopping_links = {}
    if request.include_shopping_links and ingredient_mapper:
        try:
            urls = ingredient_mapper.map_ingredients_to_urls(request.ingredients)
            for name, url_info in urls.items():
                shopping_links[name] = {
                    "url": url_info.get("amazon_fresh_url"),
                    "ingredient": url_info.get("ingredient"),
                }
        except Exception as e:
            print(f"⚠️ Shopping link generation failed: {e}")

    return {
        "recipe": response_text,
        "shopping_links": shopping_links or None,
    }


@app.post("/ingredients/shop")
async def get_shopping_links(request: ShoppingListRequest):
    """Return Amazon Fresh URLs for given ingredients."""
    if not ingredient_mapper:
        raise HTTPException(status_code=503, detail="Ingredient mapper unavailable")

    try:
        shopping_list = ingredient_mapper.generate_shopping_list(request.ingredients)
        return {"shopping_list": shopping_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating list: {str(e)}")


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "sagemaker_endpoint": sagemaker_endpoint_name or "not configured",
        "ingredient_mapper": "configured" if ingredient_mapper else "not configured",
    }


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the frontend homepage."""
    index_file = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>AI Meal Planner</h1><p>Frontend not found.</p>")


# --------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
