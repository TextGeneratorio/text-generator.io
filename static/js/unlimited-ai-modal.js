// Unlimited AI Offerings Modal JavaScript
if (typeof window.UnlimitedAIModal === 'undefined') {
window.UnlimitedAIModal = class UnlimitedAIModal {
    constructor() {
        this.modal = null;
        this.isOpen = false;
        this.init();
    }

    init() {
        // Check if modal already exists
        if (document.getElementById('unlimited-ai-modal')) {
            this.modal = document.getElementById('unlimited-ai-modal');
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
            <div id="unlimited-ai-modal" class="unlimited-ai-modal" style="display: none;">
                <div class="unlimited-ai-modal-content">
                    <button class="unlimited-ai-modal-close" onclick="if(window.unlimitedAIModal) unlimitedAIModal.close()">×</button>
                    
                    <div class="unlimited-ai-modal-header">
                        <h2 class="unlimited-ai-modal-title">Unlimited AI Text Editing & Speech Generation</h2>
                        <p class="unlimited-ai-modal-subtitle">Access all premium AI features with your subscription</p>
                    </div>

                    <div class="unlimited-ai-modal-body">
                        <div class="unlimited-ai-pricing">
                            <div class="unlimited-ai-price">$19.00 USD</div>
                            <div class="unlimited-ai-period">Monthly</div>
                        </div>

                        <ul class="unlimited-ai-features">
                            <li class="unlimited-ai-feature">
                                <svg class="unlimited-ai-feature-icon" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                                </svg>
                                Quick Start - The fastest way to get started using the API
                            </li>
                            <li class="unlimited-ai-feature">
                                <svg class="unlimited-ai-feature-icon" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                                </svg>
                                Multi-lingual generation - Instruction following, logic and creativity in almost all languages
                            </li>
                            <li class="unlimited-ai-feature">
                                <svg class="unlimited-ai-feature-icon" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                                </svg>
                                Code generation - Polyglot Code, Autocomplete, Translation, Explanation generation
                            </li>
                            <li class="unlimited-ai-feature">
                                <svg class="unlimited-ai-feature-icon" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                                </svg>
                                Complete data privacy - We do not store any private data sent to the APIs
                            </li>
                            <li class="unlimited-ai-feature">
                                <svg class="unlimited-ai-feature-icon" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                                </svg>
                                Prompt Tuning - Advanced prompt optimization for better AI responses
                            </li>
                            <li class="unlimited-ai-feature">
                                <svg class="unlimited-ai-feature-icon" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                                </svg>
                                AI Text Editor - Built-in AI-powered text editing and enhancement tools
                            </li>
                        </ul>

                        <div class="unlimited-ai-modal-actions">
                            <a href="/subscribe" class="unlimited-ai-btn unlimited-ai-btn-primary">Subscribe Now</a>
                            <button class="unlimited-ai-btn unlimited-ai-btn-secondary" onclick="if(window.unlimitedAIModal) unlimitedAIModal.close()">Maybe Later</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add CSS styles for the modal
        const styles = `
            <style>
                .unlimited-ai-modal {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.6);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    z-index: 1001;
                    backdrop-filter: blur(4px);
                }

                .unlimited-ai-modal-content {
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

                .unlimited-ai-modal-close {
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

                .unlimited-ai-modal-close:hover {
                    background: rgba(255, 182, 193, 0.2);
                    color: #333;
                }

                .unlimited-ai-modal-header {
                    text-align: center;
                    padding: 32px 32px 16px;
                }

                .unlimited-ai-modal-title {
                    font-size: 24px;
                    font-weight: 700;
                    margin: 0 0 8px;
                    background: linear-gradient(135deg, #FFB6C1 0%, #FFA07A 50%, #FF6347 100%);
                    background-clip: text;
                    -webkit-background-clip: text;
                    color: transparent;
                }

                .unlimited-ai-modal-subtitle {
                    font-size: 16px;
                    color: #666;
                    margin: 0;
                    font-weight: 400;
                }

                .unlimited-ai-modal-body {
                    padding: 0 32px 32px;
                }

                .unlimited-ai-pricing {
                    text-align: center;
                    margin: 24px 0 32px;
                    padding: 20px;
                    background: linear-gradient(135deg, rgba(255, 182, 193, 0.1) 0%, rgba(255, 160, 122, 0.1) 100%);
                    border-radius: 12px;
                    border: 1px solid rgba(255, 182, 193, 0.3);
                }

                .unlimited-ai-price {
                    font-size: 36px;
                    font-weight: 700;
                    background: linear-gradient(135deg, #FFB6C1 0%, #FFA07A 50%, #FF6347 100%);
                    background-clip: text;
                    -webkit-background-clip: text;
                    color: transparent;
                    margin-bottom: 4px;
                }

                .unlimited-ai-period {
                    font-size: 16px;
                    color: #666;
                    font-weight: 500;
                }

                .unlimited-ai-features {
                    list-style: none;
                    padding: 0;
                    margin: 0 0 32px;
                }

                .unlimited-ai-feature {
                    display: flex;
                    align-items: flex-start;
                    padding: 12px 0;
                    font-size: 15px;
                    color: #333;
                    border-bottom: 1px solid rgba(255, 182, 193, 0.2);
                    line-height: 1.4;
                }

                .unlimited-ai-feature:last-child {
                    border-bottom: none;
                }

                .unlimited-ai-feature-icon {
                    width: 20px;
                    height: 20px;
                    margin-right: 12px;
                    margin-top: 2px;
                    color: #FF6347;
                    flex-shrink: 0;
                }

                .unlimited-ai-modal-actions {
                    display: flex;
                    gap: 12px;
                    flex-direction: column;
                }

                .unlimited-ai-btn {
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

                .unlimited-ai-btn-primary {
                    background: linear-gradient(90deg, #d79f2a, #d34675);
                    color: white;
                    box-shadow: 0 4px 15px rgba(215, 159, 42, 0.4);
                    transition: all 0.2s ease;
                }

                .unlimited-ai-btn-primary:hover {
                    background: linear-gradient(90deg, #c48d24, #c23e67);
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(215, 159, 42, 0.5);
                    text-decoration: none;
                    color: white;
                }

                .unlimited-ai-btn-secondary {
                    background: rgba(255, 182, 193, 0.1);
                    color: #666;
                    border: 1px solid rgba(255, 182, 193, 0.3);
                }

                .unlimited-ai-btn-secondary:hover {
                    background: rgba(255, 182, 193, 0.2);
                    color: #333;
                }

                .unlimited-ai-modal.show {
                    opacity: 1;
                    visibility: visible;
                }

                @media (max-width: 600px) {
                    .unlimited-ai-modal-content {
                        margin: 20px;
                        width: calc(100% - 40px);
                    }
                    
                    .unlimited-ai-modal-header,
                    .unlimited-ai-modal-body {
                        padding-left: 24px;
                        padding-right: 24px;
                    }
                    
                    .unlimited-ai-modal-title {
                        font-size: 20px;
                    }
                    
                    .unlimited-ai-price {
                        font-size: 32px;
                    }
                }
            </style>
        `;

        document.head.insertAdjacentHTML('beforeend', styles);
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modal = document.getElementById('unlimited-ai-modal');
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
if (typeof window.unlimitedAIModal === 'undefined') {
    let unlimitedAIModal;

    function initUnlimitedAIModal() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                unlimitedAIModal = new window.UnlimitedAIModal();
                window.unlimitedAIModal = unlimitedAIModal;
            });
        } else {
            unlimitedAIModal = new window.UnlimitedAIModal();
            window.unlimitedAIModal = unlimitedAIModal;
        }
    }

    // Initialize
    initUnlimitedAIModal();

    // Helper function for easy access
    window.showUnlimitedAIModal = function() {
        if (!window.unlimitedAIModal) {
            console.warn('UnlimitedAIModal not initialized yet');
            return;
        }
        window.unlimitedAIModal.show();
    };
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { UnlimitedAIModal, unlimitedAIModal, showUnlimitedAIModal };
}