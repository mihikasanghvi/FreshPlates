// // API Configuration
// const CONFIG = {
//     // API base URL - defaults to localhost, can be overridden
//     API_BASE_URL: window.API_BASE_URL || 'http://localhost:8000',
    
//     // API endpoints
//     ENDPOINTS: {
//         PLAN: '/plan',
//         RECIPE: '/recipe',
//         SHOP: '/ingredients/shop',
//         HEALTH: '/health'
//     },
    
//     // Timeout for API requests (milliseconds)
//     REQUEST_TIMEOUT: 30000,
    
//     // Maximum number of messages to keep in history
//     MAX_MESSAGES: 100
// };

// // Helper function to get full API URL
// function getApiUrl(endpoint) {
//     return `${CONFIG.API_BASE_URL}${endpoint}`;
// }

// API Configuration
const CONFIG = {
    // Detect if we're behind a proxy and construct the correct API URL
    API_BASE_URL: (() => {
        const origin = window.location.origin;
        const pathname = window.location.pathname;
        
        // If accessing through CloudFront proxy
        if (pathname.includes('/proxy/')) {
            return origin + '/proxy/8000';
        }
        
        // Default to localhost
        return 'http://localhost:8000';
    })(),
    
    // API endpoints
    ENDPOINTS: {
        PLAN: '/plan',
        RECIPE: '/recipe',
        SHOP: '/ingredients/shop',
        HEALTH: '/health'
    },
    
    // Timeout for API requests (milliseconds)
    REQUEST_TIMEOUT: 30000,
    
    // Maximum number of messages to keep in history
    MAX_MESSAGES: 100
};

// Helper function to get full API URL
function getApiUrl(endpoint) {
    return `${CONFIG.API_BASE_URL}${endpoint}`;
}
