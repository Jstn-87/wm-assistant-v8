// Enhanced WM Assistant with modern AI chat features
class WMAssistant {
    constructor() {
        this.messagesContainer = document.getElementById('messages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.charCount = document.getElementById('charCount');
        this.suggestionsContainer = document.getElementById('suggestions');
        this.reloadSessionBtn = document.getElementById('reloadSession');
        this.seedDataBtn = document.getElementById('seedData');
        this.addressIndicator = document.getElementById('addressIndicator');
        this.addressText = document.getElementById('addressText');
        this.changeAddressBtn = document.getElementById('changeAddressBtn');
        this.errorToast = document.getElementById('errorToast');
        this.addressModal = document.getElementById('addressModal');
        this.addressInput = document.getElementById('addressInput');
        this.closeAddressModal = document.getElementById('closeAddressModal');
        this.cancelAddress = document.getElementById('cancelAddress');
        this.saveAddress = document.getElementById('saveAddress');
        
        // Backend API base URL - use your backend URL
        // Use relative URL for production, localhost for development
        this.API_BASE_URL = window.location.hostname === 'localhost' ? 'http://localhost:8001' : '';
        
        this.sessionManager = new SessionManager();
        this.messageQueue = [];
        this.isProcessing = false;
        this.retryCount = 0;
        this.maxRetries = 3;
        
        this.init();
    }
    
    init() {
        // Event listeners
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Character count with debouncing
        this.messageInput.addEventListener('input', debounce(() => {
            this.updateCharCount();
            this.updateSuggestions();
        }, 300));
        
        // Suggestion chips
        document.querySelectorAll('.suggestion-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const message = chip.getAttribute('data-message');
                this.messageInput.value = message;
                this.updateCharCount();
                this.sendMessage();
            });
        });
        
        // Action buttons
        this.reloadSessionBtn.addEventListener('click', () => this.reloadSession());
        this.seedDataBtn.addEventListener('click', () => this.seedData());
        
        // Address management
        this.changeAddressBtn.addEventListener('click', () => this.showAddressModal());
        this.closeAddressModal.addEventListener('click', () => this.hideAddressModal());
        this.cancelAddress.addEventListener('click', () => this.hideAddressModal());
        this.saveAddress.addEventListener('click', () => this.saveAddressFromModal());
        
        // Error toast
        this.errorToast.querySelector('.toast-close').addEventListener('click', () => {
            this.hideErrorToast();
        });
        
        // Modal overlay click to close
        this.addressModal.addEventListener('click', (e) => {
            if (e.target === this.addressModal) {
                this.hideAddressModal();
            }
        });
        
        // Focus input on load
        this.messageInput.focus();
        this.updateCharCount();
        
        // Set random subheader
        this.setRandomSubheader();
        
        // Load session state
        this.sessionManager.loadSessionState().then(() => {
            this.updateAddressIndicator();
            this.updateSuggestions();
        });
    }
    
    setRandomSubheader() {
        const subheaders = [
            "A smarter WM experience",
            "The next generation of support",
            "A new way to connect with WM",
            "Say hello to the future of WM support",
            "A more intelligent way to connect with WM",
            "Your new intelligent connection to WM",
            "A connected, intelligent experience built around you",
            "Welcome to the intelligent WM experience",
            "Everything you need, powered by intelligence",
            "Intelligent help for everything WM",
            "Your WM. Smarter."
        ];
        
        const randomIndex = Math.floor(Math.random() * subheaders.length);
        const dynamicSubtitle = document.getElementById('dynamicSubtitle');
        if (dynamicSubtitle) {
            dynamicSubtitle.textContent = subheaders[randomIndex];
        }
    }
    
    updateCharCount() {
        const count = this.messageInput.value.length;
        this.charCount.textContent = `${count}/500`;
        this.sendButton.disabled = count === 0 || this.isProcessing;
        
        // Hide suggestions after user starts typing
        if (count > 0) {
            this.suggestionsContainer.style.display = 'none';
        } else {
            this.suggestionsContainer.style.display = 'block';
        }
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        
        if (!message || this.isProcessing) {
            return;
        }
        
        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Clear input and disable send button
        this.messageInput.value = '';
        this.updateCharCount();
        this.setLoading(true);
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            await this.attemptSendMessage(message);
            this.retryCount = 0; // Reset retry count on success
        } catch (error) {
            console.error('Error sending message:', error);
            this.handleSendError(error, message);
        } finally {
            this.setLoading(false);
            this.hideTypingIndicator();
        }
    }
    
    async attemptSendMessage(message) {
        console.log('Attempting to send message:', message);
        console.log('Using session ID:', this.sessionManager.sessionId);
        
        const response = await fetch(`${this.API_BASE_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                session_id: this.sessionManager.sessionId,
                message: message,
                context: this.getConversationContext()
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Add assistant response to chat
        this.addMessage(data.content, 'assistant', data);
        
        // Update session state
        await this.sessionManager.updateSessionState(data);
        this.updateAddressIndicator();
        this.updateSuggestions();
    }
    
    getConversationContext() {
        // Get recent conversation context from chat messages
        const messages = this.messagesContainer.querySelectorAll('.message');
        const context = [];
        
        // Get last 5 messages for context
        const recentMessages = Array.from(messages).slice(-5);
        
        recentMessages.forEach(msg => {
            const role = msg.classList.contains('user') ? 'user' : 'assistant';
            const messageTextElement = msg.querySelector('.message-text');
            if (messageTextElement) {
                const content = messageTextElement.textContent;
                context.push({ role, content });
            }
        });
        
        return JSON.stringify(context);
    }
    
    handleSendError(error, message) {
        this.retryCount++;
        
        if (this.retryCount < this.maxRetries) {
            this.showRetryOption(message);
        } else {
            this.addMessage('Sorry, I encountered an error. Please try again.', 'assistant', {
                type: 'error',
                error: error.message
            });
            this.showErrorToast('Connection failed. Please check your internet connection and try again.');
        }
    }
    
    showRetryOption(message) {
        const retryDiv = document.createElement('div');
        retryDiv.className = 'message assistant error-message';
        retryDiv.innerHTML = `
            <div class="message-avatar">
                <img class="avatar-logo" src="https://www.wm.com/content/dam/wm/icons/branding/wm-logo-web-header-footer.svg" alt="WM" />
            </div>
            <div class="message-content">
                <div class="error-content">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Connection issue. Retrying... (${this.retryCount}/${this.maxRetries})</p>
                    <button class="retry-btn" onclick="window.wmAssistant.retryMessage('${message}')">Retry Now</button>
                </div>
            </div>
        `;
        this.messagesContainer.appendChild(retryDiv);
        this.scrollToBottom();
        
        // Auto-retry after delay
        setTimeout(() => {
            if (this.retryCount < this.maxRetries) {
                this.retryMessage(message);
            }
        }, 1000 * this.retryCount);
    }
    
    async retryMessage(message) {
        this.hideTypingIndicator();
        this.setLoading(true);
        
        try {
            await this.attemptSendMessage(message);
            this.retryCount = 0;
        } catch (error) {
            this.handleSendError(error, message);
        } finally {
            this.setLoading(false);
        }
    }
    
    showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant typing-indicator';
        typingDiv.id = 'typingIndicator';
        typingDiv.innerHTML = `
            <div class="message-avatar">
                <img class="avatar-logo" src="https://www.wm.com/content/dam/wm/icons/branding/wm-logo-web-header-footer.svg" alt="WM" />
            </div>
            <div class="message-content">
                <div class="typing-dots">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        this.messagesContainer.appendChild(typingDiv);
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    addMessage(content, sender, options = {}) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender} ${options.type || 'text'}`;
        
        // Create avatar
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        if (sender === 'user') {
            avatarDiv.innerHTML = '<i class="fas fa-user"></i>';
        } else {
            avatarDiv.innerHTML = `
                <img
                    class="avatar-logo"
                    src="https://www.wm.com/content/dam/wm/icons/branding/wm-logo-web-header-footer.svg"
                    alt="WM"
                    aria-hidden="true"
                />
            `;
        }
        
        // Create message content
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Handle different message types
        switch (options.type) {
            case 'order_confirmation':
                this.addOrderConfirmationMessage(contentDiv, content, options);
                break;
            case 'service_status':
                this.addServiceStatusMessage(contentDiv, content, options);
                break;
            case 'pricing_info':
                this.addPricingMessage(contentDiv, content, options);
                break;
            case 'error':
                this.addErrorMessage(contentDiv, content, options);
                break;
            default:
                this.addTextMessage(contentDiv, content, options);
        }
        
        // Add timestamp
        const timestampDiv = document.createElement('div');
        timestampDiv.className = 'message-timestamp';
        timestampDiv.innerHTML = `<span class="timestamp">${this.getCurrentTime()}</span>`;
        contentDiv.appendChild(timestampDiv);
        
        // Add message status for user messages
        if (sender === 'user') {
            const statusDiv = document.createElement('div');
            statusDiv.className = 'message-status sent';
            contentDiv.appendChild(statusDiv);
        }
        
        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);
        this.messagesContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        this.scrollToBottom();
    }
    
    addTextMessage(container, content, options = {}) {
        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        
        // Handle URLs from the backend response
        let formattedContent = content;
        if (options.urls && options.urls.length > 0) {
            options.urls.forEach(url => {
                const linkText = this.extractDomain(url);
                const link = `<a href="${url}" target="_blank" rel="noopener noreferrer">${linkText}</a>`;
                formattedContent = formattedContent.replace(url, link);
            });
        }
        
        // Also handle any markdown-style links in the content
        formattedContent = formattedContent.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
        
        // Convert line breaks to HTML
        formattedContent = formattedContent.replace(/\n/g, '<br>');
        
        textDiv.innerHTML = formattedContent;
        container.appendChild(textDiv);
    }
    
    extractDomain(url) {
        try {
            const domain = new URL(url).hostname;
            return domain.replace('www.', '');
        } catch {
            return url;
        }
    }
    
    addOrderConfirmationMessage(container, content, options) {
        container.innerHTML = `
            <div class="message-text">${content}</div>
            <div class="order-confirmation">
                <div class="confirmation-header">
                    <i class="fas fa-check-circle"></i>
                    <h3>Order Confirmed</h3>
                </div>
                <div class="order-details">
                    <p><strong>Order #:</strong> ${options.orderNumber || 'WM-' + Date.now()}</p>
                    <p><strong>Service:</strong> ${options.serviceType || 'Service Request'}</p>
                    <p><strong>Estimated Date:</strong> ${options.estimatedDate || 'Within 2 business days'}</p>
                    <p><strong>Total Cost:</strong> $${options.cost || '0.00'}</p>
                </div>
                <div class="confirmation-actions">
                    <button class="btn-secondary">View Details</button>
                    <button class="btn-primary">Track Order</button>
                </div>
            </div>
        `;
    }
    
    addServiceStatusMessage(container, content, options) {
        const statusClass = options.status === 'delayed' ? 'delayed' : 'on-time';
        container.innerHTML = `
            <div class="message-text">${content}</div>
            <div class="service-status-message ${statusClass}">
                <div class="status-header">
                    <i class="fas fa-${options.status === 'delayed' ? 'clock' : 'check-circle'}"></i>
                    <h4>Service Status: ${options.status === 'delayed' ? 'Delayed' : 'On Time'}</h4>
                </div>
                <p>${options.details || 'Your service is running normally.'}</p>
            </div>
        `;
    }
    
    addPricingMessage(container, content, options) {
        container.innerHTML = `
            <div class="message-text">${content}</div>
            <div class="pricing-info">
                <h4>Pricing Information</h4>
                <div class="pricing-details">
                    ${options.pricing ? Object.entries(options.pricing).map(([key, value]) => 
                        `<span>${key}:</span><span>$${value}</span>`
                    ).join('') : '<p>No pricing information available.</p>'}
                </div>
            </div>
        `;
    }
    
    addErrorMessage(container, content, options) {
        container.innerHTML = `
            <div class="message-text">${content}</div>
            <div class="error-message">
                <div class="error-content">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>Error: ${options.error || 'Unknown error occurred'}</span>
                </div>
            </div>
        `;
    }
    
    getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    setLoading(loading) {
        this.isProcessing = loading;
        this.sendButton.disabled = loading || this.messageInput.value.length === 0;
        
        if (loading) {
            this.sendButton.innerHTML = '<div class="loading"></div>';
        } else {
            this.sendButton.innerHTML = '<i class="fas fa-paper-plane"></i>';
            this.messageInput.focus();
        }
    }
    
    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
    
    updateSuggestions() {
        const context = this.getContextualSuggestions();
        this.suggestionsContainer.innerHTML = `
            <div class="suggestion-chips">
                ${context.map(suggestion => `
                    <button class="suggestion-chip" data-message="${suggestion.message}">
                        <i class="${suggestion.icon}"></i>
                        ${suggestion.label}
                    </button>
                `).join('')}
            </div>
        `;
        
        // Re-attach event listeners
        document.querySelectorAll('.suggestion-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const message = chip.getAttribute('data-message');
                this.messageInput.value = message;
                this.updateCharCount();
                this.sendMessage();
            });
        });
    }
    
    getContextualSuggestions() {
        const session = this.sessionManager.getSession();
        
        if (!session.address) {
            return [
                { label: "Set My Address", message: "My address is 123 Main St", icon: "fas fa-map-marker-alt" },
                { label: "Service Status", message: "What is my service status?", icon: "fas fa-info-circle" },
                { label: "Find My Zone", message: "What zone am I in?", icon: "fas fa-search" }
            ];
        }
        
        if (session.lastIntent === 'service_status') {
            return [
                { label: "Change Container", message: "Can I change my container size?", icon: "fas fa-exchange-alt" },
                { label: "Bulk Pickup", message: "Schedule bulk pickup", icon: "fas fa-truck" },
                { label: "Yard Waste", message: "Do you collect yard waste?", icon: "fas fa-leaf" }
            ];
        }
        
        return [
            { label: "Service Status", message: "What is my service status?", icon: "fas fa-info-circle" },
            { label: "Change Container", message: "Can I change my container size?", icon: "fas fa-exchange-alt" },
            { label: "Bulk Pickup", message: "Schedule bulk pickup", icon: "fas fa-truck" },
            { label: "Yard Waste", message: "Do you collect yard waste?", icon: "fas fa-leaf" }
        ];
    }
    
    updateAddressIndicator() {
        const session = this.sessionManager.getSession();
        if (session.address) {
            this.addressText.textContent = session.address;
            this.addressIndicator.style.display = 'flex';
        } else {
            this.addressIndicator.style.display = 'none';
        }
    }
    
    showAddressModal() {
        this.addressModal.style.display = 'flex';
        this.addressInput.focus();
    }
    
    hideAddressModal() {
        this.addressModal.style.display = 'none';
        this.addressInput.value = '';
    }
    
    async saveAddressFromModal() {
        const address = this.addressInput.value.trim();
        if (!address) return;
        
        try {
            await this.sessionManager.setAddress(address);
            this.updateAddressIndicator();
            this.updateSuggestions();
            this.hideAddressModal();
            this.addMessage(`Address set to: ${address}`, 'assistant');
        } catch (error) {
            this.showErrorToast('Failed to set address. Please try again.');
        }
    }
    
    showErrorToast(message) {
        this.errorToast.querySelector('.toast-message').textContent = message;
        this.errorToast.classList.add('show');
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            this.hideErrorToast();
        }, 5000);
    }
    
    hideErrorToast() {
        this.errorToast.classList.remove('show');
    }
    
    async reloadSession() {
        await this.sessionManager.reloadSession();
        this.messagesContainer.innerHTML = `
            <div class="message assistant">
                <div class="message-avatar">
                    <img
                        class="avatar-logo"
                        src="https://www.wm.com/content/dam/wm/icons/branding/wm-logo-web-header-footer.svg"
                        alt="WM"
                        aria-hidden="true"
                    />
                </div>
                <div class="message-content">
                    <div class="message-text">
                        Session reloaded! Hello! I'm your WM Assistant. How can I help you today?
                    </div>
                    <div class="message-timestamp">
                        <span class="timestamp">${this.getCurrentTime()}</span>
                    </div>
                </div>
            </div>
        `;
        this.suggestionsContainer.style.display = 'block';
        this.updateAddressIndicator();
        this.updateSuggestions();
    }
    
    async seedData() {
        try {
            // For now, just show a message since we don't have a seed endpoint
            this.addMessage('Demo data reloaded successfully! All previous session data has been cleared.', 'assistant');
            this.updateAddressIndicator();
            this.updateSuggestions();
        } catch (error) {
            console.error('Error reloading demo data:', error);
            this.addMessage('Failed to reload demo data.', 'assistant');
        }
    }
}

// Session Manager for handling session persistence
class SessionManager {
    constructor() {
        // Use relative URL for production, localhost for development
        this.API_BASE_URL = window.location.hostname === 'localhost' ? 'http://localhost:8001' : '';
        console.log('SessionManager constructor - API_BASE_URL set to:', this.API_BASE_URL);
        this.sessionId = this.getOrCreateSession();
        this.sessionData = null;
    }
    
    getOrCreateSession() {
        let sessionId = localStorage.getItem('wm_session_id');
        if (!sessionId) {
            sessionId = this.generateSessionId();
            localStorage.setItem('wm_session_id', sessionId);
        }
        console.log('SessionManager - Using session ID:', sessionId);
        return sessionId;
    }
    
    generateSessionId() {
        // Generate a UUID-like session ID to match backend expectations
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
    
    async loadSessionState() {
        try {
            console.log('Loading session state with API_BASE_URL:', this.API_BASE_URL);
            console.log('Session ID:', this.sessionId);
            // Initialize with empty session data since we don't have session endpoints
            this.sessionData = {
                sessionId: this.sessionId,
                address: localStorage.getItem('wm_address') || null,
                lastIntent: null
            };
            console.log('Session initialized:', this.sessionData);
        } catch (error) {
            console.error('Failed to load session:', error);
            this.sessionData = {
                sessionId: this.sessionId,
                address: localStorage.getItem('wm_address') || null,
                lastIntent: null
            };
        }
    }

    async updateSessionState(data) {
        if (data) {
            this.sessionData = {
                ...this.sessionData,
                lastIntent: data.intent || null,
                address: data.address || this.sessionData?.address
            };
        }
    }
    
    async setAddress(address) {
        // For now, just store locally
        this.sessionData = {
            ...this.sessionData,
            address: address
        };
        localStorage.setItem('wm_address', address);
    }
    
    async reloadSession() {
        this.sessionData = null;
        this.sessionId = this.generateSessionId();
        localStorage.setItem('wm_session_id', this.sessionId);
        localStorage.removeItem('wm_address');
        
        this.sessionData = {
            sessionId: this.sessionId,
            address: null,
            lastIntent: null
        };
    }
    
    getSession() {
        return this.sessionData || {
            sessionId: this.sessionId,
            address: localStorage.getItem('wm_address'),
            lastIntent: null
        };
    }
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.wmAssistant = new WMAssistant();
});