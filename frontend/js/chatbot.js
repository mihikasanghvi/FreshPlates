// Chatbot functionality and message handling

class Chatbot {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.messages = [];
        this.isProcessing = false;
    }

    addMessage(role, content, metadata = {}) {
        const message = {
            role: role,
            content: content,
            timestamp: new Date(),
            metadata: metadata
        };
        this.messages.push(message);
        return message;
    }

    formatMealPlanResponse(data) {
        const { meal_plan, ingredients, shopping_links } = data;
        
        let html = '<div class="recipe-card">';
        
        // Parse meal plan text
        const lines = meal_plan.split('\n');
        let currentSection = '';
        let inIngredients = false;
        let inInstructions = false;
        
        for (let line of lines) {
            line = line.trim();
            if (!line) continue;
            
            // Detect sections
            if (line.toLowerCase().includes('recipe:') || line.toLowerCase().includes('**recipe:')) {
                const recipeName = line.replace(/[*:]/g, '').replace(/recipe/gi, '').trim();
                html += `<div class="recipe-title">🍳 ${recipeName}</div>`;
                continue;
            }
            
            if (line.toLowerCase().includes('ingredient')) {
                inIngredients = true;
                inInstructions = false;
                html += '<div class="recipe-section"><div class="recipe-section-title">📋 Ingredients</div><ul class="ingredients-list">';
                continue;
            }
            
            if (line.toLowerCase().includes('instruction') || line.toLowerCase().includes('step')) {
                inIngredients = false;
                inInstructions = true;
                if (html.includes('<ul class="ingredients-list">')) {
                    html += '</ul></div>';
                }
                html += '<div class="recipe-section"><div class="recipe-section-title">👨‍🍳 Instructions</div><div class="instructions">';
                continue;
            }
            
            if (line.toLowerCase().includes('calorie')) {
                const calories = line.match(/\d+/)?.[0] || '';
                html += `<div style="margin-top: 12px; padding: 8px; background: #e6fffa; border-radius: 8px; color: #234e52; font-weight: 500;">🔥 Calories: ${calories}</div>`;
                continue;
            }
            
            if (line.toLowerCase().includes('constraint')) {
                const constraints = line.match(/\[(.*?)\]/)?.[1] || line;
                const constraintList = constraints.split(',').map(c => c.trim());
                html += '<div style="margin-top: 12px;">';
                constraintList.forEach(c => {
                    html += `<span class="constraints-badge">${c}</span>`;
                });
                html += '</div>';
                continue;
            }
            
            // Format ingredient lines
            if (inIngredients && (line.startsWith('-') || line.match(/^\d+/))) {
                const ingredientText = line.replace(/^[-•]\s*/, '').trim();
                html += `<li>${ingredientText}</li>`;
                continue;
            }
            
            // Format instruction lines
            if (inInstructions) {
                html += line + '<br>';
                continue;
            }
            
            // Regular text
            if (!inIngredients && !inInstructions) {
                html += `<p style="margin: 8px 0;">${line}</p>`;
            }
        }
        
        // Close any open sections
        if (html.includes('<ul class="ingredients-list">')) {
            html += '</ul></div>';
        }
        if (html.includes('<div class="instructions">')) {
            html += '</div></div>';
        }
        
        // Add shopping links
        if (shopping_links && Object.keys(shopping_links).length > 0) {
            html += '<div class="shopping-links">';
            html += '<div class="shopping-links-title">🛒 Shop on Amazon Fresh</div>';
            
            for (const [ingredientName, linkData] of Object.entries(shopping_links)) {
                if (linkData && linkData.url) {
                    html += `
                        <a href="${linkData.url}" target="_blank" rel="noopener noreferrer" class="shopping-link-item">
                            <span class="shopping-link-name">${linkData.ingredient || ingredientName}</span>
                            <span class="shopping-link-icon">🛒</span>
                        </a>
                    `;
                }
            }
            
            html += '</div>';
        }
        
        html += '</div>';
        return html;
    }

    formatRecipeResponse(data) {
        return this.formatMealPlanResponse({
            meal_plan: data.recipe,
            shopping_links: data.shopping_links
        });
    }

    async processUserMessage(userMessage) {
        if (this.isProcessing) {
            return;
        }

        this.isProcessing = true;
        
        // Add user message
        this.addMessage('user', userMessage);
        this.renderMessages();

        try {
            // Determine if it's a recipe request (has ingredients list) or meal plan request
            const isRecipeRequest = userMessage.toLowerCase().includes('recipe') && 
                                   (userMessage.includes(':') || userMessage.includes('using'));
            
            let response;
            
            if (isRecipeRequest) {
                // Extract ingredients from message
                const ingredientsMatch = userMessage.match(/using:\s*(.+?)(?:\.|Constraints|$)/i) ||
                                        userMessage.match(/with:\s*(.+?)(?:\.|Constraints|$)/i) ||
                                        userMessage.match(/ingredients?:\s*(.+?)(?:\.|Constraints|$)/i);
                
                if (ingredientsMatch) {
                    const ingredientsText = ingredientsMatch[1].trim();
                    const ingredients = ingredientsText.split(',').map(i => i.trim());
                    
                    // Extract constraints
                    const constraintsMatch = userMessage.match(/constraints?:\s*(.+)/i);
                    const constraints = constraintsMatch ? 
                        constraintsMatch[1].split(',').map(c => c.trim()) : [];
                    
                    response = await this.apiClient.generateRecipe(ingredients, constraints, true);
                    const formattedResponse = this.formatRecipeResponse(response);
                    this.addMessage('assistant', formattedResponse, { type: 'recipe', data: response });
                } else {
                    // Fallback to meal plan
                    response = await this.apiClient.generateMealPlan(userMessage, [], true);
                    const formattedResponse = this.formatMealPlanResponse(response);
                    this.addMessage('assistant', formattedResponse, { type: 'meal_plan', data: response });
                }
            } else {
                // Extract constraints from message
                const constraints = [];
                const constraintPatterns = [
                    /(?:no|without)\s+(\w+)/gi,
                    /(?:under|below|less than)\s+(\d+)\s+calories?/gi,
                    /(?:vegetarian|vegan|keto|paleo|gluten-free)/gi
                ];
                
                constraintPatterns.forEach(pattern => {
                    const matches = userMessage.matchAll(pattern);
                    for (const match of matches) {
                        if (match[0]) constraints.push(match[0].toLowerCase());
                    }
                });
                
                response = await this.apiClient.generateMealPlan(userMessage, constraints, true);
                const formattedResponse = this.formatMealPlanResponse(response);
                this.addMessage('assistant', formattedResponse, { type: 'meal_plan', data: response });
            }
            
            this.renderMessages();
        } catch (error) {
            console.error('Error processing message:', error);
            const errorMessage = `Sorry, I encountered an error: ${error.message}. Please try again or check if the API is running.`;
            this.addMessage('assistant', `<div class="error-message">${errorMessage}</div>`, { type: 'error' });
            this.renderMessages();
        } finally {
            this.isProcessing = false;
        }
    }

    renderMessages() {
        const messagesContainer = document.getElementById('messages');
        const welcomeMessage = document.getElementById('welcomeMessage');
        
        if (this.messages.length > 0) {
            welcomeMessage.style.display = 'none';
        } else {
            welcomeMessage.style.display = 'block';
        }
        
        messagesContainer.innerHTML = '';
        
        this.messages.forEach(message => {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${message.role}`;
            
            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            avatar.textContent = message.role === 'user' ? '👤' : '🤖';
            
            const content = document.createElement('div');
            content.className = 'message-content';
            
            if (typeof message.content === 'string' && message.content.includes('<')) {
                content.innerHTML = message.content;
            } else {
                content.textContent = message.content;
            }
            
            const time = document.createElement('div');
            time.className = 'message-time';
            time.textContent = message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            
            content.appendChild(time);
            messageDiv.appendChild(avatar);
            messageDiv.appendChild(content);
            messagesContainer.appendChild(messageDiv);
        });
        
        // Scroll to bottom
        const chatContainer = document.getElementById('chatContainer');
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    clearChat() {
        this.messages = [];
        this.renderMessages();
    }
}

