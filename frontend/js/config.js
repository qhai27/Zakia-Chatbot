/**
 * Configuration for ZAKIA Chatbot
 */
const CONFIG = {
    API_BASE_URL: "http://127.0.0.1:5000",
    ENDPOINTS: {
        CHAT: "/chat",
        FAQS: "/faqs",
        HEALTH: "/health"
    },
    UI: {
        TYPING_DELAY: 1000,
        QUICK_REPLY_SELECTION_DURATION: 2000,
        MAX_QUICK_REPLIES: 4
    },
    MESSAGES: {
        SERVER_ERROR: "Maaf, ralat pelayan. Cuba lagi. 🙏",
        CONNECTION_ERROR: "Maaf, tidak dapat capai pelayan sekarang. Sila cuba lagi.",
        SESSION_ENDED: "Sesi ditamatkan. Anda boleh mula semula bila-bila masa."
    }
};

// Make config available globally
window.CONFIG = CONFIG;
