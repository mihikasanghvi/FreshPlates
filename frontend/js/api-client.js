// API Client for Meal Planner API

class MealPlannerAPI {
    constructor(baseUrl) {
        this.baseUrl = baseUrl || CONFIG.API_BASE_URL;
    }

    async checkHealth() {
        try {
            const response = await fetch(`${this.baseUrl}${CONFIG.ENDPOINTS.HEALTH}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            return await response.json();
        } catch (error) {
            console.error('Health check failed:', error);
            return { status: 'error', error: error.message };
        }
    }

    async generateMealPlan(query, constraints = [], includeShoppingLinks = true) {
        try {
            const response = await fetch(`${this.baseUrl}${CONFIG.ENDPOINTS.PLAN}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    constraints: constraints,
                    include_shopping_links: includeShoppingLinks
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Meal plan generation failed:', error);
            throw error;
        }
    }

    async generateRecipe(ingredients, constraints = [], includeShoppingLinks = true) {
        try {
            const response = await fetch(`${this.baseUrl}${CONFIG.ENDPOINTS.RECIPE}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ingredients: ingredients,
                    constraints: constraints,
                    include_shopping_links: includeShoppingLinks
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Recipe generation failed:', error);
            throw error;
        }
    }

    async getShoppingLinks(ingredients) {
        try {
            const response = await fetch(`${this.baseUrl}${CONFIG.ENDPOINTS.SHOP}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ingredients: ingredients
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Shopping links failed:', error);
            throw error;
        }
    }
}

// Create global API instance
const apiClient = new MealPlannerAPI();

