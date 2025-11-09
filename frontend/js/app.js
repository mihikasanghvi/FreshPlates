// Main application logic

let chatbot;
let loadingOverlay;

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    chatbot = new Chatbot(apiClient);
    loadingOverlay = document.getElementById('loadingOverlay');
    
    initializeEventListeners();
    checkApiHealth();
});

function initializeEventListeners() {
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const clearBtn = document.getElementById('clearChatBtn');
    
    // Send message on button click
    sendBtn.addEventListener('click', handleSendMessage);
    
    // Send message on Enter key
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });
    
    // Clear chat
    clearBtn.addEventListener('click', () => {
        if (confirm('Are you sure you want to clear the chat?')) {
            chatbot.clearChat();
        }
    });
    
    // Example query buttons
    document.querySelectorAll('.example-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const query = btn.getAttribute('data-query');
            userInput.value = query;
            handleSendMessage();
        });
    });
}

async function handleSendMessage() {
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const message = userInput.value.trim();
    
    if (!message || chatbot.isProcessing) {
        return;
    }
    
    // Disable input
    userInput.disabled = true;
    sendBtn.disabled = true;
    showLoading();
    
    // Clear input
    userInput.value = '';
    
    try {
        await chatbot.processUserMessage(message);
    } catch (error) {
        console.error('Error handling message:', error);
    } finally {
        hideLoading();
        userInput.disabled = false;
        sendBtn.disabled = false;
        userInput.focus();
    }
}

function showLoading() {
    if (loadingOverlay) {
        loadingOverlay.classList.add('active');
    }
}

function hideLoading() {
    if (loadingOverlay) {
        loadingOverlay.classList.remove('active');
    }
}

async function checkApiHealth() {
    try {
        const health = await apiClient.checkHealth();
        if (health.status === 'healthy') {
            console.log('API is healthy:', health);
        } else {
            console.warn('API health check returned:', health);
            showApiWarning();
        }
    } catch (error) {
        console.error('API health check failed:', error);
        showApiWarning();
    }
}

function showApiWarning() {
    const warning = document.createElement('div');
    warning.className = 'error-message';
    warning.style.margin = '12px 24px';
    warning.innerHTML = '⚠️ <strong>Warning:</strong> Unable to connect to API. Make sure the API server is running at ' + CONFIG.API_BASE_URL;
    
    const chatContainer = document.getElementById('chatContainer');
    chatContainer.insertBefore(warning, chatContainer.firstChild);
    
    // Remove warning after 10 seconds
    setTimeout(() => {
        if (warning.parentNode) {
            warning.remove();
        }
    }, 10000);
}

