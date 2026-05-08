// Checkout Dialog with Embedded Stripe Checkout
const CHECKOUT_PRICING = {
    monthly: '$9.99',
    annual: '$99.99',
    savingsLabel: 'save 17%',
};

class CheckoutDialog {
    constructor() {
        this.modal = null;
        this.isOpen = false;
        this.currentUser = null;
        this.stripe = null;
        this.elements = null;
        this.embeddedCheckout = null;
        this.subscriptionType = 'monthly';
        this.offerType = 'plan';
        this.allowCreditChoice = window.location.pathname === '/playground';
        this.init();
    }

    init() {
        // Check if modal already exists
        if (document.getElementById('checkout-dialog')) {
            return;
        }

        // Initialize Stripe
        this.initStripe();
        
        // Create modal HTML
        this.createModal();
        this.bindEvents();
    }

    initStripe() {
        // Get Stripe publishable key from the page (should be set by the backend)
        const stripeKey = window.STRIPE_PUBLISHABLE_KEY || 'pk_live_51KjJGaDtz2XsjQRO1wdSdz8zS4bXzXq0tJ2m7lzJLdFpGhOdmGzX8fWwO9hm3vHdVVbfQc0XLJlT8l6KZGHJdUdl00zLUOHnMy';
        this.stripe = Stripe(stripeKey);
    }

    createModal() {
        // Wait for DOM to be ready
        if (!document.body) {
            console.warn('Document body not ready, deferring modal creation');
            setTimeout(() => this.createModal(), 100);
            return;
        }

        const modalHTML = `
            <div id="checkout-dialog" class="checkout-dialog" style="display: none;">
                <div class="checkout-dialog-content">
                    <button class="checkout-dialog-close" onclick="window.checkoutDialog && window.checkoutDialog.close()">×</button>
                    
                    <div class="checkout-dialog-header">
                        <h2 class="checkout-dialog-title">Cloud AI Text Generator</h2>
                        <p class="checkout-dialog-subtitle">Start instantly with our most popular plan.</p>
                        <div class="checkout-price-highlight" role="status" aria-live="polite">
                            <span class="checkout-price-value">${CHECKOUT_PRICING.monthly}</span>
                            <span class="checkout-price-period">/month</span>
                            <span class="checkout-price-note">or ${CHECKOUT_PRICING.annual}/year (${CHECKOUT_PRICING.savingsLabel})</span>
                        </div>
                        <div class="checkout-pricing-toggle" role="radiogroup" aria-label="Billing period">
                            <label class="checkout-toggle-label">
                                <input type="radio" name="pricing" value="monthly" checked>
                                <span class="checkout-toggle-text">Monthly · ${CHECKOUT_PRICING.monthly}/mo</span>
                            </label>
                            <label class="checkout-toggle-label">
                                <input type="radio" name="pricing" value="annual">
                                <span class="checkout-toggle-text">Annual · ${CHECKOUT_PRICING.annual}/yr</span>
                            </label>
                        </div>
                        <div class="checkout-offer-chooser" id="checkout-offer-chooser" style="display: none;">
                            <button type="button" class="checkout-offer-btn is-active" data-offer="plan">Add a plan</button>
                            <button type="button" class="checkout-offer-btn" data-offer="credits">Add API credits</button>
                        </div>
                    </div>

                    <div class="checkout-dialog-body">
                        <div id="checkout-credits-panel" class="checkout-credits-panel" style="display: none;">
                            <h3>API credits</h3>
                            <p>Need pay-as-you-go API credits instead of a recurring plan?</p>
                            <div class="checkout-credits-actions">
                                <a class="checkout-btn checkout-btn-secondary" href="/contact">Contact support for credits</a>
                                <button type="button" class="checkout-btn" id="checkout-switch-plan-btn">Use subscription plan</button>
                            </div>
                        </div>
                        <div id="checkout-container">
                            <div class="checkout-loading">
                                <div class="checkout-spinner"></div>
                                <p>Loading secure checkout...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modal = document.getElementById('checkout-dialog');
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

        // Handle pricing toggle
        document.addEventListener('change', (e) => {
            if (e.target.name === 'pricing') {
                this.subscriptionType = e.target.value;
                if (this.isOpen) {
                    this.loadCheckout();
                }
            }
        });

        document.addEventListener('click', (e) => {
            const offerBtn = e.target.closest('.checkout-offer-btn');
            if (offerBtn) {
                this.setOfferType(offerBtn.dataset.offer || 'plan');
            }

            if (e.target.id === 'checkout-switch-plan-btn') {
                this.setOfferType('plan');
            }
        });
    }

    async getCurrentUser() {
        try {
            const response = await fetch('/api/current-user');
            if (response.ok) {
                const user = await response.json();
                this.currentUser = user;
                return user;
            }
            return null;
        } catch (error) {
            console.error('Error getting current user:', error);
            return null;
        }
    }

    async loadCheckout() {
        if (this.offerType === 'credits') {
            this.renderCreditsState();
            return;
        }

        const user = await this.getCurrentUser();
        if (!user) {
            this.showError('Please log in to subscribe');
            return;
        }

        if (user.is_subscribed) {
            this.showError('You already have an active subscription');
            return;
        }

        try {
            const response = await fetch('/create-checkout-session-embedded', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    uid: user.id,
                    secret: user.secret || '',
                    email: user.email,
                    subscription_type: this.subscriptionType,
                    referral: ''
                })
            });

            if (!response.ok) {
                throw new Error('Failed to create checkout session');
            }

            const { clientSecret } = await response.json();
            
            // Clear previous checkout if it exists
            if (this.embeddedCheckout) {
                this.embeddedCheckout.destroy();
            }

            // Create new embedded checkout
            this.embeddedCheckout = await this.stripe.initEmbeddedCheckout({
                clientSecret
            });

            // Mount the checkout
            const checkoutContainer = document.getElementById('checkout-container');
            checkoutContainer.innerHTML = '';
            this.embeddedCheckout.mount('#checkout-container');

        } catch (error) {
            console.error('Error loading checkout:', error);
            this.showError('Failed to load checkout. Please try again.');
        }
    }

    showError(message) {
        const checkoutContainer = document.getElementById('checkout-container');
        checkoutContainer.innerHTML = `
            <div class="checkout-error">
                <p>${message}</p>
                <button onclick="if(window.checkoutDialog) checkoutDialog.close()" class="checkout-btn">Close</button>
            </div>
        `;
    }

    renderCreditsState() {
        const checkoutContainer = document.getElementById('checkout-container');
        if (checkoutContainer) {
            checkoutContainer.innerHTML = '';
        }

        const creditsPanel = document.getElementById('checkout-credits-panel');
        if (creditsPanel) {
            creditsPanel.style.display = 'block';
        }
    }

    setOfferType(offerType = 'plan') {
        this.offerType = offerType;
        const buttons = document.querySelectorAll('.checkout-offer-btn');
        buttons.forEach((btn) => {
            btn.classList.toggle('is-active', btn.dataset.offer === offerType);
        });

        const creditsPanel = document.getElementById('checkout-credits-panel');
        if (creditsPanel) {
            creditsPanel.style.display = offerType === 'credits' ? 'block' : 'none';
        }

        const checkoutContainer = document.getElementById('checkout-container');
        if (checkoutContainer) {
            checkoutContainer.style.display = offerType === 'credits' ? 'none' : 'block';
        }

        if (this.isOpen && offerType === 'plan') {
            this.loadCheckout();
        } else if (this.isOpen && offerType === 'credits') {
            this.renderCreditsState();
        }
    }

    async show() {
        if (this.modal) {
            const offerChooser = document.getElementById('checkout-offer-chooser');
            if (offerChooser) {
                offerChooser.style.display = this.allowCreditChoice ? 'flex' : 'none';
            }

            this.modal.style.display = 'flex';
            this.modal.classList.add('show');
            this.isOpen = true;
            document.body.style.overflow = 'hidden';
            this.setOfferType(this.allowCreditChoice ? this.offerType : 'plan');
            
            // Load checkout when modal is shown
            await this.loadCheckout();
        }
    }

    close() {
        if (this.modal) {
            this.modal.style.display = 'none';
            this.modal.classList.remove('show');
            this.isOpen = false;
            document.body.style.overflow = '';
            
            // Destroy embedded checkout when closing
            if (this.embeddedCheckout) {
                this.embeddedCheckout.destroy();
                this.embeddedCheckout = null;
            }
        }
    }
}

// Create global instance when DOM is ready
let checkoutDialog;

function initCheckoutDialog() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            checkoutDialog = new CheckoutDialog();
            window.checkoutDialog = checkoutDialog;
        });
    } else {
        checkoutDialog = new CheckoutDialog();
        window.checkoutDialog = checkoutDialog;
    }
}

// Initialize
initCheckoutDialog();

// Helper function for easy access
async function showCheckoutDialog(subscriptionType = 'monthly') {
    if (!checkoutDialog) {
        console.warn('CheckoutDialog not initialized yet, waiting...');
        // Wait for initialization
        let attempts = 0;
        while (!checkoutDialog && attempts < 50) {
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }
        if (!checkoutDialog) {
            console.error('CheckoutDialog failed to initialize after 5 seconds');
            return;
        }
    }
    checkoutDialog.subscriptionType = subscriptionType;
    checkoutDialog.offerType = window.location.pathname === '/playground' ? checkoutDialog.offerType : 'plan';
    // Update radio button selection
    const radioBtn = document.querySelector(`input[name="pricing"][value="${subscriptionType}"]`);
    if (radioBtn) {
        radioBtn.checked = true;
    }
    await checkoutDialog.show();
}

window.showCheckoutDialog = showCheckoutDialog;

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CheckoutDialog, checkoutDialog, showCheckoutDialog };
}
