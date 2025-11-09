"""
Map recipe ingredients to Amazon Fresh search URLs.
Generates direct links to Amazon Fresh product searches.
"""
from typing import List, Dict, Optional, Any
import re
from urllib.parse import quote_plus


class IngredientMapper:
    """Maps recipe ingredients to Amazon Fresh search URLs."""
    
    def __init__(self):
        """Initialize ingredient mapper."""
        # Common ingredient to search term mappings for better results
        self.ingredient_mappings = {
            "chicken breast": "organic chicken breast",
            "ground beef": "grass fed ground beef",
            "salmon": "wild caught salmon",
            "tofu": "organic tofu",
            "olive oil": "extra virgin olive oil",
            "butter": "organic butter",
            "milk": "organic whole milk",
            "eggs": "free range eggs",
        }
    
    def parse_ingredient(self, ingredient: str) -> Dict[str, Any]:
        """
        Parse ingredient string into structured format.
        
        Args:
            ingredient: Ingredient string (e.g., "2 cups flour" or "chicken breast")
        
        Returns:
            Dictionary with amount, unit, name
        """
        # Pattern to match amount, unit, and ingredient name
        pattern = r'^(\d+(?:\.\d+)?)\s*(\w+)?\s*(.+)$'
        match = re.match(pattern, ingredient.strip())
        
        if match:
            amount = match.group(1)
            unit = match.group(2) or ""
            name = match.group(3).strip()
        else:
            # No amount/unit, just ingredient name
            amount = None
            unit = None
            name = ingredient.strip()
        
        return {
            "amount": amount,
            "unit": unit,
            "name": name.lower()
        }
    
    def generate_amazon_fresh_url(self, ingredient_name: str) -> str:
        """
        Generate Amazon Fresh search URL for an ingredient.
        
        Args:
            ingredient_name: Name of the ingredient
        
        Returns:
            Amazon Fresh search URL
        """
        # Use mapping if available, otherwise use ingredient name as-is
        search_term = self.ingredient_mappings.get(ingredient_name, ingredient_name)
        
        # URL encode the search term
        encoded_term = quote_plus(search_term)
        
        # Generate Amazon Fresh search URL
        url = f"https://www.amazon.com/s?k={encoded_term}+site:amazonfresh.com"
        
        return url
    
    def map_ingredient_to_url(self, ingredient: str) -> Dict[str, Any]:
        """
        Map an ingredient to an Amazon Fresh search URL.
        
        Args:
            ingredient: Ingredient name or full ingredient string
        
        Returns:
            Dictionary with ingredient info and search URL
        """
        # Parse ingredient
        parsed = self.parse_ingredient(ingredient)
        ingredient_name = parsed["name"]
        
        # Generate URL
        url = self.generate_amazon_fresh_url(ingredient_name)
        
        return {
            "ingredient": ingredient,
            "ingredient_name": ingredient_name,
            "amount": parsed["amount"],
            "unit": parsed["unit"],
            "amazon_fresh_url": url
        }
    
    def map_ingredients_to_urls(
        self,
        ingredients: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Map multiple ingredients to Amazon Fresh search URLs.
        
        Args:
            ingredients: List of ingredient strings
        
        Returns:
            Dictionary mapping ingredient names to URL info
        """
        ingredient_urls = {}
        
        for ingredient in ingredients:
            parsed = self.parse_ingredient(ingredient)
            ingredient_name = parsed["name"]
            
            url_info = self.map_ingredient_to_url(ingredient)
            ingredient_urls[ingredient_name] = url_info
        
        return ingredient_urls
    
    def generate_shopping_list(
        self,
        ingredients: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Generate a shopping list with Amazon Fresh search URLs.
        
        Args:
            ingredients: List of ingredient strings
        
        Returns:
            List of shopping items with Amazon Fresh URLs
        """
        shopping_list = []
        
        for ingredient in ingredients:
            item = self.map_ingredient_to_url(ingredient)
            shopping_list.append(item)
        
        return shopping_list
