"""
Prepare recipe dataset from local CSV files.
Uses RecipeNLG CSV and FoodData Central for nutritional information.
"""
import json
import pandas as pd
import ast
import sys
import os
sys.path.append(os.path.dirname(__file__))
from recipe_formatter import RecipeFormatter
import argparse
from typing import List, Dict, Any, Optional


def load_recipe_csv(csv_path: str, num_samples: int = None) -> pd.DataFrame:
    """Load RecipeNLG CSV file."""
    print(f"Loading recipes from {csv_path}")
    
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} recipes from CSV")
    
    if num_samples:
        df = df.head(num_samples)
        print(f"Using first {len(df)} recipes")
    
    return df


def load_nutrition_data(food_data_dir: str) -> Dict[str, pd.DataFrame]:
    """Load FoodData Central CSV files."""
    print(f"Loading nutrition data from {food_data_dir}")
    
    nutrition_data = {}
    
    try:
        # Load food descriptions
        food_df = pd.read_csv(os.path.join(food_data_dir, "food.csv"))
        nutrition_data['food'] = food_df
        print(f"Loaded {len(food_df)} food items")
        
        # Load nutrients
        nutrient_df = pd.read_csv(os.path.join(food_data_dir, "nutrient.csv"))
        nutrition_data['nutrient'] = nutrient_df
        print(f"Loaded {len(nutrient_df)} nutrients")
        
        # Load food-nutrient relationships
        food_nutrient_df = pd.read_csv(os.path.join(food_data_dir, "food_nutrient.csv"))
        nutrition_data['food_nutrient'] = food_nutrient_df
        print(f"Loaded {len(food_nutrient_df)} food-nutrient relationships")
        
    except Exception as e:
        print(f"Warning: Could not load nutrition data: {e}")
        nutrition_data = {}
    
    return nutrition_data


def parse_recipe_ingredients(ingredients_str: str) -> List[str]:
    """Parse ingredients string from CSV format."""
    try:
        # The ingredients are stored as string representation of list
        ingredients_list = ast.literal_eval(ingredients_str)
        return [ing.strip() for ing in ingredients_list if ing.strip()]
    except:
        # Fallback: split by comma if parsing fails
        return [ing.strip() for ing in ingredients_str.split(',') if ing.strip()]


def parse_recipe_directions(directions_str: str) -> str:
    """Parse directions string from CSV format."""
    try:
        # The directions are stored as string representation of list
        directions_list = ast.literal_eval(directions_str)
        return "\n".join([dir.strip() for dir in directions_list if dir.strip()])
    except:
        # Fallback: return as is if parsing fails
        return directions_str.strip()


def estimate_calories(ingredients: List[str], nutrition_data: Dict[str, pd.DataFrame]) -> Optional[int]:
    """Estimate calories for a recipe based on ingredients."""
    if not nutrition_data or 'food' not in nutrition_data:
        return None
    
    try:
        # Simple calorie estimation based on common ingredients
        calorie_estimates = {
            'chicken': 165,  # per 100g
            'beef': 250,
            'pork': 242,
            'fish': 206,
            'salmon': 208,
            'rice': 130,
            'pasta': 131,
            'bread': 265,
            'cheese': 402,
            'butter': 717,
            'oil': 884,
            'sugar': 387,
            'flour': 364,
            'milk': 42,
            'egg': 155
        }
        
        total_calories = 0
        ingredient_count = 0
        
        for ingredient in ingredients[:10]:  # Limit to first 10 ingredients
            ingredient_lower = ingredient.lower()
            for key, calories in calorie_estimates.items():
                if key in ingredient_lower:
                    total_calories += calories
                    ingredient_count += 1
                    break
        
        if ingredient_count > 0:
            # Rough estimate: average calories per ingredient * serving adjustment
            return int(total_calories * 0.8)  # Adjust for typical serving size
        
    except Exception as e:
        print(f"Error estimating calories: {e}")
    
    return None


def transform_csv_recipe(row: pd.Series, nutrition_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """Transform CSV recipe row to standard format."""
    try:
        ingredients = parse_recipe_ingredients(row['ingredients'])
        directions = parse_recipe_directions(row['directions'])
        calories = estimate_calories(ingredients, nutrition_data)
        
        return {
            "name": row['title'],
            "ingredients": ingredients,
            "instructions": directions,
            "calories": calories,
            "source": row.get('source', 'RecipeNLG')
        }
    except Exception as e:
        print(f"Error transforming recipe: {e}")
        return None


def prepare_training_data(
    recipe_df: pd.DataFrame,
    nutrition_data: Dict[str, pd.DataFrame],
    formatter: RecipeFormatter,
    meal_plan_ratio: float = 0.6
) -> List[Dict[str, Any]]:
    """Prepare training data from recipe DataFrame."""
    training_examples = []
    
    print(f"Processing {len(recipe_df)} recipes...")
    
    for i, (_, row) in enumerate(recipe_df.iterrows()):
        if i % 100 == 0:
            print(f"Processed {i}/{len(recipe_df)} recipes")
        
        try:
            # Transform recipe to standard format
            transformed_recipe = transform_csv_recipe(row, nutrition_data)
            
            if not transformed_recipe:
                continue
                
            # Skip if recipe is missing essential information
            if not transformed_recipe.get("ingredients") or not transformed_recipe.get("instructions"):
                continue
            
            # Decide task type based on ratio
            if (i / len(recipe_df)) < meal_plan_ratio:
                # Meal planning task
                example = formatter.format_meal_plan_query(transformed_recipe)
            else:
                # Recipe generation task
                example = formatter.format_recipe_generation_query(transformed_recipe)
            
            training_examples.append(example)
            
        except Exception as e:
            print(f"Error processing recipe {i}: {e}")
            continue
    
    print(f"Generated {len(training_examples)} training examples")
    return training_examples


def save_dataset(examples: List[Dict[str, Any]], output_path: str):
    """Save prepared dataset to JSON file."""
    print(f"Saving dataset to {output_path}...")
    with open(output_path, 'w') as f:
        json.dump(examples, f, indent=2)
    print(f"Saved {len(examples)} examples to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Prepare recipe dataset from local CSV files")
    parser.add_argument(
        "--recipe_csv",
        type=str,
        default="RecipeNLG_dataset.csv",
        help="Path to RecipeNLG CSV file"
    )
    parser.add_argument(
        "--nutrition_dir",
        type=str,
        default="FoodData_Central_csv_2025-04-24",
        help="Path to FoodData Central directory"
    )
    parser.add_argument(
        "--num_samples",
        type=int,
        default=1000,
        help="Number of recipes to process"
    )
    parser.add_argument(
        "--output_path",
        type=str,
        default="meal_planning_dataset.json",
        help="Output path for prepared dataset"
    )
    parser.add_argument(
        "--meal_plan_ratio",
        type=float,
        default=0.6,
        help="Ratio of meal planning vs recipe generation tasks (0.0-1.0)"
    )
    
    args = parser.parse_args()
    
    # Load recipe CSV
    recipe_df = load_recipe_csv(args.recipe_csv, args.num_samples)
    
    # Load nutrition data
    nutrition_data = load_nutrition_data(args.nutrition_dir)
    
    # Initialize formatter
    formatter = RecipeFormatter()
    
    # Prepare training data
    training_examples = prepare_training_data(
        recipe_df,
        nutrition_data,
        formatter,
        meal_plan_ratio=args.meal_plan_ratio
    )
    
    # Save dataset
    save_dataset(training_examples, args.output_path)
    
    print("Dataset preparation complete!")


if __name__ == "__main__":
    main()