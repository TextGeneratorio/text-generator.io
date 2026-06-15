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
                    <button class="subscription-modal-close" onclick="if(window.subscriptionModal) window.subscriptionModal.close()">×</button>
                    
                    <div class="subscription-modal-header">
                        <div class="subscription-modal-brand">
                            <div class="subscription-modal-logo">
                                <img src="/static/img/android-chrome-192x192.png" alt="Text Generator" width="32" height="32">
                            </div>
                            <div>
                                <p class="subscription-modal-kicker">Text Generator</p>
                                <h2 class="subscription-modal-title">Subscription Required</h2>
                            </div>
                        </div>
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
                            <button type="button" class="subscription-btn subscription-btn-primary mdl-button mdl-js-button mdl-button--raised mdl-button--accent mdl-js-ripple-effect" onclick="if(window.subscriptionModal) window.subscriptionModal.close(); if(window.showCheckoutDialog) showCheckoutDialog('monthly');">Subscribe Now</button>
                            <button class="subscription-btn subscription-btn-secondary" onclick="if(window.subscriptionModal) window.subscriptionModal.close()">Maybe Later</button>
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
                    background: linear-gradient(135deg, #fff9ef 0%, #fff3dd 100%);
                    border-radius: 16px;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
                    max-width: 480px;
                    width: 90%;
                    max-height: 90vh;
                    overflow-y: auto;
                    position: relative;
                    border: 1px solid rgba(245, 158, 11, 0.22);
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
                    background: rgba(245, 158, 11, 0.14);
                    color: #333;
                }

                .subscription-modal-header {
                    text-align: center;
                    padding: 30px 32px 16px;
                }

                .subscription-modal-brand {
                    display: inline-flex;
                    align-items: center;
                    gap: 12px;
                    margin-bottom: 10px;
                    text-align: left;
                }

                .subscription-modal-logo {
                    width: 44px;
                    height: 44px;
                    border-radius: 13px;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    background: linear-gradient(135deg, #f59e0b, #ea580c);
                    box-shadow: 0 12px 24px rgba(234, 88, 12, 0.22);
                    flex-shrink: 0;
                }

                .subscription-modal-logo img {
                    display: block;
                }

                .subscription-modal-kicker {
                    margin: 0 0 4px;
                    font: 700 0.72rem/1 'IBM Plex Mono', monospace;
                    text-transform: uppercase;
                    letter-spacing: 0.12em;
                    color: #c2410c;
                }

                .subscription-modal-title {
                    font-size: 28px;
                    font-weight: 700;
                    margin: 0;
                    background: linear-gradient(135deg, #c2410c 0%, #f59e0b 52%, #fbbf24 100%);
                    background-clip: text;
                    -webkit-background-clip: text;
                    color: transparent;
                }

                .subscription-modal-subtitle {
                    font-size: 16px;
                    color: #7c5b43;
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
                    background: linear-gradient(135deg, rgba(245, 158, 11, 0.12) 0%, rgba(234, 88, 12, 0.12) 100%);
                    border-radius: 12px;
                    border: 1px solid rgba(245, 158, 11, 0.22);
                }

                .subscription-price {
                    font-size: 36px;
                    font-weight: 700;
                    background: linear-gradient(135deg, #c2410c 0%, #f59e0b 52%, #fbbf24 100%);
                    background-clip: text;
                    -webkit-background-clip: text;
                    color: transparent;
                    margin-bottom: 4px;
                }

                .subscription-period {
                    font-size: 16px;
                    color: #7c5b43;
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
                    color: #3b2a1f;
                    border-bottom: 1px solid rgba(245, 158, 11, 0.16);
                }

                .subscription-feature:last-child {
                    border-bottom: none;
                }

                .subscription-feature-icon {
                    width: 20px;
                    height: 20px;
                    margin-right: 12px;
                    color: #ea580c;
                    flex-shrink: 0;
                }

                .subscription-modal-actions {
                    display: flex;
                    gap: 12px;
                    flex-direction: column;
                }

                .subscription-btn {
                    padding: 16px 24px;
                    font-family: inherit;
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
                    background: linear-gradient(90deg, #ea580c, #f59e0b);
                    color: white;
                    box-shadow: 0 4px 15px rgba(234, 88, 12, 0.28);
                    transition: all 0.2s ease;
                }

                .subscription-btn-primary:hover {
                    background: linear-gradient(90deg, #c2410c, #d97706);
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(234, 88, 12, 0.36);
                    text-decoration: none;
                    color: white;
                }

                .subscription-btn-secondary {
                    background: #fff1e6;
                    color: #9a3412;
                    border: 1px solid rgba(245, 158, 11, 0.16);
                }

                .subscription-btn-secondary:hover {
                    background: #fde8d8;
                    color: #7c2d12;
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

        if (typeof componentHandler !== 'undefined') {
            componentHandler.upgradeAllRegistered();
        }
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
