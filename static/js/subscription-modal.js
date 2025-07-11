// Subscription Modal JavaScript
class SubscriptionModal {
    constructor() {
        this.modal = null;
        this.isOpen = false;
        this.currentUser = null;
        this.init();
    }

    init() {
        // Check if modal already exists
        if (document.getElementById('subscription-modal')) {
            return;
        }

        // Create modal HTML
        this.createModal();
        this.bindEvents();
    }

    createModal() {
        const modalHTML = `
            <div id="subscription-modal" class="subscription-modal" style="display: none;">
                <div class="subscription-modal-content">
                    <button class="subscription-modal-close" onclick="subscriptionModal.close()">×</button>
                    
                    <div class="subscription-modal-header">
                        <h2 class="subscription-modal-title">Unlock Premium Features</h2>
                        <p class="subscription-modal-subtitle">Subscribe to access advanced AI tools and unlimited usage</p>
                    </div>

                    <div class="subscription-modal-body">
                        <div class="subscription-pricing">
                            <div class="subscription-price">$6.99</div>
                            <div class="subscription-period">per month</div>
                        </div>

                        <ul class="subscription-features">
                            <li class="subscription-feature">
                                <svg class="subscription-feature-icon" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                                </svg>
                                Unlimited AI text generation
                            </li>
                            <li class="subscription-feature">
                                <svg class="subscription-feature-icon" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                                </svg>
                                Access to all AI tools
                            </li>
                            <li class="subscription-feature">
                                <svg class="subscription-feature-icon" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                                </svg>
                                Priority processing
                            </li>
                            <li class="subscription-feature">
                                <svg class="subscription-feature-icon" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                                </svg>
                                Advanced customization options
                            </li>
                        </ul>

                        <div class="subscription-modal-actions">
                            <a href="/subscribe" class="subscription-btn subscription-btn-primary">Subscribe Now</a>
                            <button class="subscription-btn subscription-btn-secondary" onclick="subscriptionModal.close()">Maybe Later</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modal = document.getElementById('subscription-modal');
    }

    bindEvents() {
        // Close modal when clicking outside
        document.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        });

        // Close modal on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });
    }

    async checkSubscription() {
        try {
            const response = await fetch('/api/current-user');
            if (response.ok) {
                const user = await response.json();
                this.currentUser = user;
                return user.is_subscribed === true;
            }
            return false;
        } catch (error) {
            console.error('Error checking subscription:', error);
            return false;
        }
    }

    async requireSubscription(action = 'access this feature') {
        const isSubscribed = await this.checkSubscription();
        
        if (!isSubscribed) {
            // Update modal title based on action
            const titleElement = this.modal.querySelector('.subscription-modal-title');
            if (titleElement) {
                titleElement.textContent = `Subscription Required`;
            }
            
            const subtitleElement = this.modal.querySelector('.subscription-modal-subtitle');
            if (subtitleElement) {
                subtitleElement.textContent = `You need an active subscription to ${action}`;
            }
            
            this.show();
            return false;
        }
        
        return true;
    }

    show() {
        if (this.modal) {
            this.modal.style.display = 'flex';
            this.modal.classList.add('show');
            this.isOpen = true;
            document.body.style.overflow = 'hidden';
        }
    }

    close() {
        if (this.modal) {
            this.modal.style.display = 'none';
            this.modal.classList.remove('show');
            this.isOpen = false;
            document.body.style.overflow = '';
        }
    }
}

// Create global instance
const subscriptionModal = new SubscriptionModal();

// Helper function for easy access
async function requireSubscription(action = 'access this feature') {
    return await subscriptionModal.requireSubscription(action);
}

// Helper function to check if user is subscribed
async function isUserSubscribed() {
    return await subscriptionModal.checkSubscription();
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SubscriptionModal, subscriptionModal, requireSubscription, isUserSubscribed };
}
