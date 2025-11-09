"""
Recipe formatter for meal planning training data.
Transforms recipe datasets into conversation format for fine-tuning.
"""
import json
import random
from typing import Dict, List, Any, Optional


class RecipeFormatter:
    """Formats recipes into training data for meal planning tasks."""
    
    def __init__(self):
        self.meal_types = ["breakfast", "lunch", "dinner", "snack", "dessert"]
        self.constraint_templates = {
            "dietary": ["no dairy", "no gluten", "vegetarian", "vegan", "keto", "paleo"],
            "calorie": ["under 500 calories", "under 600 calories", "under 400 calories", "under 300 calories"],
            "preference": ["can include tofu", "prefer chicken", "prefer fish", "prefer vegetables"]
        }
    
    def format_meal_plan_query(self, recipe: Dict[str, Any], meal_type: str = None) -> Dict[str, Any]:
        """
        Format a recipe into a meal planning query-response pair.
        
        Args:
            recipe: Recipe dictionary with name, ingredients, instructions, etc.
            meal_type: Type of meal (breakfast, lunch, dinner, etc.)
        
        Returns:
            Dictionary with formatted conversation for meal planning
        """
        if meal_type is None:
            meal_type = random.choice(self.meal_types)
        
        # Extract recipe information
        recipe_name = recipe.get("name", "Unknown Recipe")
        ingredients = recipe.get("ingredients", [])
        instructions = recipe.get("instructions", "")
        calories = recipe.get("calories", None)
        
        # Generate constraints based on recipe
        constraints = self._generate_constraints_from_recipe(recipe)
        constraint_text = ", ".join(constraints) if constraints else ""
        
        # Create user query
        if constraint_text:
            user_query = f"What can I make for {meal_type}? {constraint_text}"
        else:
            user_query = f"What can I make for {meal_type}?"
        
        # Format ingredients list
        ingredients_list = self._format_ingredients_list(ingredients)
        
        # Create assistant response with structured format
        assistant_response = self._format_meal_plan_response(
            meal_type=meal_type,
            recipe_name=recipe_name,
            ingredients=ingredients_list,
            instructions=instructions,
            calories=calories,
            constraints=constraints
        )
        
        return {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an AI meal planning assistant that generates meal plans and recipes "
                        "based on user constraints. Always include a complete list of ingredients "
                        "needed for each recipe in your response."
                    )
                },
                {"role": "user", "content": user_query},
                {"role": "assistant", "content": assistant_response}
            ]
        }
    
    def format_recipe_generation_query(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a recipe into an ingredient-based recipe generation query-response pair.
        
        Args:
            recipe: Recipe dictionary with name, ingredients, instructions, etc.
        
        Returns:
            Dictionary with formatted conversation for recipe generation
        """
        ingredients = recipe.get("ingredients", [])
        recipe_name = recipe.get("name", "Unknown Recipe")
        instructions = recipe.get("instructions", "")
        calories = recipe.get("calories", None)
        
        # Format ingredients list for query
        ingredients_text = ", ".join([ing.get("name", ing) if isinstance(ing, dict) else str(ing) for ing in ingredients[:10]])
        
        # Generate constraints
        constraints = self._generate_constraints_from_recipe(recipe)
        constraint_text = ", ".join(constraints) if constraints else ""
        
        # Create user query
        if constraint_text:
            user_query = f"Generate a recipe using: {ingredients_text}. Constraints: {constraint_text}"
        else:
            user_query = f"Generate a recipe using: {ingredients_text}"
        
        # Format assistant response
        ingredients_list = self._format_ingredients_list(ingredients)
        assistant_response = self._format_recipe_response(
            recipe_name=recipe_name,
            ingredients=ingredients_list,
            instructions=instructions,
            calories=calories
        )
        
        return {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an AI recipe generation assistant. Given a list of ingredients "
                        "and optional constraints, generate a complete recipe with ingredients list "
                        "and step-by-step instructions."
                    )
                },
                {"role": "user", "content": user_query},
                {"role": "assistant", "content": assistant_response}
            ]
        }
    
    def _generate_constraints_from_recipe(self, recipe: Dict[str, Any]) -> List[str]:
        """Generate realistic constraints based on recipe content."""
        constraints = []
        
        # Check for dietary restrictions based on ingredients
        ingredients_text = " ".join([
            str(ing.get("name", ing) if isinstance(ing, dict) else ing).lower() 
            for ing in recipe.get("ingredients", [])
        ])
        
        # Add dietary constraints
        if "dairy" not in ingredients_text and "cheese" not in ingredients_text and "milk" not in ingredients_text:
            if random.random() < 0.3:
                constraints.append("no dairy")
        
        if "meat" not in ingredients_text and "chicken" not in ingredients_text and "beef" not in ingredients_text:
            if random.random() < 0.4:
                constraints.append("vegetarian")
        
        # Add calorie constraints
        calories = recipe.get("calories")
        if calories:
            if calories < 300:
                constraints.append("under 300 calories")
            elif calories < 400:
                constraints.append("under 400 calories")
            elif calories < 500:
                constraints.append("under 500 calories")
            elif calories < 600:
                constraints.append("under 600 calories")
        
        return constraints
    
    def _format_ingredients_list(self, ingredients: List[Any]) -> str:
        """Format ingredients list into a readable string."""
        formatted = []
        for ing in ingredients:
            if isinstance(ing, dict):
                name = ing.get("name", "")
                amount = ing.get("amount", "")
                unit = ing.get("unit", "")
                if amount and unit:
                    formatted.append(f"- {amount} {unit} {name}")
                elif amount:
                    formatted.append(f"- {amount} {name}")
                else:
                    formatted.append(f"- {name}")
            else:
                formatted.append(f"- {ing}")
        return "\n".join(formatted)
    
    def _format_meal_plan_response(
        self, 
        meal_type: str, 
        recipe_name: str, 
        ingredients: str, 
        instructions: str,
        calories: Optional[int],
        constraints: List[str]
    ) -> str:
        """Format meal plan response with structured information."""
        response = f"Here's a {meal_type} meal plan:\n\n"
        response += f"**Recipe: {recipe_name}**\n\n"
        response += f"**Ingredients needed:**\n{ingredients}\n\n"
        response += f"**Instructions:**\n{instructions}\n"
        
        if calories:
            response += f"\n**Calories:** {calories}"
        
        if constraints:
            response += f"\n**Constraints met:** {', '.join(constraints)}"
        
        return response
    
    def _format_recipe_response(
        self,
        recipe_name: str,
        ingredients: str,
        instructions: str,
        calories: Optional[int]
    ) -> str:
        """Format recipe generation response."""
        response = f"**Recipe: {recipe_name}**\n\n"
        response += f"**Ingredients:**\n{ingredients}\n\n"
        response += f"**Instructions:**\n{instructions}\n"
        
        if calories:
            response += f"\n**Calories:** {calories}"
        
        return response

