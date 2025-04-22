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
      MIN_SUGGESTION_LENGTH: 15,
      AUTOCOMPLETE_DEBOUNCE_MS: 800,
      AUTOCOMPLETE_MIN_PROB: 0.7,
      BULK_GEN_MIN_PROB: 0,
      TYPING_DEBOUNCE: 800, // Debounce time before triggering autocomplete check (increased back)
      CURSOR_TOLERANCE: 3, // How much cursor can move before invalidating suggestion
      
      // Typing history settings
      MAX_TYPING_HISTORY: 100,
      TYPING_TIMEOUT_MS: 2000,
      
      // Claude API settings
      CLAUDE_MODEL: "claude-3-sonnet-20240229",
      CLAUDE_MAX_TOKENS: 1000,
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
      // Call parent init method
      await super.init();
      
      // Add enhanced UI elements
      this.addWideModeToggle();
      
      // Override default debounce settings
      this.initDebounceSettings();
      
      // Add enhanced event listeners for typing detection
      this.initEnhancedEventListeners();
      
      console.log('Enhanced Text Generator Docs initialized');
    } catch (error) {
      console.error('Error initializing enhanced text generator:', error);
    }
  }
  
  /**
   * Initialize enhanced event listeners
   */
  initEnhancedEventListeners() {
    // Add wide mode toggle
    this.addWideModeToggle();
    
    // Apply wide mode if it was previously enabled
    if (this.isWideMode) {
      this.enableWideMode();
    }
    
    // Add keyboard shortcuts help button
    const helpButton = document.createElement('button');
    helpButton.className = 'mdl-button mdl-js-button mdl-button--icon tgdocs-help-button';
    helpButton.innerHTML = '<i class="material-icons">help</i>';
    helpButton.title = 'Keyboard Shortcuts';
    
    // Add to the actions container
    const actionsContainer = document.querySelector('.tgdocs-actions');
    if (actionsContainer) {
      actionsContainer.appendChild(helpButton);
    }
    
    // Set up keyboard shortcuts dialog
    const keyboardShortcutsDialog = document.getElementById('keyboard-shortcuts-dialog');
    if (keyboardShortcutsDialog) {
      helpButton.addEventListener('click', () => {
        keyboardShortcutsDialog.style.display = 'flex';
      });
      
      const closeButton = keyboardShortcutsDialog.querySelector('#close-shortcuts-btn');
      if (closeButton) {
        closeButton.addEventListener('click', () => {
          keyboardShortcutsDialog.style.display = 'none';
        });
      }
    }
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

        let hideSuggestion = true;
        let incrementCounter = true;
        let updateSuggestionText = null;

        // Analyze the change if a suggestion is active
        if (this.suggestionActive && this.suggestionText && delta.ops) {
            // Check if the change is a simple text insertion
            if (delta.ops.length === 1 && delta.ops[0].insert && typeof delta.ops[0].insert === 'string') {
                const insertedText = delta.ops[0].insert;

                // Case 1: User typed only spaces
                if (/^\s+$/.test(insertedText)) {
                    hideSuggestion = false; // Keep suggestion visible
                    incrementCounter = false; // Don't invalidate pending requests
                }
                // Case 2: User typed text matching the start of the suggestion
                else if (this.suggestionText.startsWith(insertedText)) {
                    updateSuggestionText = this.suggestionText.substring(insertedText.length);
                    hideSuggestion = false; // Keep suggestion visible (it will be updated)
                    incrementCounter = false; // Don't invalidate pending requests
                }
            }
            // Any other change (deletion, complex op, non-matching insert) invalidates
        }

        // --- Apply decisions --- 
        if (hideSuggestion && this.suggestionActive) {
            this.hideSuggestion();
        }

        if (incrementCounter) {
            this.textChangeCounter++;
        }

        // Track changes for history (call original logic)
        this.trackEditorChanges(delta, oldDelta, source);

        // If suggestion needs updating (user typed matching prefix)
        if (updateSuggestionText !== null) {
            this.suggestionText = updateSuggestionText;
            if (this.suggestionText === '') { // If user typed the whole suggestion
                this.hideSuggestion();
            } else {
                // Update the displayed suggestion (needs modification to showInlineSuggestion or similar)
                // For now, let's just remove the old and show the new if possible
                const selection = this.editor.getSelection();
                if(selection) {
                    this.removeInlineSuggestion(); // Remove old visual
                    this.showInlineSuggestion(this.suggestionText, selection.index); // Show updated visual
                }
            }
        } 
        // Don't reset debounce if we are just updating the suggestion or user typed spaces
        else if (hideSuggestion) { 
          // --- Debounce for Autocomplete --- 
          clearTimeout(this.debounceTimeout);
          this.debounceTimeout = setTimeout(() => {
            if (!this.suggestionActive) { // Only generate if none is active
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
      const textBeforeCursor = text.substring(0, cursorPosition);
      
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
        this.showInlineSuggestion(cachedSuggestion, cursorPosition);
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
        this.showInlineSuggestion(historyMatch, cursorPosition);
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
      const isLocal = window.location.hostname.includes('localhost') || window.location.hostname.includes('127.0.0.1');
      const generateEndpoint = isLocal ? 
          'http://localhost:8000/api/v1/generate' : 
          'https://api.text-generator.io/api/v1/generate'; // Use standard generate endpoint

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
      const generatedText = data[0].generated_text;
      const suggestion = generatedText.substring(prefix.length);
      
      // If we got a suggestion and it's not empty
      if (suggestion && suggestion.trim() !== '' && !this.suggestionActive) {
        // Get the original request data
        const requestData = this.pendingSuggestionRequests[requestId];
        
        // Only store in cache with the EXACT prefix that initiated the request
        this.addToCompletionCache(prefix, suggestion);
        
        // Show the suggestion if the request is still valid
        if (this.isSpecificRequestValid(requestId, changeCounterBeforeCall)) {
          this.showInlineSuggestion(suggestion, requestData.cursorPosition);
        } else {
          console.log(`Not showing suggestion for request ${requestId} - context changed`);
        }
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
      const response = await fetch('https://api.text-generator.io/api/v1/generate', {
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
        const isLocal = window.location.hostname.includes('localhost') || window.location.hostname.includes('127.0.0.1');
        const largeGenerateEndpoint = isLocal ? 
            'http://localhost:8000/api/v1/generate-large' : 
            'https://api.text-generator.io/api/v1/generate-large';

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
   * Override hideSuggestion to ensure proper cleanup
   * @override
   */
  hideSuggestion() {
    // Hide the suggestion UI element (if it exists and is separate)
    if (this.suggestionElement) {
      this.suggestionElement.style.display = 'none';
    }
    
    // Remove any inline suggestion elements from the DOM
    this.removeInlineSuggestion();
    
    // Reset state
    this.suggestionActive = false;
    this.suggestionText = '';
    
    // Clear any data attributes from the main suggestion element
    if (this.suggestionElement) {
      this.suggestionElement.removeAttribute('data-position');
    }
    
    // Remove any suggestion markers left in the editor content area
    try {
       if (this.editor && this.editor.root) {
         const markers = this.editor.root.querySelectorAll('.suggestion-marker');
         markers.forEach(marker => marker.remove());
       }
    } catch (error) {
        console.error('Error removing suggestion markers:', error);
    }
  }
  
  /**
   * Override removeInlineSuggestion to ensure complete cleanup
   * @override
   */
  removeInlineSuggestion() {
    try {
      // Remove any inline suggestion spans from the editor content area
       if (this.editor && this.editor.root) {
         const suggestions = this.editor.root.querySelectorAll('.inline-suggestion');
         suggestions.forEach(suggestion => suggestion.remove());
       }
    } catch (error) {
      console.error('Error removing inline suggestions:', error);
    }
  }
  
  /**
   * Override acceptSuggestion to ensure it works with the current content
   * and prevent race conditions
   * @override
   */
  acceptSuggestion() {
    if (!this.suggestionActive || !this.editor) return;
    
    try {
      // Use a flag to prevent race conditions and multiple acceptances
      if (this._isAcceptingSuggestion) {
        console.log('Already accepting a suggestion, ignoring duplicate request');
        return;
      }
      
      this._isAcceptingSuggestion = true;
      
      // Get current state
      const selection = this.editor.getSelection();
      if (!selection) {
        this._isAcceptingSuggestion = false;
        return;
      }
      
      const cursorPosition = selection.index;
      const text = this.editor.getText();
      
      // Get the suggestion text from either the suggestion element or inline elements
      let suggestionText = '';
      
      // First try getting from a dedicated suggestion element 
      if (this.suggestionElement && this.suggestionElement.querySelector('.suggestion-text')) {
        suggestionText = this.suggestionElement.querySelector('.suggestion-text').textContent;
      }
      
      // If that fails, try getting from the active inline suggestion in the DOM
      if (!suggestionText) {
        const inlineSuggestion = document.querySelector('.inline-suggestion');
        if (inlineSuggestion) {
          suggestionText = inlineSuggestion.textContent;
        }
      }
      
      // If we still don't have a suggestion text, use the cached one
      if (!suggestionText && this.suggestionText) {
        suggestionText = this.suggestionText;
      }
      
      // If we have suggestion text to insert
      if (suggestionText && suggestionText.trim() !== '') {
        // Insert the suggestion at the cursor position using the Quill API
        this.editor.insertText(cursorPosition, suggestionText);
        
        // Move cursor to end of inserted text
        this.editor.setSelection(cursorPosition + suggestionText.length, 0);
        
        // Add to the completion cache for future use
        // Use the EXACT prefix at the cursor position for precise caching
        const prefix = text.substring(0, cursorPosition);
        this.addToCompletionCache(prefix, suggestionText);
        
        console.log('Suggestion accepted and inserted:', suggestionText);
      } else {
        console.warn('No suggestion text found to accept');
      }
      
      // Always hide the suggestion UI elements after trying to accept
      this.hideSuggestion();
      
      // Ensure editor stays focused
      this.editor.focus();
      
      // Auto-save after accepting suggestion
      this.autosaveCurrentDocument();
      
      // Release the flag
      this._isAcceptingSuggestion = false;
    } catch (error) {
      console.error('Error accepting suggestion:', error);
      this.hideSuggestion();
      this._isAcceptingSuggestion = false;
    }
  }
  
  /**
   * Override showInlineSuggestion to store position information
   * @override
   */
  showInlineSuggestion(suggestion, position) {
    if (!this.editor || !this.suggestionElement || this.suggestionActive) return;
    
    try {
      // Store the position for later validation
      this.suggestionElement.dataset.position = position.toString();
      
      // Set the suggestion text
      const suggestionTextEl = this.suggestionElement.querySelector('.suggestion-text');
      if (suggestionTextEl) {
        suggestionTextEl.textContent = suggestion;
      }
      
      // Position the suggestion element
      const bounds = this.editor.getBounds(position);
      if (bounds) {
        this.suggestionElement.style.top = `${bounds.top}px`;
        this.suggestionElement.style.left = `${bounds.left}px`;
        this.suggestionElement.style.display = 'block';
      }
      
      // Mark suggestion as active
      this.suggestionActive = true;
      this.suggestionText = suggestion;
      
      // Add the inline suggestion as a span to the editor
      const inlineNode = document.createElement('span');
      inlineNode.className = 'inline-suggestion';
      inlineNode.textContent = suggestion;
      
      // Insert at current position
      const quill = this.editor;
      const editorElement = quill.root;
      
      // Mark selection point for the SuggestionBlot
      const selection = quill.getSelection();
      if (selection) {
        // Add marker for inline suggestion node
        const marker = document.createElement('span');
        marker.className = 'suggestion-marker';
        marker.dataset.position = position.toString();
        
        // Insert marker and suggestion node in DOM but not in Quill Delta
        const cursorNode = this.getNodeAtPosition(editorElement, position);
        if (cursorNode) {
          cursorNode.parentNode.insertBefore(marker, cursorNode.nextSibling);
          marker.parentNode.insertBefore(inlineNode, marker.nextSibling);
        }
      }
    } catch (error) {
      console.error('Error showing inline suggestion:', error);
      this.suggestionActive = false;
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
      
      // Get current cursor position
      const selection = this.editor.getSelection();
      if (!selection) return;
      
      const cursorPosition = selection.index;
      
      // Get the suggestion position from the element's data attribute 
      // or directly from the document element
      let suggestionPos = 0;
      
      if (this.suggestionElement && this.suggestionElement.dataset.position) {
        suggestionPos = parseInt(this.suggestionElement.dataset.position || '0');
      } else {
        // Try to find the suggestion marker in the DOM
        const marker = document.querySelector('.suggestion-marker');
        if (marker && marker.dataset.position) {
          suggestionPos = parseInt(marker.dataset.position || '0');
        }
      }
      
      // Only accept if cursor is close enough to where suggestion was shown
      if (Math.abs(cursorPosition - suggestionPos) <= EnhancedTextGeneratorDocs.CONFIG.CURSOR_TOLERANCE) {
        console.log('Accepting suggestion via Tab key');
        this.acceptSuggestion();
      } else {
        // If cursor moved too far, hide suggestion instead of accepting
        console.log('Cursor moved too far from suggestion position, hiding instead of accepting');
        this.hideSuggestion();
      }
      return false; // Ensure the event is completely stopped
    }
    
    // If escape is pressed and we have an active suggestion, hide it
    if (event.key === 'Escape' && this.suggestionActive) {
      event.preventDefault();
      this.hideSuggestion();
      return;
    }
    
    // For all other keys, call parent method
    super.handleKeyDown(event);
  }

  /**
   * Override showGenerateContentDialog to act as a Rewrite/Edit trigger
   * @override
   */
  showGenerateContentDialog() {
    // Create dialog container
    const dialogContainer = document.createElement('div');
    dialogContainer.className = 'tgdocs-generate-dialog';
    
    // Create dialog content
    const dialogContent = document.createElement('div');
    dialogContent.className = 'tgdocs-generate-dialog-content';
    
    // Add title
    const title = document.createElement('h3');
    title.textContent = 'Rewrite Document';
    dialogContent.appendChild(title);
    
    // Add description
    const description = document.createElement('p');
    description.textContent = 'Enter instructions for rewriting the entire document below.';
    dialogContent.appendChild(description);
    
    // Add textarea for prompt
    const promptTextarea = document.createElement('textarea');
    promptTextarea.className = 'tgdocs-generate-prompt';
    promptTextarea.placeholder = 'e.g., Make this more concise, Fix grammar, Change the tone to formal';
    promptTextarea.value = "Let's make this more concise"; 
    dialogContent.appendChild(promptTextarea);
    
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
    
    // Add rewrite button
    const rewriteButton = document.createElement('button');
    rewriteButton.className = 'mdl-button mdl-js-button mdl-button--raised mdl-button--colored';
    rewriteButton.textContent = 'Rewrite';
    rewriteButton.addEventListener('click', async () => {
      const instructionPrompt = promptTextarea.value.trim();
      if (instructionPrompt) {
        closeDialog(); // Close dialog before starting rewrite
        await this.rewriteDocument(instructionPrompt);
      }
    });
    actions.appendChild(rewriteButton);
    
    dialogContent.appendChild(actions);
    dialogContainer.appendChild(dialogContent);
    document.body.appendChild(dialogContainer);
    
    // Focus the textarea and select the default text
    promptTextarea.focus();
    promptTextarea.select();

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
   * Rewrites the entire document based on instructions using an LLM.
   * @param {string} instructionPrompt - The instructions for rewriting.
   */
  async rewriteDocument(instructionPrompt) {
    if (!this.editor) return;

    const fullDocumentText = this.editor.getText();
    if (!fullDocumentText || fullDocumentText.trim() === '\n') {
      this.updateSaveStatus('Document is empty, nothing to rewrite.');
      return;
    }

    this.updateSaveStatus('Rewriting document...');

    try {
      // Determine the API endpoint (always use Claude for rewriting for better quality)
      const isLocal = window.location.hostname.includes('localhost') || window.location.hostname.includes('127.0.0.1');
      const largeGenerateEndpoint = isLocal ? 
          'http://localhost:8000/api/v1/generate-large' : 
          'https://api.text-generator.io/api/v1/generate-large';

      // Construct a system message suitable for rewriting
      const system_message = `You are an expert editor. Rewrite the following document based *only* on the user's instructions. Preserve the original meaning unless instructed otherwise. Output *only* the rewritten document content, without any preamble, comments, or explanations. Do not include the instructions in your output. The user's instruction is: ${instructionPrompt}`;

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
        return;
      }

      const data = await response.json();

      if (!data || !Array.isArray(data) || data.length === 0) {
        console.warn('Empty or invalid response from rewrite API');
        this.updateSaveStatus('Rewrite received empty response');
        return;
      }

      // The API might return the original prompt + generation, or just the generation.
      // We want *only* the rewritten content.
      // Assuming the structure returns { generated_text: "... rewritten content ..." }
      // Claude might prepend the original text, so we need to be careful.
      // Since the system prompt asks *only* for the rewritten content, we hope it complies.
      let rewrittenText = data[0].generated_text;
      
      // Basic check: If the response starts exactly with the original text, try removing it.
      // This is imperfect but might handle some cases.
      if (rewrittenText.startsWith(fullDocumentText)) {
         // rewrittenText = rewrittenText.substring(fullDocumentText.length).trimStart();
         // Let's trust the system prompt for now, assuming it outputs only the rewrite.
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
    }
  }

  /**
   * Autowrites text starting from the current cursor position based on preceding content.
   */
  async autoWriteFromCursor() {
    if (!this.editor) return;

    const selection = this.editor.getSelection();
    if (!selection) return;

    const cursorPosition = selection.index;
    const textBeforeCursor = this.editor.getText(0, cursorPosition);

    if (!textBeforeCursor || textBeforeCursor.trim() === '') {
      this.updateSaveStatus('Cannot autowrite without preceding text.');
      return;
    }

    this.updateSaveStatus('Autowriting...');

    try {
      // Determine the API endpoint (Claude for better continuation)
      const isLocal = window.location.hostname.includes('localhost') || window.location.hostname.includes('127.0.0.1');
      const largeGenerateEndpoint = isLocal ? 
          'http://localhost:8000/api/v1/generate-large' : 
          'https://api.text-generator.io/api/v1/generate-large';

      // Construct a system message suitable for continuation
      const system_message = `You are a helpful writing assistant. Continue writing naturally from the following text. Do not repeat the provided text. Output only the continuation.`;

      const response = await fetch(largeGenerateEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'secret': this.secret
        },
        body: JSON.stringify({
          text: textBeforeCursor, // Send preceding text as prompt
          // Use settings suitable for creative continuation
          max_length: 500, // Moderate length for continuation
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
        return;
      }

      const data = await response.json();

      if (!data || !Array.isArray(data) || data.length === 0) {
        console.warn('Empty or invalid response from autowrite API');
        this.updateSaveStatus('Autowrite received empty response');
        return;
      }

      // Extract only the generated continuation
      let continuationText = data[0].generated_text;
      // If the API includes the prompt, remove it
      if (continuationText.startsWith(textBeforeCursor)) {
        continuationText = continuationText.substring(textBeforeCursor.length);
      }
      
      // It might be better to rely on the system prompt asking for *only* the continuation
      // continuationText = data[0].generated_text;

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
      console.error('Error autowriting text:', error);
      this.updateSaveStatus('Autowrite failed');
    }
  }
} 