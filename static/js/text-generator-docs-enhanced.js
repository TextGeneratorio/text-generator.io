/**
 * Enhanced Text Generator Docs
 * 
 * This class extends the base TextGeneratorDocs with advanced features:
 * - Improved typing history tracking for better suggestions
 * - Wide mode layout for better screen utilization
 * - Enhanced tab completion with history-based suggestions
 * - Proper min_probability handling for different generation modes
 * - Code block syntax highlighting
 */

class EnhancedTextGeneratorDocs extends TextGeneratorDocs {
  /**
   * Static configuration for the enhanced text generator
   */
  static get CONFIG() {
    return {
      // Autocomplete settings
      MIN_SUGGESTION_LENGTH: 2,
      AUTOCOMPLETE_DEBOUNCE_MS: 800,
      AUTOCOMPLETE_MIN_PROB: 0.7,
      BULK_GEN_MIN_PROB: 0.2,
      TYPING_DEBOUNCE: 800, // Debounce time before triggering autocomplete check (increased back)
      CURSOR_TOLERANCE: 3, // How much cursor can move before invalidating suggestion
      
      // Typing history settings
      MAX_TYPING_HISTORY: 100,
      TYPING_TIMEOUT_MS: 2000,
      
      // Claude API settings
      CLAUDE_MODEL: "claude-sonnet-4-20250514",
      CLAUDE_MAX_TOKENS: 5999,
      CLAUDE_TEMPERATURE: 0.8,
      
      // UI settings
      WIDE_MODE_STORAGE_KEY: 'tgdocs-wide-mode',
      CLAUDE_TOGGLE_STORAGE_KEY: 'tgdocs-use-claude'
    };
  }

  /**
   * @constructor
   * @param {Object} options - Initialization options
   */
  constructor(options) {
    // Call parent constructor
    super(options);
    
    // Initialize enhanced properties
    this.typingHistory = [];
    this.deletedText = {};
    this.isWideMode = localStorage.getItem(EnhancedTextGeneratorDocs.CONFIG.WIDE_MODE_STORAGE_KEY) === 'true';
    
    // Track pending suggestion requests to handle race conditions
    this.pendingSuggestionRequests = {};
    this.lastRequestId = 0;
    this.lastTypingTimestamp = 0;
    this.textChangeCounter = 0;  // Counter that increments for each text change
    
    // Apply wide mode if enabled
    if (this.isWideMode) {
      this.enableWideMode();
    }
    
    console.log('Enhanced Text Generator Docs constructed');
  }
  
  //------------------------------------------------------
  // Lifecycle Methods
  //------------------------------------------------------
  
  /**
   * Initialize the enhanced text generator
   * @override
   */
  async init() {
    try {
      // Call parent init method FIRST - this should find elements via options passed during instantiation
      await super.init();

      // Add other enhanced UI elements immediately (assuming they don't depend on the buttons yet)
      // this.addWideModeToggle(); // Removed fullscreen icon
      this.initDebounceSettings(); // Needs this.editor from super.init()
      this.initEnhancedEventListeners(); // Needs this.editor from super.init()
      this.addToolbarTooltips(); // Should be safe

      console.log("Attempting to configure buttons after delay...");

      // Prefer using properties set by base class constructor if available, fallback to getElementById
      const autowriteBtn = this.generateContentButton || document.getElementById('generate-content-btn');
      const rewriteBtn = this.rewriteContentButton || document.getElementById('rewrite-content-btn');

      // Configure "Write from Cursor" Button
      if (autowriteBtn) {
          console.log("#generate-content-btn found/referenced. Configuring...");
          autowriteBtn.innerHTML = '<i class="material-icons">auto_fix_high</i> Write from Cursor (Ctrl+Space)';
          autowriteBtn.setAttribute('title', 'Generate text starting from cursor (Ctrl+Space)');
          // Remove potential old listeners before adding new one
          autowriteBtn.removeEventListener('click', this._boundAutoWriteFromCursor);
          this._boundAutoWriteFromCursor = () => this.autoWriteFromCursor(); // Store bound function
          autowriteBtn.addEventListener('click', this._boundAutoWriteFromCursor);
      } else {
          console.warn('Button #generate-content-btn STILL not found.');
      }

      // Configure "Rewrite" Button
      if (rewriteBtn) {
          console.log("#rewrite-content-btn found/referenced. Configuring...");
          rewriteBtn.innerHTML = '<i class="material-icons">edit_note</i> Rewrite (Ctrl+G)';
          rewriteBtn.setAttribute('title', 'Rewrite selected text or whole document with instructions (Ctrl+G)');
          // Remove potential old listeners before adding new one
          rewriteBtn.removeEventListener('click', this._boundRewriteWithInstructions);
          this._boundRewriteWithInstructions = () => this.showRewriteDialog(); 
          rewriteBtn.addEventListener('click', this._boundRewriteWithInstructions);
      } else {
          console.warn('Button #rewrite-content-btn STILL not found.');
      }

      // Expose this instance globally for testing
      if (typeof window !== 'undefined') {
        window.scene = this;
      }

      console.log('Enhanced Text Generator Docs initialized');
    } catch (error) {
      console.error('Error initializing enhanced text generator:', error);
    }
  }
  
  /**
   * Initialize enhanced event listeners
   */
  initEnhancedEventListeners() {
    // Capture Tab globally to accept suggestion popup whenever active
    document.addEventListener('keydown', event => {
      // Check if Tab pressed and either suggestion is active OR editor has focus
      if (event.key === 'Tab' && (this.suggestionActive || (this.editor && this.editor.hasFocus()))) {
        event.preventDefault();
        event.stopImmediatePropagation();
        // Only accept suggestion if one is active
        if (this.suggestionActive) {
          this.acceptSuggestion();
        } else {
          // Insert a tab character if in editor and no suggestion
          this.editor.insertText(this.editor.getSelection() ? this.editor.getSelection().index : 0, '\t', 'user');
        }
      }
      
      // Hide suggestion on arrow keys (new functionality)
      if (this.suggestionActive && (event.key === 'ArrowLeft' || event.key === 'ArrowRight' || 
          event.key === 'ArrowUp' || event.key === 'ArrowDown')) {
        console.log('Arrow key pressed while suggestion active, hiding suggestion');
        this.hideSuggestion();
      }
    }, true);

    // Add listeners to hide popup on scroll/resize
    this._boundHideSuggestion = this.hideSuggestion.bind(this); // Bind for listener removal
    window.addEventListener('scroll', this._boundHideSuggestion, true); // Use capture phase
    window.addEventListener('resize', this._boundHideSuggestion); 

    // Add listener for document clicks to hide suggestions when clicking elsewhere
    document.addEventListener('mousedown', (event) => {
      if (this.suggestionActive) {
        // Get the editor element and suggestion element
        const editorElement = this.editor.root;
        const suggestionElement = this.suggestionElement;
        
        // Check if click is outside both the editor and suggestion element
        if (!editorElement.contains(event.target) && 
            !(suggestionElement && suggestionElement.contains(event.target))) {
          console.log('Click outside editor/suggestion detected, hiding suggestion');
          this.hideSuggestion();
        }
      }
    }, true);

    // Enhanced selection change handling
    if (this.editor) {
      // Track cursor movement to hide suggestions when cursor moves
      this.editor.on('selection-change', (range, oldRange, source) => {
        // If suggestion is active and cursor moves more than 1 character or changes via API
        if (this.suggestionActive && 
            ((range && oldRange && Math.abs(range.index - oldRange.index) > 0) || source === 'api')) {
          console.log('Cursor moved or selection changed, hiding suggestion');
          this.hideSuggestion();
        }
      });
      
      // Rest of the existing code...
    }

    // Rebind Quill Tab key to accept suggestion when popup is active
    if (this.editor && this.editor.keyboard) {
      // Remove default Tab bindings
      delete this.editor.keyboard.bindings[9];
      // Add custom Tab binding
      this.editor.keyboard.addBinding({ key: 9 }, (range, context) => {
        // When in editor, always handle Tab internally
        if (this.suggestionActive) {
          this.acceptSuggestion();
        } else {
          // Insert tab character
          this.editor.insertText(range.index, '\t', 'user');
        }
        return false; // Always prevent default Tab behavior
      });
    }

    // Global listener for Ctrl+Space to open Autowrite dialog
    document.addEventListener('keydown', (event) => {
      // Check if Ctrl+Space is pressed AND the editor currently has focus
      if (event.ctrlKey && event.code === 'Space' && this.editor && this.editor.hasFocus()) {
          event.preventDefault();     // Prevent default browser behavior (e.g., inserting space)
          event.stopPropagation();  // Stop event from bubbling further
          console.log('Ctrl+Space detected, triggering Write from Cursor.');
          this.autoWriteFromCursor(); // Trigger Write from Cursor directly
      }
    }, true); // Use capture phase: true

    // Global listener for Ctrl+G to trigger Rewrite
    document.addEventListener('keydown', (event) => {
      // Check if Ctrl+G is pressed AND the editor currently has focus
      if (event.ctrlKey && event.key === 'g' && this.editor && this.editor.hasFocus()) {
          event.preventDefault();     // Prevent default browser behavior (e.g., find)
          event.stopPropagation();  // Stop event from bubbling further
          console.log('Ctrl+G detected, triggering Rewrite.');
          this.showRewriteDialog(); // Show rewrite dialog instead
      }
    }, true); // Use capture phase: true

    // TODO: Consider adding a MutationObserver on the editor for complex reflows
  }
  
  /**
   * Override default debounce settings
   */
  initDebounceSettings() {
    // Override handleEditorChange to implement refined suggestion handling
    this.editor.off('text-change'); // Remove potential existing listener from base class init
    this.editor.on('text-change', (delta, oldDelta, source) => {
        // If change isn't from the user, ignore
        if (source !== 'user') return;

        let shouldHideSuggestion = true;
        let incrementCounter = true;

        // --- Analyze change for hiding popup --- 
        if (this.suggestionActive && delta.ops) {
            // Check if the change is a simple text insertion
            if (delta.ops.length === 1 && delta.ops[0].insert && typeof delta.ops[0].insert === 'string') {
                const insertedText = delta.ops[0].insert;

                // Case 1: User typed only spaces - KEEP suggestion visible
                if (/^\s+$/.test(insertedText)) {
                    shouldHideSuggestion = false; // Keep popup visible
                    incrementCounter = false; // Don't invalidate pending requests
                }
                // Case 2: Any other insertion -> HIDE suggestion
            }
            // Case 3: Deletions or complex changes -> HIDE suggestion
            else {
                shouldHideSuggestion = true; // Ensure hiding
            }
        }

        // --- Apply decisions --- 
        if (shouldHideSuggestion && this.suggestionActive) {
            console.log("Invalidating change detected, hiding suggestion popup.");
            this.hideSuggestion(); // Hide the popup and reset state
        }

        if (incrementCounter) {
            this.textChangeCounter++;
        }

        // Track changes for history (call original logic)
      this.trackEditorChanges(delta, oldDelta, source);
      
        // Reset debounce timer ONLY if the suggestion was hidden (or wasn't active)
        if (shouldHideSuggestion) { 
            // --- Debounce for Autocomplete --- 
        clearTimeout(this.debounceTimeout);
        this.debounceTimeout = setTimeout(() => {
                // Check suggestionActive again, as it might have been hidden by this handler
          if (!this.suggestionActive) {
                    // Use the *new* popup display function
            this.generateAutocompleteSuggestion();
          }
        }, EnhancedTextGeneratorDocs.CONFIG.TYPING_DEBOUNCE);
        }
        
        // --- Debounce for Autosave --- 
        clearTimeout(this.autosaveTimeout);
        this.updateSaveStatus('Saving...');
        this.autosaveTimeout = setTimeout(() => {
          this.autosaveCurrentDocument();
        }, EnhancedTextGeneratorDocs.CONFIG.AUTOSAVE_INTERVAL || 60000); // Add default
    });
  }
  
  //------------------------------------------------------
  // UI Enhancement Methods
  //------------------------------------------------------
  
  /**
   * Add a toggle button for wide mode
   */
  addWideModeToggle() {
    try {
      const actionsContainer = document.querySelector('.tgdocs-actions');
      // Check if the container exists and if the button hasn't already been added
      if (!actionsContainer || actionsContainer.querySelector('.tgdocs-wide-mode-toggle')) {
          return;
      }
      
      const wideModeButton = document.createElement('button');
      wideModeButton.className = 'mdl-button mdl-js-button mdl-button--icon tgdocs-wide-mode-toggle';
      wideModeButton.innerHTML = `<i class="material-icons">${this.isWideMode ? 'fullscreen_exit' : 'fullscreen'}</i>`;
      wideModeButton.setAttribute('title', this.isWideMode ? 'Exit Wide Mode' : 'Enter Wide Mode');
      
      wideModeButton.addEventListener('click', () => {
        this.toggleWideMode();
      });
      
      actionsContainer.appendChild(wideModeButton);
    } catch (error) {
      console.error('Error adding wide mode toggle:', error);
    }
  }
  
  /**
   * Toggle between wide mode and normal mode
   */
  toggleWideMode() {
    this.isWideMode = !this.isWideMode;
    localStorage.setItem(EnhancedTextGeneratorDocs.CONFIG.WIDE_MODE_STORAGE_KEY, this.isWideMode);
    
    const button = document.querySelector('.tgdocs-wide-mode-toggle i');
    if (button) {
      button.textContent = this.isWideMode ? 'fullscreen_exit' : 'fullscreen';
    }
    
    if (this.isWideMode) {
      this.enableWideMode();
    } else {
      this.disableWideMode();
    }
  }
  
  /**
   * Enable wide mode layout
   */
  enableWideMode() {
    try {
      const container = document.querySelector('.tgdocs-container');
      if (container) {
        container.classList.add('wide-mode');
      }
      
      const sidebar = document.querySelector('.tgdocs-sidebar');
      if (sidebar) {
        sidebar.classList.add('collapsed');
      }
    } catch (error) {
      console.error('Error enabling wide mode:', error);
    }
  }
  
  /**
   * Disable wide mode layout
   */
  disableWideMode() {
    try {
      const container = document.querySelector('.tgdocs-container');
      if (container) {
        container.classList.remove('wide-mode');
      }
      
      const sidebar = document.querySelector('.tgdocs-sidebar');
      if (sidebar) {
        sidebar.classList.remove('collapsed');
      }
    } catch (error) {
      console.error('Error disabling wide mode:', error);
    }
  }
  
  //------------------------------------------------------
  // Typing History Tracking
  //------------------------------------------------------
  
  /**
   * Track editor changes for history and suggestion purposes
   * @param {Object} delta - The change delta
   * @param {Object} oldDelta - The previous state
   * @param {string} source - Source of the change ('user' or 'api')
   */
  trackEditorChanges(delta, oldDelta, source) {
    // Only process user inputs (not programmatic changes)
    if (source !== 'user' || !delta.ops || !this.editor) return;
    
    try {
      // Record the timestamp of this typing activity
      this.lastTypingTimestamp = Date.now();
      
      // Clean up any stale pending requests
      this.cleanupStalePendingRequests();
      
      for (const op of delta.ops) {
        // Track insertions for suggestion cache
        if (op.insert && typeof op.insert === 'string') {
          this.trackInsertion(op.insert);
        }
        
        // Track deletions for potential reuse
        if (op.delete) {
          this.trackDeletion(op.delete, oldDelta);
        }
      }
    } catch (error) {
      console.error('Error tracking editor changes:', error);
    }
  }
  
  /**
   * Track text insertion for typing history
   * @param {string} text - The inserted text
   */
  trackInsertion(text) {
    // Add to typing history
    this.typingHistory.push(text);
    
    // Trim history if too long
    if (this.typingHistory.length > EnhancedTextGeneratorDocs.CONFIG.MAX_HISTORY_LENGTH) {
      this.typingHistory.shift();
    }
  }
  
  /**
   * Track text deletion for future suggestion reuse
   * @param {number} deleteCount - Number of characters deleted
   * @param {Object} oldDelta - Previous editor state
   */
  trackDeletion(deleteCount, oldDelta) {
    try {
      // Extract the text content from old delta
      const contents = oldDelta.ops.reduce((text, op) => {
        if (typeof op.insert === 'string') {
          return text + op.insert;
        }
        return text;
      }, '');
      
      // Store the deleted text if it's substantial
      if (contents.length > 3) {
        const hash = this.hashString(contents);
        this.deletedText[hash] = {
          text: contents,
          timestamp: Date.now()
        };
        
        // Clean up old deletions
        this.cleanupDeletedText();
      }
    } catch (error) {
      console.error('Error tracking deletion:', error);
    }
  }
  
  /**
   * Clean up old deleted text entries
   */
  cleanupDeletedText() {
    const now = Date.now();
    
    Object.keys(this.deletedText).forEach(key => {
      if (now - this.deletedText[key].timestamp > EnhancedTextGeneratorDocs.CONFIG.DELETED_TEXT_EXPIRY) {
        delete this.deletedText[key];
      }
    });
  }
  
  /**
   * Clean up stale pending requests
   */
  cleanupStalePendingRequests() {
    const now = Date.now();
    const maxAge = EnhancedTextGeneratorDocs.CONFIG.REQUEST_TIMEOUT;
    
    Object.keys(this.pendingSuggestionRequests).forEach(key => {
      // If request is older than maxAge, remove it
      if (now - this.pendingSuggestionRequests[key].timestamp > maxAge) {
        console.log(`Cleaning up stale request ${key}`);
        delete this.pendingSuggestionRequests[key];
      }
    });
  }
  
  //------------------------------------------------------
  // Enhanced Autocomplete Methods
  //------------------------------------------------------
  
  /**
   * Override the generateAutocompleteSuggestion method to use typing history
   * @override
   */
  async generateAutocompleteSuggestion() {
    // Check if AI features are disabled due to subscription
    if (this.aiDisabled) {
      return;
    }
    
    // If editor is not initialized or not focused, don't proceed
    if (!this.editor || !this.editor.hasFocus()) return;
    
    // Don't generate if a suggestion is already active
    if (this.suggestionActive) return;
    
    try {
      // Get the current text and cursor position
      const text = this.editor.getText();
      const selection = this.editor.getSelection();
      if (!selection) return;
      
      const cursorPosition = selection.index;
      let textBeforeCursor = text.substring(0, cursorPosition);
      
      // If the text before cursor is too short, don't suggest
      if (textBeforeCursor.trim().length < EnhancedTextGeneratorDocs.CONFIG.MIN_SUGGESTION_LENGTH) return;
      
      // Check if user is actively typing by looking at recent history
      const isActivelyTyping = this.isUserActivelyTyping();
      if (isActivelyTyping) {
        return;
      }
      
      // Generate a unique ID for this request to track it
      const requestId = ++this.lastRequestId;
      
      // Capture the current state when making the request
      const changeCounterAtRequest = this.textChangeCounter;
      // dont need that much context for autocomplete
      if (textBeforeCursor.length > 512) {
        textBeforeCursor = textBeforeCursor.slice(-512);
      }
      // Store the current context for this request
      this.pendingSuggestionRequests[requestId] = {
        prefix: textBeforeCursor,
        cursorPosition: cursorPosition,
        timestamp: Date.now(),
        changeCounter: changeCounterAtRequest
      };
      
      // Get suggestion from cache first (fast path)
      const cachedSuggestion = this.getFromCompletionCache(textBeforeCursor);
      if (cachedSuggestion && !this.suggestionActive) {
        console.log("Using cached suggestion for:", textBeforeCursor);
        this.showAutocompletePopup(cachedSuggestion, cursorPosition);
        delete this.pendingSuggestionRequests[requestId];
        return;
      }
      
      // // Try getting from deleted text next (also fast) - Feature to be implemented
      // const deletedSuggestion = this.getFromDeletedText(textBeforeCursor);
      // if (deletedSuggestion && !this.suggestionActive) {
      //   console.log("Using previously deleted text for suggestion");
      //   this.addToCompletionCache(textBeforeCursor, deletedSuggestion);
      //   this.showInlineSuggestion(deletedSuggestion, cursorPosition);
      //   delete this.pendingSuggestionRequests[requestId];
      //   return;
      // }
      
      // Try getting from typing history
      const historyMatch = this.findPatternInTypingHistory(textBeforeCursor);
      if (historyMatch && !this.suggestionActive) {
        console.log("Using typing history pattern for suggestion");
        // Add to completion cache for future use with the EXACT prefix
        this.addToCompletionCache(textBeforeCursor, historyMatch);
        this.showAutocompletePopup(historyMatch, cursorPosition);
        delete this.pendingSuggestionRequests[requestId];
        return;
      }
      
      // If no local suggestions found, try API with request tracking
      this.fetchAPICompletionWithTracking(textBeforeCursor, requestId);
    } catch (error) {
      console.error('Error generating autocomplete suggestion:', error);
    }
  }
  
  /**
   * Fetch completion from API with careful request tracking
   * @param {string} prefix - Text prefix to complete
   * @param {number} requestId - Request ID for tracking
   */
  async fetchAPICompletionWithTracking(prefix, requestId) {
    // Make sure request still exists (hasn't been cancelled)
    if (!this.pendingSuggestionRequests[requestId]) {
      console.log(`Request ${requestId} was cancelled before API call`);
      return;
    }
    
    console.log(`Generating suggestion from API for request ${requestId}:`, prefix);
    
    try {
      // Always ensure correct min_probability for autocomplete
      const settingsForAutocomplete = { 
        ...this.generationSettings, 
        min_probability: EnhancedTextGeneratorDocs.CONFIG.AUTOCOMPLETE_MIN_PROB 
      };
      
      // Capture the change counter when the API request is initiated
      const changeCounterBeforeCall = this.textChangeCounter;
      
      // Use the correct API endpoint with the secret key in header
      // Determine the correct API endpoint based on hostname
      const isLocal = window.location.hostname.includes('localhost') || 
                     window.location.hostname.includes('127.0.0.1') || 
                     window.location.hostname.includes('0.0.0.0');
      const generateEndpoint = isLocal ? 
          '/api/v1/generate' : 
          'https://text-generator.io/api/v1/generate'; 

      const response = await fetch(generateEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'secret': this.secret
        },
        body: JSON.stringify({
          ...settingsForAutocomplete,
          text: prefix
        })
      });
      
      // Check if the request is still valid after API call returns
      if (!this.isSpecificRequestValid(requestId, changeCounterBeforeCall)) {
        console.log(`Discarding API response for request ${requestId} - context changed`);
        return;
      }
      
      if (!response.ok) {
        console.error(`API error: ${response.status} ${response.statusText}`);
        delete this.pendingSuggestionRequests[requestId]; // Clean up failed request
        return;
      }
      
      const data = await response.json();
      
      // Check again if request is still valid after parsing JSON
      if (!this.isSpecificRequestValid(requestId, changeCounterBeforeCall)) {
        console.log(`Discarding parsed API response for request ${requestId} - context changed`);
        delete this.pendingSuggestionRequests[requestId]; // Clean up invalidated request
        return;
      }
      
      // If no data or empty array, return null
      if (!data || !Array.isArray(data) || data.length === 0) {
         delete this.pendingSuggestionRequests[requestId]; // Clean up empty response request
        return;
      }
      
      // Extract the suggestion from the generated text
      // Return only the part after the prompt
      let suggestion = data[0].generated_text.substring(prefix.length);
      
      // --- Filter Suggestion --- 
      // Check if suggestion is valid (length > 1, not just whitespace) and none is active
      const isValidSuggestion = suggestion && suggestion.trim().length > 1;
      
      if (isValidSuggestion && !this.suggestionActive) {
        // Get the original request data
        const requestData = this.pendingSuggestionRequests[requestId];
        
        // Only store in cache with the EXACT prefix that initiated the request
        this.addToCompletionCache(prefix, suggestion);
        
        // Show the suggestion if the request is still valid
        if (this.isSpecificRequestValid(requestId, changeCounterBeforeCall)) {
          this.showAutocompletePopup(suggestion, requestData.cursorPosition);
        } else {
          console.log(`Not showing suggestion for request ${requestId} - context changed`);
        }
      } else if (!isValidSuggestion) {
          console.log("Suggestion filtered (empty, length 1, or whitespace):", suggestion); // Log filtering
      } else { 
          // Suggestion was valid but one was already active, or some other edge case
          console.log("Suggestion not shown (already active?):", suggestion);
      }
      
      // Clean up this request
      delete this.pendingSuggestionRequests[requestId];
    } catch (error) {
      console.error(`Error fetching API completion for request ${requestId}:`, error);
      delete this.pendingSuggestionRequests[requestId];
    }
  }
  
  /**
   * Check if a specific request is still valid based on its ID and the change counter
   * @param {number} requestId - The ID of the request
   * @param {number} changeCounter - The change counter value to compare against
   * @returns {boolean} Whether the request is still valid
   */
  isSpecificRequestValid(requestId, changeCounter) {
    // Get the request data
    const request = this.pendingSuggestionRequests[requestId];
    if (!request) return false;
    
    // If there have been text changes since the request was initiated, it's invalid
    if (this.textChangeCounter !== changeCounter) {
      console.log(`Request ${requestId} invalid - text changed (counter: ${changeCounter} vs ${this.textChangeCounter})`);
      return false;
    }
    
    // Get current cursor position
    const selection = this.editor ? this.editor.getSelection() : null;
    if (!selection) return false;
    
    const currentCursorPosition = selection.index;
    
    // Check if cursor position is close enough to original position
    const cursorMovement = Math.abs(currentCursorPosition - request.cursorPosition);
    const CURSOR_TOLERANCE = 3; // Allow small cursor movements
    
    // If cursor moved by more than the tolerance, request is invalid
    if (cursorMovement > CURSOR_TOLERANCE) {
      console.log(`Request ${requestId} invalid - cursor moved ${cursorMovement} characters`);
      return false;
    }
    
    return true;
  }
  
  /**
   * Check if the user is actively typing based on recent typing history
   * @returns {boolean} Whether the user is actively typing
   */
  isUserActivelyTyping() {
    const recentTypingThreshold = 500; // ms
    const now = Date.now();
    
    // Check if there was typing in the last 500ms
    if (this.lastTypingTimestamp && now - this.lastTypingTimestamp < recentTypingThreshold) {
      return true;
    }
    
    return false;
  }
  
  /**
   * Find patterns in typing history that match the current context
   * @param {string} prefix - The text prefix to match
   * @returns {string|null} Matching continuation or null if none found
   */
  findPatternInTypingHistory(prefix) {
    // Get the last few characters as our matching pattern
    const pattern = prefix.slice(-EnhancedTextGeneratorDocs.CONFIG.PATTERN_MATCH_LENGTH);
    if (pattern.length < 3) return null;
    
    try {
      // Join typing history to search for the pattern
      const history = this.typingHistory.join('');
      
      // Look for the pattern in our typing history
      const matches = [];
      let startPos = 0;
      let pos;
      
      // Find all occurrences of the pattern
      while ((pos = history.indexOf(pattern, startPos)) !== -1) {
        // Look at what comes after the pattern
        const endPos = Math.min(pos + pattern.length + 30, history.length);
        if (pos + pattern.length < endPos) {
          matches.push(history.substring(pos + pattern.length, endPos));
        }
        startPos = pos + 1;
      }
      
      // Return the most recent match if we found any
      if (matches.length > 0) {
        return matches[matches.length - 1];
      }
    } catch (error) {
      console.error('Error finding pattern in typing history:', error);
    }
    
    return null;
  }
  
  //------------------------------------------------------
  // API and Text Generation Methods
  //------------------------------------------------------
  
  /**
   * Override fetchSuggestion to ensure min_probability is set correctly
   * @override
   * @param {string} prompt - The text to generate a continuation for
   * @param {Object} customSettings - Optional custom generation settings
   * @returns {string|null} Generated text or null on failure
   */
  async fetchSuggestion(prompt, customSettings = null) {
    // Use custom settings or default to generationSettings with min_probability=0.7
    const settings = customSettings || {
      ...this.generationSettings,
      min_probability: EnhancedTextGeneratorDocs.CONFIG.AUTOCOMPLETE_MIN_PROB
    };
    
    // Set the text parameter
    settings.text = prompt;
    
    try {
      // Use the correct API endpoint with the secret key in header
      const isLocal = window.location.hostname.includes('localhost') || 
                     window.location.hostname.includes('127.0.0.1') || 
                     window.location.hostname.includes('0.0.0.0');
      const apiEndpoint = isLocal ? '/api/v1/generate' : 'https://text-generator.io/api/v1/generate';
      const response = await fetch(apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'secret': this.secret
        },
        body: JSON.stringify(settings)
      });
      
      if (!response.ok) {
        console.error(`API error: ${response.status} ${response.statusText}`);
        return null;
      }
      
      const data = await response.json();
      
      // If no data or empty array, return null
      if (!data || !Array.isArray(data) || data.length === 0) {
        return null;
      }
      
      // Extract the suggestion from the generated text
      // Return only the part after the prompt
      const generatedText = data[0].generated_text;
      return generatedText.substring(prompt.length);
    } catch (error) {
      console.error('Error fetching suggestion:', error);
      return null;
    }
  }
  
  /**
   * Override insertLLMResponse to ensure min_probability is set correctly for each generation type
   * @override
   * @param {string} prompt - The text to generate from
   * @param {boolean} isBulkGeneration - Whether this is a bulk generation
   */
  async insertLLMResponse(prompt, isBulkGeneration = false) {
    if (!prompt || prompt.trim() === '') return;
    
    // Show loading indicator
    this.updateSaveStatus('Generating content...');
    
    // Save current cursor position
    const savedSelection = this.editor ? this.editor.getSelection() : null;
    
    try {
      // Determine if we should use Claude for this generation
      const useClaudeForThisRequest = isBulkGeneration && this.useClaudeForBulk;
      
      let generatedText = '';
      
      if (useClaudeForThisRequest) {
        // Use Claude API for bulk generation
        this.updateSaveStatus('Using Claude for high-quality generation...');
        
        // Determine the correct API endpoint based on hostname
        const isLocal = window.location.hostname.includes('localhost') || 
                     window.location.hostname.includes('127.0.0.1') || 
                     window.location.hostname.includes('0.0.0.0');
        const largeGenerateEndpoint = isLocal ? 
            '/api/v1/generate-large' : 
            'https://text-generator.io/api/v1/generate-large';
        
        // Generate content using the Claude API endpoint
        const response = await fetch(largeGenerateEndpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'secret': this.secret
          },
          body: JSON.stringify({
            text: prompt,
            number_of_results: 1,
            max_length: EnhancedTextGeneratorDocs.CONFIG.CLAUDE_MAX_TOKENS,
            max_sentences: 20,
            min_probability: 0,
            stop_sequences: [],
            top_p: 0.9,
            top_k: 40,
            temperature: EnhancedTextGeneratorDocs.CONFIG.CLAUDE_TEMPERATURE,
            repetition_penalty: 1.17,
            seed: 0,
            model: EnhancedTextGeneratorDocs.CONFIG.CLAUDE_MODEL
          })
        });
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error(`Claude API Error (${response.status}): ${errorText}`);
          this.updateSaveStatus(`Generation failed: ${response.status} error`);
          return;
        }
        
        const data = await response.json();
        
        // If no data or empty array, return null
        if (!data || !Array.isArray(data) || data.length === 0) {
          console.warn('Empty or invalid response from Claude API');
          this.updateSaveStatus('Generation received empty response');
          return;
        }
        
        // Process the response - extract the generated text that comes after the prompt
        generatedText = data[0].generated_text.substring(prompt.length);
      } else {
        // Generate content using the standard API with adjusted settings
        const generationSettings = {...this.generationSettings};
        
        if (isBulkGeneration) {
          // For bulk generation, use appropriate settings
          generationSettings.min_probability = EnhancedTextGeneratorDocs.CONFIG.BULK_GEN_MIN_PROB;
          generationSettings.max_length = 1000;
          generationSettings.max_sentences = 20;
          generationSettings.temperature = 0.8;
        } else {
          // For autocomplete, use appropriate settings
          generationSettings.min_probability = EnhancedTextGeneratorDocs.CONFIG.AUTOCOMPLETE_MIN_PROB;
        }
        
        // Use the correct API endpoint with the secret key in header
        const response = await fetch('/api/v1/generate', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'secret': this.secret
          },
          body: JSON.stringify({
            ...generationSettings,
            text: prompt
          })
        });
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error(`API Error (${response.status}): ${errorText}`);
          this.updateSaveStatus(`Generation failed: ${response.status} error`);
          return;
        }
        
        const data = await response.json();
        
        // If no data or empty array, return null
        if (!data || !Array.isArray(data) || data.length === 0) {
          console.warn('Empty or invalid response from API');
          this.updateSaveStatus('Generation received empty response');
          return;
        }
        
        // Process the response correctly - extract the generated text that comes after the prompt
        generatedText = data[0].generated_text.substring(prompt.length);
      }
      
      if (generatedText && generatedText.trim() !== '') {
        await this.insertGeneratedContent(generatedText, savedSelection);
      } else {
        this.updateSaveStatus('Generated empty content');
      }
    } catch (error) {
      console.error('Error generating content:', error);
      this.updateSaveStatus('Generation failed');
    }
  }
  
  /**
   * Insert generated content into the editor
   * @param {string} generatedText - The text to insert
   * @param {Object} savedSelection - The saved cursor position
   */
  async insertGeneratedContent(generatedText, savedSelection) {
    if (!this.editor) return;
    
    try {
      // Make sure cursor position is still valid
      if (savedSelection) {
        // Restore cursor position
        this.editor.setSelection(savedSelection);
      }
      
      // Check if the response contains markdown
      const containsMarkdown = /(\#{1,6}\s+.+)|(\*\*.*?\*\*)|(\*[^\*]+?\*)|(\`[^\`]+?\`)|(\[[^\]]+?\]\([^\)]+?\))|(\>\s+.*?)|(^\s*[\*\-+]\s+.*?)|(^\s*\d+\.\s+.*?)|(\`\`\`[\s\S]*?\`\`\`)/m.test(generatedText);
      
      if (containsMarkdown) {
        // Insert as markdown
        this.insertMarkdown(generatedText);
        
        // Restore focus to editor
        if (this.editor) {
          this.editor.focus();
        }
      } else {
        // Insert as plain text
        this.insertPlainText(generatedText, savedSelection);
      }
      
      // Update save status and autosave
      this.updateSaveStatus('Content inserted');
      this.autosaveCurrentDocument();
    } catch (error) {
      console.error('Error inserting generated content:', error);
      this.updateSaveStatus('Error inserting content');
    }
  }
  
  /**
   * Insert plain text at cursor position
   * @param {string} text - The text to insert
   * @param {Object} savedSelection - The saved cursor position
   */
  insertPlainText(text, savedSelection) {
    if (!this.editor) return;
    
    try {
      // Get current selection
      const currentSelection = this.editor.getSelection() || savedSelection;
      
      if (currentSelection) {
        // Insert at the cursor position
        this.editor.insertText(currentSelection.index, text);
        
        // Set the cursor to the end of the inserted text
        this.editor.setSelection(currentSelection.index + text.length, 0);
      } else {
        // Fallback to appending at the end
        this.editor.insertText(this.editor.getLength() - 1, text);
      }
    } catch (error) {
      console.error('Error inserting plain text:', error);
    }
  }
  
  /**
   * Hides the autocomplete popup and resets the suggestion state.
   */
  hideSuggestion() {
    // console.log("Hiding suggestion popup"); // Optional: Keep for debugging
    
    if (this.suggestionElement) {
      this.suggestionElement.style.display = 'none';
        this.suggestionElement.innerHTML = ''; // Clear content
    }
    // Reset internal state
    this.suggestionActive = false;
    this.suggestionText = '';
    this.suggestionPosition = null;
  }
  
  /**
   * Shows the autocomplete suggestion in a popup below the cursor.
   */
  showAutocompletePopup(suggestion, position) {
    // Ensure editor exists and none is already active
    if (!this.editor || this.suggestionActive) return;
    
    // --- Ensure suggestionElement exists (with fallback query) --- 
    if (!this.suggestionElement) {
        console.warn('this.suggestionElement is invalid, attempting fallback query...');
        this.suggestionElement = document.getElementById('autocomplete-suggestion');
        if (!this.suggestionElement) {
            console.error('Fallback query failed: Autocomplete popup element (#autocomplete-suggestion) not found in the DOM.');
        return;
      }
    }

    console.log(`Attempting to show popup suggestion: "${suggestion}" at position ${position}`);

    // Use editor root directly for styling and positioning

    try {
      // Hide any previous popup first
      this.hideSuggestion();
      
      // Mark suggestion as active internally
      this.suggestionActive = true;
      this.suggestionText = suggestion; 
      this.suggestionPosition = position; 

      // Extract the current partial word for visual continuity
      let partialWord = '';
      try {
      const text = this.editor.getText();
        const beforeCursor = text.substring(0, position);
        // More lenient regex that catches any sequence of word chars at end
        const wordRegex = /(\w+)$/;
        const match = beforeCursor.match(wordRegex);
        
        if (match && match[1]) {
          partialWord = match[1];
          console.log(`Detected partial word: "${partialWord}"`);
        }
      } catch (error) {
        console.warn('Error extracting partial word:', error);
      }

      // --- Calculate position --- 
      const bounds = this.editor.getBounds(position); 
      if (!bounds || typeof bounds.left !== 'number' || typeof bounds.top !== 'number') { // Check top now
          console.warn('Could not get valid bounds for suggestion position:', bounds);
      this.hideSuggestion();
        return;
      }
      console.log('Cursor bounds:', bounds);

      // Update popup content, incorporating partial word if appropriate
      if (partialWord && suggestion.toLowerCase().startsWith(partialWord.toLowerCase())) {
        // Split the suggestion: showing typed part + remaining part
        const remainingText = suggestion.substring(partialWord.length);
        this.suggestionElement.innerHTML = `
          <span class="suggestion-partial">${partialWord}</span><span class="suggestion-text">${remainingText}</span><span class="suggestion-hint"><kbd>&#x21E5;</kbd></span>
        `.trim();
      } else {
        // Just show the suggestion as normal
        this.suggestionElement.innerHTML = `<span class="suggestion-text">${suggestion}</span><span class="suggestion-hint"><kbd>&#x21E5;</kbd></span>`;
      }
      
      // Add better visibility styles directly to the element
      this.suggestionElement.style.backgroundColor = '#ffffff';
      this.suggestionElement.style.border = '1px solid #dddddd';
      this.suggestionElement.style.borderRadius = '4px';
      this.suggestionElement.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)';
      this.suggestionElement.style.padding = '2px 4px';
      this.suggestionElement.style.zIndex = '9999';
      this.suggestionElement.style.display = 'block';
      this.suggestionElement.style.opacity = '1';
      this.suggestionElement.style.whiteSpace = 'nowrap';
      this.suggestionElement.style.maxWidth = '400px';
      this.suggestionElement.style.overflow = 'hidden';
      this.suggestionElement.style.textOverflow = 'ellipsis';
      this.suggestionElement.style.lineHeight = '1';
      this.suggestionElement.style.display = 'inline-flex';
      this.suggestionElement.style.alignItems = 'center';

      // --- Apply editor font styles and get line height --- 
      let editorLineHeight = '1.42'; // Default fallback line height
      try {
        const styleSource = this.editor.root.querySelector('p') || this.editor.root;
        const computedStyle = window.getComputedStyle(styleSource);
        console.log('Applying font styles from:', styleSource, 'Style:', computedStyle.fontFamily, computedStyle.fontSize, computedStyle.lineHeight);
        
        this.suggestionElement.style.fontSize = computedStyle.fontSize;
        this.suggestionElement.style.fontFamily = computedStyle.fontFamily;
        this.suggestionElement.style.fontWeight = computedStyle.fontWeight;
        this.suggestionElement.style.fontStyle = computedStyle.fontStyle;
        this.suggestionElement.style.color = '#555';
        
        const textSpan = this.suggestionElement.querySelector('.suggestion-text');
        if(textSpan) {
          textSpan.style.opacity = '0.65';
          textSpan.style.display = 'inline';
          textSpan.style.margin = '0';
          textSpan.style.padding = '0';
        }
        
        // Style the partial word to match the editor text
        const partialSpan = this.suggestionElement.querySelector('.suggestion-partial');
        if(partialSpan) {
          partialSpan.style.display = 'inline';
          partialSpan.style.margin = '0';
          partialSpan.style.padding = '0';
          partialSpan.style.opacity = '1';
          partialSpan.style.color = 'black';
          partialSpan.style.fontWeight = 'inherit';
        }
        
        const hintSpan = this.suggestionElement.querySelector('.suggestion-hint');
        if(hintSpan) {
          hintSpan.style.display = 'inline-flex';
          hintSpan.style.marginLeft = '2px';
          hintSpan.style.fontSize = '0.8em';
          hintSpan.style.opacity = '0.8';
        }

        // Store line height for positioning
        if (computedStyle.lineHeight && computedStyle.lineHeight !== 'normal') {
            editorLineHeight = computedStyle.lineHeight;
        }
        
      } catch (styleError) {
        console.warn("Could not apply editor styles to suggestion popup:", styleError);
      }

      // --- Position the popup using getBounds.bottom ---
      const editorRect = this.editor.root.getBoundingClientRect();
      const viewportTop = editorRect.top + bounds.top + bounds.height;
      
      // Adjust left position - subtract width of partial word if present
      let partialWordWidth = 0;
      const partialSpan = this.suggestionElement.querySelector('.suggestion-partial');
      if (partialSpan) {
        // Create an invisible measuring element to calculate exact width
        const measurer = document.createElement('span');
        measurer.style.visibility = 'hidden';
        measurer.style.position = 'absolute';
        measurer.style.fontSize = this.suggestionElement.style.fontSize;
        measurer.style.fontFamily = this.suggestionElement.style.fontFamily;
        measurer.style.fontWeight = this.suggestionElement.style.fontWeight;
        measurer.style.whiteSpace = 'pre';
        measurer.textContent = partialWord;
        document.body.appendChild(measurer);
        partialWordWidth = measurer.getBoundingClientRect().width;
        document.body.removeChild(measurer);
        console.log(`Partial word "${partialWord}" width: ${partialWordWidth}px`);
      }
      
      const alignmentOffset = 105; // Base offset for alignment
      const viewportLeft = editorRect.left + bounds.left - alignmentOffset - partialWordWidth;

      // Use absolute positioning relative to document by translating based on scroll offset
      const scrollX = window.scrollX || window.pageXOffset;
      const scrollY = window.scrollY || window.pageYOffset;

      // Switch to fixed positioning to avoid scroll issues - more reliable
      this.suggestionElement.style.position = 'fixed';
      this.suggestionElement.style.top = `${viewportTop}px`;
      this.suggestionElement.style.left = `${viewportLeft}px`;
      this.suggestionElement.style.margin = '0';

      console.log('Suggestion popup displayed.');

    } catch (error) {
      console.error('Error showing suggestion popup:', error);
      this.hideSuggestion(); 
    }
  }
  
  /**
   * Get the DOM node at a given position in the editor
   * @param {Element} root - The editor root element
   * @param {number} position - The position to find
   * @returns {Node|null} The node at the position or null
   */
  getNodeAtPosition(root, position) {
    const treeWalker = document.createTreeWalker(
      root,
      NodeFilter.SHOW_TEXT,
      null,
      false
    );
    
    let currentNode = treeWalker.currentNode;
    let currentPosition = 0;
    
    while (currentNode) {
      const nodeLength = currentNode.length || 0;
      
      if (currentPosition + nodeLength >= position) {
        return currentNode;
      }
      
      currentPosition += nodeLength;
      currentNode = treeWalker.nextNode();
    }
    
    return null;
  }
  
  /**
   * Override handleKeyDown to provide a more robust tab completion and additional keyboard shortcuts
   * @override
   */
  handleKeyDown(event) {
    // Handle keyboard shortcuts for content generation
    // Ctrl+G or Cmd+G to trigger Rewrite Document dialog
    if ((event.ctrlKey || event.metaKey) && event.key === 'g') {
      event.preventDefault();
      this.showGenerateContentDialog(); // This now shows the Rewrite dialog
      return;
    }
    
    // Alt+Enter or Option+Enter to trigger Autowrite from cursor
    if (event.altKey && event.key === 'Enter') { 
      event.preventDefault();
      event.stopPropagation();
      // Cancel any active suggestion first
      if (this.suggestionActive) {
        this.hideSuggestion();
      }
      this.autoWriteFromCursor();
      return;
    }

    // Ctrl+S or Cmd+S to save document
    if ((event.ctrlKey || event.metaKey) && event.key === 's') {
      event.preventDefault();
      this.saveCurrentDocument();
      return;
    }

    // Ctrl+E or Cmd+E to export document
    if ((event.ctrlKey || event.metaKey) && event.key === 'e') {
      event.preventDefault();
      this.exportCurrentDocument();
      return;
    }

    // If Tab is pressed and we have an active suggestion
    if (event.key === 'Tab' && this.suggestionActive) {
      event.preventDefault();
      event.stopPropagation(); // Stop propagation to prevent focus change
      
      // If suggestion popup is active, accept it directly
      console.log('Accepting suggestion via Tab key (popup)');
      this.acceptSuggestion();
      
      return false; // Ensure the event is completely stopped
    }
    
    // If escape is pressed and we have an active suggestion, hide it
    if (event.key === 'Escape' && this.suggestionActive) {
      event.preventDefault();
      this.hideSuggestion();
      return;
    }
    
    // If arrow keys are pressed and we have an active suggestion, hide it
    if (this.suggestionActive && (event.key === 'ArrowLeft' || event.key === 'ArrowRight' || 
        event.key === 'ArrowUp' || event.key === 'ArrowDown')) {
      this.hideSuggestion();
      // But allow the event to propagate for normal cursor movement
    }
    
    // For all other keys, call parent method
    super.handleKeyDown(event);
  }

  /**
   * Override showGenerateContentDialog to properly handle Write from Cursor functionality
   * @override
   */
  showGenerateContentDialog() {
    // Check if AI features are disabled due to subscription
    if (this.aiDisabled) {
      if (window.subscriptionModal) { subscriptionModal.show(); };
      return;
    }
    
    // Create dialog container
    const dialogContainer = document.createElement('div');
    dialogContainer.className = 'tgdocs-generate-dialog';
    
    // Create dialog content
    const dialogContent = document.createElement('div');
    dialogContent.className = 'tgdocs-generate-dialog-content';
    
    // Add title
    const title = document.createElement('h3');
    title.textContent = 'Write from Cursor';
    dialogContent.appendChild(title);
    
    // Add description
    const description = document.createElement('p');
    description.textContent = 'This will generate new text continuing from your current cursor position.';
    dialogContent.appendChild(description);
    
    // Add textarea for prompt - actually not needed for write from cursor
    // as it uses preceding text automatically
    
    // Add actions
    const actions = document.createElement('div');
    actions.className = 'tgdocs-generate-actions';
    
    // Function to close the dialog and remove listeners
    const closeDialog = () => {
      document.removeEventListener('keydown', handleEscapeKey);
      if (dialogContainer.parentNode) {
        document.body.removeChild(dialogContainer);
      }
    };
    
    // Add cancel button
    const cancelButton = document.createElement('button');
    cancelButton.className = 'mdl-button mdl-js-button mdl-button--raised';
    cancelButton.textContent = 'Cancel';
    cancelButton.addEventListener('click', closeDialog);
    actions.appendChild(cancelButton);
    
    // Add autowrite button
    const autowriteButton = document.createElement('button');
    autowriteButton.className = 'mdl-button mdl-js-button mdl-button--raised mdl-button--colored tgdocs-autowrite-btn';
    autowriteButton.textContent = 'Generate';
    autowriteButton.addEventListener('click', async () => {
      // Disable button and show loading state
      autowriteButton.disabled = true;
      // Add spinner element to button
      const originalText = autowriteButton.textContent;
      const spinner = document.createElement('span');
      spinner.className = 'autowrite-spinner';
      spinner.style.display = 'inline-block';
      spinner.style.width = '16px';
      spinner.style.height = '16px';
      spinner.style.border = '2px solid rgba(255,255,255,0.3)';
      spinner.style.borderRadius = '50%';
      spinner.style.borderTopColor = '#fff';
      spinner.style.animation = 'spin 1s linear infinite';
      spinner.style.marginRight = '8px';
      spinner.style.verticalAlign = 'middle';
      
      // Add keyframes animation if it doesn't exist
      if (!document.getElementById('spinner-keyframes')) {
        const style = document.createElement('style');
        style.id = 'spinner-keyframes';
        style.textContent = '@keyframes spin { to { transform: rotate(360deg); } }';
        document.head.appendChild(style);
      }
      
      autowriteButton.textContent = 'Generating...';
      autowriteButton.insertBefore(spinner, autowriteButton.firstChild);
      autowriteButton.style.opacity = '0.8';
      autowriteButton.style.cursor = 'not-allowed';

      closeDialog(); // Close dialog before starting write from cursor
      try {
        // Call the correct function for "Write from Cursor"
        await this.autoWriteFromCursor();
      } finally {
        // Re-enable button regardless of success/failure (dialog is already closed)
      }
    });
    actions.appendChild(autowriteButton);
    
    dialogContent.appendChild(actions);
    dialogContainer.appendChild(dialogContent);
    document.body.appendChild(dialogContainer);

    // Add Escape key listener
    const handleEscapeKey = (event) => {
      if (event.key === 'Escape') {
        closeDialog();
      }
    };
    document.addEventListener('keydown', handleEscapeKey);

    // Add background click listener
    dialogContainer.addEventListener('click', (event) => {
      // Check if the click is directly on the background container
      if (event.target === dialogContainer) {
        closeDialog();
      }
    });
  }

  /**
   * Show dialog to get rewrite instructions from user
   */
  showRewriteDialog() {
    // Check if AI features are disabled due to subscription
    if (this.aiDisabled) {
      if (window.subscriptionModal) { subscriptionModal.show(); };
      return;
    }
    
    // Create dialog for rewrite instructions
    const dialogContainer = document.createElement('div');
    dialogContainer.className = 'tgdocs-generate-dialog'; // Reuse the same dialog styling
    
    // Create dialog content
    const dialogContent = document.createElement('div');
    dialogContent.className = 'tgdocs-generate-dialog-content';
    dialogContent.innerHTML = `
      <h3>Rewrite Content</h3>
      <p>Enter instructions for how you want the content to be rewritten:</p>
      <textarea id="rewrite-instructions" class="tgdocs-generate-prompt" placeholder="E.g., Make it more formal, convert to bullet points, rewrite in a fantasy style..."></textarea>
      <div class="tgdocs-generate-actions">
        <button id="rewrite-cancel" class="mdl-button mdl-js-button">Cancel</button>
        <button id="rewrite-submit" class="mdl-button mdl-js-button mdl-button--raised mdl-button--colored">Rewrite</button>
      </div>
    `;
    
    // Append dialog to body
    document.body.appendChild(dialogContainer);
    dialogContainer.appendChild(dialogContent);
    
    // Helper for closing dialog
    const closeDialog = () => {
      dialogContainer.remove();
      // Remove event listeners
      document.removeEventListener('keydown', handleEscapeKey);
    };
    
    // Add event listeners
    document.getElementById('rewrite-cancel').addEventListener('click', () => {
      closeDialog();
    });
    
    document.getElementById('rewrite-submit').addEventListener('click', () => {
      const instructions = document.getElementById('rewrite-instructions').value.trim();
      if (instructions) {
        // Close dialog first
        closeDialog();
        // Then rewrite with instructions
        this.rewriteDocumentWithInstructions(instructions);
      } else {
        // Show validation message if empty
        alert('Please enter rewrite instructions');
      }
    });
    
    // Handle Escape key to close dialog
    const handleEscapeKey = (event) => {
      if (event.key === 'Escape') {
        closeDialog();
      }
    };
    document.addEventListener('keydown', handleEscapeKey);
    
    // Add background click listener to close
    dialogContainer.addEventListener('click', (event) => {
      // Check if the click is directly on the background container
      if (event.target === dialogContainer) {
        closeDialog();
      }
    });
    
    // Focus on instructions textarea
    setTimeout(() => {
      document.getElementById('rewrite-instructions').focus();
    }, 100);
  }

  /**
   * Rewrites the entire document based on instructions using an LLM.
   * @param {string} instructionPrompt - The instructions for rewriting.
   */
  async rewriteDocumentWithInstructions(instructionPrompt) {
    if (!this.editor) return;

    // Set loading state for the button
    const button = this.rewriteContentButton || document.getElementById('rewrite-content-btn');
    this.setButtonLoadingState(button, true);

    try {
      const fullDocumentText = this.editor.getText();
      // Check if document has meaningful content (not just whitespace/newlines)
      const trimmedText = fullDocumentText.trim();
      if (!trimmedText || trimmedText.length < 3) {
        this.updateSaveStatus('Document is empty or too short to rewrite. Please add some content first.');
        this.setButtonLoadingState(button, false); // Reset loading state
        // Show a user-friendly alert
        alert('Please add some content to the document before trying to rewrite it.');
        return;
      }

      this.updateSaveStatus('Rewriting document...');

      // Determine the API endpoint (always use Claude for rewriting for better quality)
      const isLocal = window.location.hostname.includes('localhost') || 
                     window.location.hostname.includes('127.0.0.1') || 
                     window.location.hostname.includes('0.0.0.0');
      const largeGenerateEndpoint = isLocal ? 
          '/api/v1/generate-large' : 
          'https://text-generator.io/api/v1/generate-large';

      // Construct a system message suitable for rewriting
      const system_message = `You are a world-class creative writer. Transform the following text according to these instructions: "${instructionPrompt}"

Approach the text as a professional writer would, not as an AI assistant. Never address the reader directly. Never use phrases like "I understand" or "Here's". 

OUTPUT RULES:
1. Start writing immediately without any introduction
2. Maintain the same perspective (first/third person) as the original unless instructed otherwise
3. Output ONLY the transformed content - no explanations, no meta-commentary
4. Do not reference yourself or the editing process in any way
5. If the instruction is to create a fantasy intro, write as if for a published fantasy novel
And finally also output the full text again if its used, as we are doing a full rewrite`;

      const response = await fetch(largeGenerateEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'secret': this.secret
        },
        body: JSON.stringify({
          text: fullDocumentText, // Send the full document as the main prompt
          // Use settings suitable for rewriting/editing
          max_length: 4000, // Allow longer responses for full doc rewrite
          max_sentences: 0, // Let the model decide sentence structure
          min_probability: 0, 
        stop_sequences: [],
          top_p: 0.8, // Slightly lower p for more focused rewriting
        top_k: 40,
          temperature: 0.6, // Lower temperature for more controlled editing
          repetition_penalty: 1.1,
          seed: 0,
          model: EnhancedTextGeneratorDocs.CONFIG.CLAUDE_MODEL, // Use the configured Claude model
          system_message: system_message // Pass the system message
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`Rewrite API Error (${response.status}): ${errorText}`);
        this.updateSaveStatus(`Rewrite failed: ${response.status} error`);
        this.setButtonLoadingState(button, false); // Reset loading state
        return;
      }

      const data = await response.json();

      if (!data || !Array.isArray(data) || data.length === 0) {
        console.warn('Empty or invalid response from rewrite API');
        this.updateSaveStatus('Rewrite received empty response');
        this.setButtonLoadingState(button, false); // Reset loading state
        return;
      }

      // The API might return the original prompt + generation, or just the generation.
      // We want *only* the rewritten content.
      // Assuming the structure returns { generated_text: "... rewritten content ..." }
      // Claude might prepend the original text, so we need to be careful.
      // Since the system prompt asks *only* for the rewritten content, we hope it complies.
      let rewrittenText = data[0].generated_text;
      
      // Basic check: If the response starts exactly with the original text, try removing it.
      if (rewrittenText.startsWith(fullDocumentText)) {
        console.log("API included original prefix in rewrite response, removing it.");
        rewrittenText = rewrittenText.substring(fullDocumentText.length).trimStart();
      }

      if (rewrittenText && rewrittenText.trim() !== '') {
        // Replace the entire editor content
        this.editor.setContents([{ insert: rewrittenText + '\n' }]); // Add newline for safety
        this.updateSaveStatus('Document rewritten');
        this.autosaveCurrentDocument();
      } else {
        this.updateSaveStatus('Rewrite resulted in empty content');
      }

    } catch (error) {
      console.error('Error rewriting document:', error);
      this.updateSaveStatus('Rewrite failed');
    } finally {
      // Ensure button loading state is reset
      this.setButtonLoadingState(button, false);
    }
  }

  /**
   * Autowrites text starting from the current cursor position based on preceding content.
   */
  async autoWriteFromCursor() {
    if (!this.editor) return;

    const selection = this.editor.getSelection();
    if (!selection) return;

    // Set loading state for the button
    const button = this.generateContentButton || document.getElementById('generate-content-btn');
    this.setButtonLoadingState(button, true);

    try {
      const cursorPosition = selection.index;
      let textBeforeCursor = this.editor.getText(0, cursorPosition);

      if (!textBeforeCursor || textBeforeCursor.trim() === '') {
        this.updateSaveStatus('Cannot autowrite without preceding text.');
        this.setButtonLoadingState(button, false); // Reset loading state
        return;
      }

      this.updateSaveStatus('Autowriting...');

      // Determine the API endpoint (Claude for better continuation)
      const isLocal = window.location.hostname.includes('localhost') || 
                     window.location.hostname.includes('127.0.0.1') || 
                     window.location.hostname.includes('0.0.0.0');
      const largeGenerateEndpoint = isLocal ? 
          '/api/v1/generate-large' : 
          'https://text-generator.io/api/v1/generate-large';

      // Construct a system message suitable for continuation
      const system_message = `You are a master storyteller and prose stylist. Continue this text naturally as a talented author would. 

KEY RULES:
1. Start writing immediately - no explanations or phrases like "here's a continuation" 
2. Maintain the established tone, tense, and perspective of the original
3. Output only your direct continuation without any meta-commentary
4. Never address the reader or acknowledge your role as an AI
5. If the text suggests a fantasy context, continue in rich, imaginative fantasy prose`;

      const response = await fetch(largeGenerateEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'secret': this.secret
        },
        body: JSON.stringify({
          text: textBeforeCursor, // Send preceding text as prompt
          // Use settings suitable for creative continuation
          max_length: 4000, // Moderate length for continuation
          max_sentences: 0, 
          min_probability: 0,
          stop_sequences: ["\n\n\n"], // Stop after a couple of paragraphs typically
          top_p: 0.9,
          top_k: 50,
          temperature: 0.75, // Balanced temperature for continuation
          repetition_penalty: 1.1,
          seed: 0,
          model: EnhancedTextGeneratorDocs.CONFIG.CLAUDE_MODEL, // Use the configured Claude model
          system_message: system_message 
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`Autowrite API Error (${response.status}): ${errorText}`);
        this.updateSaveStatus(`Autowrite failed: ${response.status} error`);
        this.setButtonLoadingState(button, false); // Reset loading state
        return;
      }

      const data = await response.json();

      if (!data || !Array.isArray(data) || data.length === 0) {
        console.warn('Empty or invalid response from autowrite API');
        this.updateSaveStatus('Autowrite received empty response');
        this.setButtonLoadingState(button, false); // Reset loading state
        return;
      }

      // Extract only the generated continuation
      let continuationText = data[0].generated_text;
      // If the API includes the prompt, remove it
      if (continuationText.startsWith(textBeforeCursor)) {
        console.log("API included original prefix in autowrite response, removing it.");
        continuationText = continuationText.substring(textBeforeCursor.length);
      }
      
      if (continuationText && continuationText.trim() !== '') {
        // Insert the continuation text at the cursor position
        this.editor.insertText(cursorPosition, continuationText);
        // Move cursor to the end of the inserted text
        this.editor.setSelection(cursorPosition + continuationText.length, 0);
        this.updateSaveStatus('Text inserted');
        this.autosaveCurrentDocument();
      } else {
        this.updateSaveStatus('Autowrite resulted in empty content');
      }

    } catch (error) {
      console.error('Error autowriting from cursor:', error);
      this.updateSaveStatus('Autowrite failed');
    } finally {
      // Ensure button loading state is reset 
      this.setButtonLoadingState(button, false);
    }
  }

  /**
   * @override
   */
  acceptSuggestion() {
    // Check if editor and suggestion state are valid
    if (!this.editor || !this.suggestionActive || !this.suggestionText || typeof this.suggestionPosition !== 'number') { 
        this.hideSuggestion(); // Clean up state just in case
        return;
    }

    console.log(`Accepting popup suggestion: "${this.suggestionText}"`);

    try {
      // Determine the correct insertion point with two fallbacks
      const currentSelection = this.editor.getSelection();
      const cursorIndex = currentSelection ? currentSelection.index : 0;
      let insertPosition = this.suggestionPosition;

      // Validate insertion position
      if (typeof insertPosition !== 'number' || insertPosition < 0 || insertPosition > this.editor.getLength()) {
        insertPosition = cursorIndex;
      }

      // Check if we have a partial word display active
      const partialSpan = this.suggestionElement.querySelector('.suggestion-partial');
      const partialWord = partialSpan ? partialSpan.textContent : '';
      
      // Save suggestion text length BEFORE we hide it
      // If we're showing a partial word, only insert the remainder
      let textToInsert = this.suggestionText;
      if (partialWord && this.suggestionText.toLowerCase().startsWith(partialWord.toLowerCase())) {
        textToInsert = this.suggestionText.substring(partialWord.length);
      }
      
      // Insert the suggestion text (either full or just remaining part)
      this.editor.insertText(insertPosition, textToInsert, 'user');
      
      // Add to completion cache using the prefix *before* the suggestion started
      const textBeforeSuggestion = this.editor.getText(0, insertPosition);
      this.addToCompletionCache(textBeforeSuggestion, this.suggestionText);

      // Hide suggestion state
      this.hideSuggestion();

      // Calculate ending position - we try multiple approaches to ensure movement
      const finalPosition = insertPosition + textToInsert.length;

      // APPROACH 1: Direct end position selection (most reliable)
      this.editor.setSelection(finalPosition, 0);
      
      // APPROACH 2: Delayed moveCursorRight as backup plan
      setTimeout(() => {
        // Double-check if cursor still isn't where it should be
        const newSel = this.editor.getSelection();
        if (!newSel || newSel.index !== finalPosition) {
          console.log('Using backup cursor positioning method');
          this.moveCursorRight(textToInsert.length);
        }
        this.editor.focus();
        console.log(`Cursor moved ${textToInsert.length} positions right after suggestion acceptance`);
      }, 50);

      // Auto-save after accepting suggestion
      this.autosaveCurrentDocument();
    } catch (error) {
      console.error('Error accepting suggestion:', error);
      this.hideSuggestion();
    }
  }

  /**
   * Add tooltips for Quill toolbar buttons to show keyboard shortcuts.
   */
  addToolbarTooltips() {
    const toolbar = document.querySelector('.ql-toolbar');
    if (!toolbar) return;
    const tooltips = [
      { selector: 'button.ql-bold', title: 'Bold (Ctrl+B)' },
      { selector: 'button.ql-italic', title: 'Italic (Ctrl+I)' },
      { selector: 'button.ql-underline', title: 'Underline (Ctrl+U)' },
      { selector: 'button.ql-strike', title: 'Strikethrough (Ctrl+Shift+S)' },
      { selector: 'button.ql-blockquote', title: 'Blockquote' },
      { selector: 'button.ql-code-block', title: 'Code Block' },
      { selector: 'button.ql-list[value="ordered"]', title: 'Ordered List (Ctrl+Shift+7)' },
      { selector: 'button.ql-list[value="bullet"]', title: 'Bullet List (Ctrl+Shift+8)' },
      { selector: 'button.ql-link', title: 'Insert Link (Ctrl+K)' },
      { selector: 'button.ql-image', title: 'Insert Image' },
      { selector: 'button.ql-clean', title: 'Remove Formatting' },
      { selector: '.ql-header .ql-picker-label', title: 'Header (Select Heading Level)' }
    ];
    tooltips.forEach(({ selector, title }) => {
      toolbar.querySelectorAll(selector).forEach(el => el.setAttribute('title', title));
    });
  }

  /**
   * Move the editor cursor right by a given number of characters.
   * Useful for manual testing/traversal from console: scene.moveCursorRight(5)
   * @param {number} count - Number of characters to move forward.
   */
  moveCursorRight(count) {
    if (!this.editor) return;
    const sel = this.editor.getSelection();
    const currentIndex = sel ? sel.index : this.editor.getLength();
    const target = currentIndex + (typeof count === 'number' ? count : 0);
    const source = (typeof Quill !== 'undefined' && Quill.sources) ? Quill.sources.USER : undefined;
    try {
      if (source) {
        this.editor.setSelection(target, 0, source);
      } else {
        this.editor.setSelection(target, 0);
      }
      // No refocus here—avoid moving focus which can interfere with caret placement
    } catch (e) {
      console.warn('moveCursorRight failed:', e);
    }
  }

  /**
   * Set loading state for a button
   * @param {HTMLElement} button - The button to set loading state for
   * @param {boolean} isLoading - Whether the button is in loading state
   */
  setButtonLoadingState(button, isLoading) {
    if (!button) return;
    
    const originalContent = button.getAttribute('data-original-content');
    
    if (isLoading) {
      // Save original content if not already saved
      if (!originalContent) {
        button.setAttribute('data-original-content', button.innerHTML);
      }
      
      // Update button appearance
      button.innerHTML = '<i class="material-icons mdl-spinner mdl-spinner--active mdl-spinner--single-color">autorenew</i> Working...';
      button.classList.add('mdl-button--disabled');
      button.disabled = true;
    } else {
      // Restore original content
      if (originalContent) {
        button.innerHTML = originalContent;
      }
      
      // Restore button state
      button.classList.remove('mdl-button--disabled');
      button.disabled = false;
    }
  }
} 