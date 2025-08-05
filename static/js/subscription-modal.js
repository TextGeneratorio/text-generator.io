// Subscription Modal JavaScript
if (typeof window.SubscriptionModal === 'undefined') {
window.SubscriptionModal = class SubscriptionModal {
    constructor() {
        this.modal = null;
        this.isOpen = false;
        this.currentUser = null;
        this.init();
    }

    init() {
        // Check if modal already exists
        if (document.getElementById('subscription-modal')) {
            this.modal = document.getElementById('subscription-modal');
            return;
        }

        // Create modal HTML
        this.createModal();
        this.bindEvents();
    }

    createModal() {
        // Wait for DOM to be ready
        if (!document.body) {
            console.warn('Document body not ready, deferring modal creation');
            setTimeout(() => this.createModal(), 100);
            return;
        }

        const modalHTML = `
            <div id="subscription-modal" class="subscription-modal" style="display: none;">
                <div class="subscription-modal-content">
                    <button class="subscription-modal-close" onclick="if(window.subscriptionModal) subscriptionModal.close()">×</button>
                    
                    <div class="subscription-modal-header">
                        <h2 class="subscription-modal-title">Subscription Required</h2>
                        <p class="subscription-modal-subtitle">You need an active subscription to use advanced AI features</p>
                    </div>

                    <div class="subscription-modal-body">
                        <div class="subscription-pricing">
                            <div class="subscription-price">$19.00</div>
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
                                AI Text Editor with advanced editing tools
                            </li>
                            <li class="subscription-feature">
                                <svg class="subscription-feature-icon" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                                </svg>
                                AI Voices & Speech Understanding
                            </li>
                            <li class="subscription-feature">
                                <svg class="subscription-feature-icon" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                                </svg>
                                Multi-lingual code generation
                            </li>
                            <li class="subscription-feature">
                                <svg class="subscription-feature-icon" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                                </svg>
                                Advanced prompt optimization
                            </li>
                            <li class="subscription-feature">
                                <svg class="subscription-feature-icon" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                                </svg>
                                Complete data privacy protection
                            </li>
                        </ul>

                        <div class="subscription-modal-actions">
                            <a href="/subscribe" class="subscription-btn subscription-btn-primary">Subscribe Now</a>
                            <button class="subscription-btn subscription-btn-secondary" onclick="if(window.subscriptionModal) subscriptionModal.close()">Maybe Later</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add CSS styles for the modal
        const styles = `
            <style>
                .subscription-modal {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.6);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    z-index: 1000;
                    backdrop-filter: blur(4px);
                }

                .subscription-modal-content {
                    background: linear-gradient(135deg, #fff 0%, #fef7f7 100%);
                    border-radius: 16px;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
                    max-width: 480px;
                    width: 90%;
                    max-height: 90vh;
                    overflow-y: auto;
                    position: relative;
                    border: 1px solid rgba(255, 182, 193, 0.3);
                }

                .subscription-modal-close {
                    position: absolute;
                    top: 16px;
                    right: 16px;
                    background: none;
                    border: none;
                    font-size: 24px;
                    cursor: pointer;
                    color: #666;
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s ease;
                }

                .subscription-modal-close:hover {
                    background: rgba(255, 182, 193, 0.2);
                    color: #333;
                }

                .subscription-modal-header {
                    text-align: center;
                    padding: 32px 32px 16px;
                    background: linear-gradient(135deg, #FFB6C1 0%, #FFA07A  50%, #FF6347 100%);
                    background-clip: text;
                    -webkit-background-clip: text;
                    color: transparent;
                }

                .subscription-modal-title {
                    font-size: 28px;
                    font-weight: 700;
                    margin: 0 0 8px;
                    background: linear-gradient(135deg, #FFB6C1 0%, #FFA07A 50%, #FF6347 100%);
                    background-clip: text;
                    -webkit-background-clip: text;
                    color: transparent;
                }

                .subscription-modal-subtitle {
                    font-size: 16px;
                    color: #666;
                    margin: 0;
                    font-weight: 400;
                }

                .subscription-modal-body {
                    padding: 0 32px 32px;
                }

                .subscription-pricing {
                    text-align: center;
                    margin: 24px 0 32px;
                    padding: 20px;
                    background: linear-gradient(135deg, rgba(255, 182, 193, 0.1) 0%, rgba(255, 160, 122, 0.1) 100%);
                    border-radius: 12px;
                    border: 1px solid rgba(255, 182, 193, 0.3);
                }

                .subscription-price {
                    font-size: 36px;
                    font-weight: 700;
                    background: linear-gradient(135deg, #FFB6C1 0%, #FFA07A 50%, #FF6347 100%);
                    background-clip: text;
                    -webkit-background-clip: text;
                    color: transparent;
                    margin-bottom: 4px;
                }

                .subscription-period {
                    font-size: 16px;
                    color: #666;
                    font-weight: 500;
                }

                .subscription-features {
                    list-style: none;
                    padding: 0;
                    margin: 0 0 32px;
                }

                .subscription-feature {
                    display: flex;
                    align-items: center;
                    padding: 12px 0;
                    font-size: 15px;
                    color: #333;
                    border-bottom: 1px solid rgba(255, 182, 193, 0.2);
                }

                .subscription-feature:last-child {
                    border-bottom: none;
                }

                .subscription-feature-icon {
                    width: 20px;
                    height: 20px;
                    margin-right: 12px;
                    color: #FF6347;
                    flex-shrink: 0;
                }

                .subscription-modal-actions {
                    display: flex;
                    gap: 12px;
                    flex-direction: column;
                }

                .subscription-btn {
                    padding: 16px 24px;
                    border-radius: 12px;
                    font-size: 16px;
                    font-weight: 600;
                    text-decoration: none;
                    text-align: center;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    border: none;
                    display: block;
                }

                .subscription-btn-primary {
                    background: linear-gradient(90deg, #d79f2a, #d34675);
                    color: white;
                    box-shadow: 0 4px 15px rgba(215, 159, 42, 0.4);
                    transition: all 0.2s ease;
                }

                .subscription-btn-primary:hover {
                    background: linear-gradient(90deg, #c48d24, #c23e67);
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(215, 159, 42, 0.5);
                    text-decoration: none;
                    color: white;
                }

                .subscription-btn-secondary {
                    background: rgba(255, 182, 193, 0.1);
                    color: #666;
                    border: 1px solid rgba(255, 182, 193, 0.3);
                }

                .subscription-btn-secondary:hover {
                    background: rgba(255, 182, 193, 0.2);
                    color: #333;
                }

                .subscription-modal.show {
                    opacity: 1;
                    visibility: visible;
                }

                @media (max-width: 600px) {
                    .subscription-modal-content {
                        margin: 20px;
                        width: calc(100% - 40px);
                    }
                    
                    .subscription-modal-header,
                    .subscription-modal-body {
                        padding-left: 24px;
                        padding-right: 24px;
                    }
                    
                    .subscription-modal-title {
                        font-size: 24px;
                    }
                    
                    .subscription-price {
                        font-size: 32px;
                    }
                }
            </style>
        `;

        document.head.insertAdjacentHTML('beforeend', styles);
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
}

// Create global instance when DOM is ready
if (typeof window.subscriptionModal === 'undefined') {
    let subscriptionModal;

    function initSubscriptionModal() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                subscriptionModal = new window.SubscriptionModal();
                window.subscriptionModal = subscriptionModal;
            });
        } else {
            subscriptionModal = new window.SubscriptionModal();
            window.subscriptionModal = subscriptionModal;
        }
    }

    // Initialize
    initSubscriptionModal();

    // Helper function for easy access
    window.requireSubscription = async function(action = 'access this feature') {
        if (!window.subscriptionModal) {
            console.warn('SubscriptionModal not initialized yet');
            return false;
        }
        return await window.subscriptionModal.requireSubscription(action);
    };

    // Helper function to check if user is subscribed
    window.isUserSubscribed = async function() {
        if (!window.subscriptionModal) {
            console.warn('SubscriptionModal not initialized yet');
            return false;
        }
        return await window.subscriptionModal.checkSubscription();
    };
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SubscriptionModal, subscriptionModal, requireSubscription, isUserSubscribed };
}
