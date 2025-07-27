// Checkout Dialog with Embedded Stripe Checkout
class CheckoutDialog {
    constructor() {
        this.modal = null;
        this.isOpen = false;
        this.currentUser = null;
        this.stripe = null;
        this.elements = null;
        this.embeddedCheckout = null;
        this.subscriptionType = 'monthly';
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
                    </div>

                    <div class="checkout-dialog-body">
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

    async show() {
        if (this.modal) {
            this.modal.style.display = 'flex';
            this.modal.classList.add('show');
            this.isOpen = true;
            document.body.style.overflow = 'hidden';
            
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
    // Update radio button selection
    const radioBtn = document.querySelector(`input[name="pricing"][value="${subscriptionType}"]`);
    if (radioBtn) {
        radioBtn.checked = true;
    }
    await checkoutDialog.show();
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CheckoutDialog, checkoutDialog, showCheckoutDialog };
}