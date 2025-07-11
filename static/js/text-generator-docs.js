/**
 * Text Generator Docs - A Medium-style WYSIWYG editor with AI-powered autocomplete
 */

// Import Quill Delta for operations
const Delta = Quill.import('delta');

class TextGeneratorDocs {
  constructor(options) {
    this.options = options || {};
    
    // Helper function to safely get DOM elements
    const safeGetElement = (element) => {
      if (typeof element === 'string') {
        return document.getElementById(element);
      }
      return element || null;
    };
    
    // Safely assign DOM elements
    this.editorContainer = safeGetElement(options.editorContainer);
    this.documentsList = safeGetElement(options.documentsList);
    this.newDocButton = safeGetElement(options.newDocButton);
    this.saveDocButton = safeGetElement(options.saveDocButton);
    this.exportDocButton = safeGetElement(options.exportDocButton);
    this.docTitleInput = safeGetElement(options.docTitleInput);
    this.generateContentButton = safeGetElement(options.generateContentButton);
    this.claudeToggle = safeGetElement(options.claudeToggle);
    this.generationSettings = options.generationSettings || {
      number_of_results: 1,
      max_length: 500,
      max_sentences: 10,
      min_probability: 0.7,
      stop_sequences: [],
      top_p: 0.9,
      top_k: 40,
      temperature: 0.75,
      repetition_penalty: 1.17,
      seed: 0
    };
    
    this.currentDocId = null;
    this.currentDocData = null;
    this.documents = [];
    this.debounceTimeout = null;
    this.isGenerating = false;
    this.suggestionText = '';
    this.suggestionActive = false;
    this.secret = this.getSecretKey();
    this.useClaudeForBulk = this.claudeToggle ? this.claudeToggle.checked : true;
    
    // Get or create anonymous user ID for localStorage
    this.anonymousUserId = localStorage.getItem('tgdocs-anonymous-user-id');
    if (!this.anonymousUserId) {
      this.anonymousUserId = 'anon_' + Date.now();
      localStorage.setItem('tgdocs-anonymous-user-id', this.anonymousUserId);
    }
    
    // Completion cache - initialize LRU cache
    this.completionCache = this.loadCompletionCache();
    this.maxCacheSize = 1000;
    
    this.init();
  }
  
  // Load the completion cache from localStorage
  loadCompletionCache() {
    try {
      const cachedData = localStorage.getItem('tgdocs-completion-cache');
      return cachedData ? JSON.parse(cachedData) : {};
    } catch (e) {
      console.error('Error loading completion cache:', e);
      return {};
    }
  }
  
  // Save the completion cache to localStorage
  saveCompletionCache() {
    try {
      localStorage.setItem('tgdocs-completion-cache', JSON.stringify(this.completionCache));
    } catch (e) {
      console.error('Error saving completion cache:', e);
    }
  }
  
  // Add an item to the LRU cache
  addToCompletionCache(prefix, completion) {
    // Get the cache keys and create a new object for LRU behavior
    const cacheKeys = Object.keys(this.completionCache);
    const newCache = {};
    
    // Add the new item first (or move to front if it exists)
    newCache[prefix] = {
      completion,
      timestamp: Date.now()
    };
    
    // If we're at max capacity, remove oldest items
    if (cacheKeys.length >= this.maxCacheSize) {
      // Sort by timestamp (oldest first)
      const sortedEntries = Object.entries(this.completionCache)
        .sort((a, b) => a[1].timestamp - b[1].timestamp);
      
      // Remove oldest entries to make room
      const entriesToKeep = sortedEntries.slice(
        sortedEntries.length - this.maxCacheSize + 1
      );
      
      // Add remaining entries to the new cache
      for (const [key, value] of entriesToKeep) {
        if (key !== prefix) { // Skip the one we just added
          newCache[key] = value;
        }
      }
    } else {
      // If not at capacity, just add all other entries
      for (const key of cacheKeys) {
        if (key !== prefix) { // Skip the one we just added
          newCache[key] = this.completionCache[key];
        }
      }
    }
    
    // Update cache and save to localStorage
    this.completionCache = newCache;
    this.saveCompletionCache();
  }
  
  // Get an item from the cache
  getFromCompletionCache(prefix) {
    const cacheItem = this.completionCache[prefix];
    if (cacheItem) {
      // Update timestamp when accessed (LRU behavior)
      cacheItem.timestamp = Date.now();
      return cacheItem.completion;
    }
    return null;
  }
  
  async init() {
    // Only initialize the editor if the container exists
    if (this.editorContainer) {
      // Initialize the editor
      this.initEditor();
    } else {
      console.error('Editor container not found. Editor initialization skipped.');
      this.editor = null;
    }
    
    // Initialize event listeners
    this.initEventListeners();
    
    // Check user authentication
    const isAuthenticated = await this.checkUserAuthentication();
    
    // Load documents if authenticated
    if ((isAuthenticated || this.userId) && this.documentsList) {
      this.loadDocuments();
    }
  }
  
  initEditor() {
    try {
      // Create inline suggestion blot
      const Inline = Quill.import('blots/inline');
      class SuggestionBlot extends Inline {
        static create(value) {
          let node = super.create();
          node.setAttribute('data-suggestion', value);
          // Add important inline styles to ensure visibility
          node.style.cssText = `
            display: inline !important;
            color: #999 !important;
            opacity: 0.6 !important;
            user-select: none !important;
            pointer-events: none !important;
            background-color: rgba(240, 240, 240, 0.3) !important;
            visibility: visible !important;
            position: relative !important;
            z-index: 5 !important;
          `;
          return node;
        }
        
        static value(node) {
          return node.getAttribute('data-suggestion');
        }
      }
      
      SuggestionBlot.blotName = 'suggestion';
      SuggestionBlot.tagName = 'span';
      SuggestionBlot.className = 'inline-suggestion';
      
      Quill.register(SuggestionBlot);
      
      // Add CSS rule for the suggestion format
      const style = document.createElement('style');
      style.id = 'suggestion-inline-style'; // Add ID to prevent duplicates if init runs again
      if (!document.getElementById(style.id)) {
          style.textContent = `
            .inline-suggestion {
              color: grey !important;
              opacity: 0.6 !important;
              background-color: rgba(220, 220, 220, 0.3) !important; /* Subtle background */
              /* Add pointer-events: none? Might interfere with selection */
            }
          `;
          document.head.appendChild(style);
      }
      
      // Ensure suggestion styles
      const ensureSuggestionStyles = () => {
        // Check if our suggestion style enforcement is already in the document
        if (!document.getElementById('suggestion-style-enforcer')) {
          const style = document.createElement('style');
          style.id = 'suggestion-style-enforcer';
          // More specific selector to increase specificity and override potential conflicts
          style.textContent = `
            span.inline-suggestion, 
            .ql-editor span.inline-suggestion {
              display: inline !important;
              color: #999 !important;
              opacity: 0.6 !important;
              user-select: none !important;
              pointer-events: none !important;
              background-color: rgba(240, 240, 240, 0.3) !important;
              visibility: visible !important;
              position: relative !important;
              z-index: 5 !important;
            }
          `;
          document.head.appendChild(style);
        }
      };
      
      // Call this function to ensure our styles are applied
      ensureSuggestionStyles();
      
      // Initialize the Quill editor
      this.editor = new Quill(this.editorContainer, {
        theme: 'snow',
        modules: {
          toolbar: [
            [{ 'header': [1, 2, 3, false] }],
            ['bold', 'italic', 'underline', 'strike'],
            ['blockquote', 'code-block'],
            [{ 'list': 'ordered'}, { 'list': 'bullet' }],
            ['link', 'image'],
            ['clean']
          ]
        },
        placeholder: 'Start writing or press Alt+Enter to generate content...'
      });
      
      // Apply highlighting to code blocks after content changes
      this.editor.on('text-change', (delta, oldDelta, source) => {
        // Check for code-block formatting in the delta
        if (delta.ops) {
          let hasCodeBlock = delta.ops.some(op => 
            op.attributes && op.attributes['code-block']
          );
          
          // If there's a code block, apply highlight.js
          if (hasCodeBlock && window.hljs) {
            // Small delay to let Quill render the code block
            setTimeout(() => {
              // Find all code blocks in the editor
              const codeBlocks = document.querySelectorAll('.ql-editor pre');
              codeBlocks.forEach(block => {
                // Only highlight if not already highlighted
                if (!block.classList.contains('hljs')) {
                  // Get language if specified
                  const language = block.getAttribute('data-language') || '';
                  if (language) {
                    block.classList.add(`language-${language}`);
                  }
                  // Apply highlighting
                  window.hljs.highlightElement(block);
                }
              });
            }, 10);
          }
        }
      });
      
      // Focus on editor
      this.editor.focus();

      // Add tooltips with keyboard shortcuts to Quill toolbar buttons
      this.addQuillToolbarTooltips();

    } catch (e) {
      console.error('Error initializing editor:', e);
    }
  }
  
  addQuillToolbarTooltips() {
    const isMac = /Mac|iPod|iPhone|iPad/.test(navigator.platform);
    const modifier = isMac ? 'Cmd' : 'Ctrl';

    const tooltips = {
      '.ql-bold': `Bold (${modifier}+B)`,
      '.ql-italic': `Italic (${modifier}+I)`,
      '.ql-underline': `Underline (${modifier}+U)`,
      '.ql-link': `Insert Link (${modifier}+K)`,
      // Add others as needed - check Quill defaults or specific config
      '.ql-header[value="1"]': 'Header 1',
      '.ql-header[value="2"]': 'Header 2',
      '.ql-header[value="3"]': 'Header 3',
      '.ql-blockquote': 'Blockquote',
      '.ql-code-block': 'Code Block',
      '.ql-list[value="ordered"]': 'Ordered List',
      '.ql-list[value="bullet"]': 'Bullet List',
      '.ql-clean': 'Remove Formatting'
    };

    // Wait a brief moment for Quill to render the toolbar fully
    setTimeout(() => {
      for (const selector in tooltips) {
        const button = this.editorContainer.parentNode.querySelector(`.ql-toolbar ${selector}`);
        if (button) {
          button.setAttribute('title', tooltips[selector]);
        }
      }
    }, 500); // Adjust delay if needed
  }
  
  initEventListeners() {
    // Initialize editor change event
    if (this.editor) {
      this.editor.on('text-change', this.handleEditorChange.bind(this));
      this.editor.root.addEventListener('keydown', this.handleKeyDown.bind(this));
    }
    
    // Initialize image upload functionality
    this.initializeImageUpload();
    
    // Initialize document list events
    if (this.documentsList) {
      this.documentsList.addEventListener('click', (event) => {
        const docItem = event.target.closest('.tgdocs-document-item');
        if (docItem) {
          const docId = docItem.dataset.id;
          this.loadDocument(docId);
        }
      });
    }
    
    // Initialize new document button
    if (this.newDocButton) {
      this.newDocButton.addEventListener('click', () => {
        this.createNewDocument();
      });
    }
    
    // Initialize save document button
    if (this.saveDocButton) {
      this.saveDocButton.addEventListener('click', () => {
        this.saveCurrentDocument();
      });
    }
    
    // Initialize export document button
    if (this.exportDocButton) {
      this.exportDocButton.addEventListener('click', () => {
        this.exportCurrentDocument();
      });
    }
    
    // Initialize document title input
    if (this.docTitleInput) {
      this.docTitleInput.addEventListener('change', () => {
        this.handleTitleChange();
      });
      
      this.docTitleInput.addEventListener('blur', () => {
        this.handleTitleChange();
      });
    }
    
    // Initialize generate content button
    if (this.generateContentButton) {
      this.generateContentButton.addEventListener('click', () => {
        this.showGenerateContentDialog();
      });
    }
  }
  
  async checkUserAuthentication() {
    try {
      // Try to get current user from API
      try {
        const response = await fetch('/api/current-user');
        if (response.ok) {
          const userData = await response.json();
          if (userData && userData.id) {
            this.userId = userData.id;
            return true;
          }
        }
      } catch (error) {
        console.log("API error when checking authentication:", error);
      }
      
      // Check if we have a secret key
      if (this.secret) {
        // Use a temporary user ID based on the secret key
        this.userId = 'user_' + this.hashString(this.secret);
        return true;
      }
      
      // Fallback to anonymous user ID for localStorage
      this.userId = this.anonymousUserId;
      
      // Show login prompt if we don't have a real user or secret
      this.showLoginPrompt();
      return false;
    } catch (error) {
      console.error('Error checking authentication:', error);
      
      // Fallback to anonymous user ID
      this.userId = this.anonymousUserId;
      return false;
    }
  }
  
  // Simple string hashing function for creating user IDs from secrets
  hashString(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    return Math.abs(hash).toString(16);
  }
  
  handleEditorChange(delta, oldDelta, source) {
    // If editor isn't initialized, don't proceed
    if (!this.editor) {
      return;
    }
    
    if (source !== 'user') return;
    
    // AUTOCOMPLETE HANDLING
    // Clear any existing autocomplete debounce
    clearTimeout(this.debounceTimeout);
    
    // Cancel any active suggestion
    if (this.suggestionActive) {
      this.hideSuggestion();
    }
    
    this.debounceTimeout = setTimeout(() => {
      this.generateAutocompleteSuggestion();
    }, 2000);
    
    // AUTOSAVE HANDLING
    // Clear any existing autosave debounce
    clearTimeout(this.autosaveTimeout);
    
    // Show saving indicator
    this.updateSaveStatus('Saving');
    
    // Debounce autosave (1 minute)
    this.autosaveTimeout = setTimeout(() => {
      this.autosaveCurrentDocument();
    }, 60000);
  }
  
  updateSaveStatus(message) {
    try {
      // Normalize message: remove trailing ellipses for 'Saving...'
      let displayMessage = message;
      if (displayMessage.endsWith('...')) {
        displayMessage = displayMessage.slice(0, -3);
      }
      // Create or update save status element
      if (!this.saveStatusElement) {
        this.saveStatusElement = document.createElement('div');
        this.saveStatusElement.className = 'tgdocs-save-status';
        this.saveStatusElement.style.position = 'fixed';
        this.saveStatusElement.style.bottom = '10px';
        this.saveStatusElement.style.right = '10px';
        // Less prominent style: white background, black text
        this.saveStatusElement.style.padding = '5px 10px';
        this.saveStatusElement.style.backgroundColor = '#fff';
        this.saveStatusElement.style.color = '#000';
        this.saveStatusElement.style.borderRadius = '3px';
        this.saveStatusElement.style.zIndex = '1000';
        this.saveStatusElement.style.opacity = '1';
        this.saveStatusElement.style.transition = 'opacity 0.3s ease-in-out';
        document.body.appendChild(this.saveStatusElement);
      }
      
      // Update text
      this.saveStatusElement.textContent = displayMessage;
      
      // Add 'saved' class if message indicates successful save
      if (displayMessage === 'Saved') {
        this.saveStatusElement.classList.add('saved');
        
        // Fade out the status after 2 seconds
        setTimeout(() => {
          if (this.saveStatusElement) {
            this.saveStatusElement.style.opacity = '0';
          }
        }, 2000);
      } else {
        this.saveStatusElement.classList.remove('saved');
      }
    } catch (e) {
      console.error('Error updating save status:', e);
    }
  }
  
  async generateAutocompleteSuggestion() {
    try {
      // Check if editor exists
      if (!this.editor) {
        console.warn('Editor not initialized for autocomplete');
        return;
      }
      
      if (this.isGenerating) return;
      
      const text = this.editor.getText();
      if (!text || text.length < 5) return; // Minimum text length for generation
      
      // Get cursor position and surrounding text
      const selection = this.editor.getSelection();
      if (!selection) return;
      
      const cursorPosition = selection.index;
      const textBeforeCursor = text.substring(0, cursorPosition);
      
      // First check if we have this prefix in cache
      const cachedSuggestion = this.getFromCompletionCache(textBeforeCursor);
      if (cachedSuggestion) {
        console.log("Using cached suggestion for:", textBeforeCursor);
        this.showInlineSuggestion(cachedSuggestion, cursorPosition);
        return;
      }
      
      // Always generate suggestions when we have enough text
      this.isGenerating = true;
      
      try {
        console.log("Generating suggestion for:", textBeforeCursor);
        const response = await this.fetchSuggestion(textBeforeCursor);
        if (response && response.generations && response.generations.length > 0) {
          const suggestion = response.generations[0].text;
          if (suggestion && suggestion.trim() !== '') {
            console.log("Received suggestion:", suggestion);
            // Cache the suggestion
            this.addToCompletionCache(textBeforeCursor, suggestion);
            
            // Show the inline suggestion
            this.showInlineSuggestion(suggestion, cursorPosition);
          } else {
            console.log("Empty suggestion received");
          }
        } else {
          console.log("No valid suggestion response");
        }
      } catch (error) {
        console.error('Error generating text:', error);
      } finally {
        this.isGenerating = false;
      }
    } catch (e) {
      console.error('Error in generateAutocompleteSuggestion:', e);
      this.isGenerating = false;
    }
  }
  
  async fetchSuggestion(prompt) {
    // Call text generation API with the proper endpoint
    const settings = {
      ...this.generationSettings,
      text: prompt
    };
    
    try {
      // Use the correct API endpoint for text generation with secret key in header
      const response = await fetch('https://api.text-generator.io/api/v1/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'secret': this.secret
        },
        body: JSON.stringify(settings)
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`API Error (${response.status}): ${errorText}`);
        throw new Error(`API request failed: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // If no data or empty array, return null
      if (!data || !Array.isArray(data) || data.length === 0) {
        console.warn('Empty or invalid response from API');
        return null;
      }
      
      // Process the response correctly - extract the generated text that comes after the prompt
      const suggestedText = data[0].generated_text.substring(prompt.length);
      
      return {
        generations: [{
          text: suggestedText
        }]
      };
    } catch (error) {
      console.error('API Error:', error);
      return null;
    }
  }
  
  showInlineSuggestion(suggestion, position) {
    if (!suggestion || suggestion.trim() === '') return;
    
    // First remove any existing suggestions
    this.removeInlineSuggestion();
    
    // Store suggestion
    this.suggestionText = suggestion;
    this.suggestionActive = true;
    
    try {
      // Insert the suggestion text as inline suggestion
      const currentLength = this.editor.getLength();
      
      // Save the current selection
      const savedSelection = this.editor.getSelection();
      
      // Insert the suggestion with the suggestion format
      this.editor.insertText(position, suggestion, { 'suggestion': true });
      
      // Restore the cursor position
      this.editor.setSelection(savedSelection);
      
      // Make sure the suggestion is visible by applying styles directly
      // and handling potential timing issues with multiple approaches
      
      // Approach 1: Direct styling with timeout
      setTimeout(() => {
        const inlineSuggestions = document.querySelectorAll('.inline-suggestion');
        if (inlineSuggestions.length > 0) {
          inlineSuggestions.forEach(el => {
            // Apply all styles with !important to override any conflicting styles
            el.style.cssText = `
              display: inline !important;
              color: #999 !important;
              opacity: 0.6 !important;
              user-select: none !important;
              pointer-events: none !important;
              background-color: rgba(240, 240, 240, 0.3) !important;
              visibility: visible !important;
              position: relative !important;
              z-index: 5 !important;
            `;
          });
        }
        
        // Approach 2: Force a DOM refresh to ensure rendering
        // This is a non-standard but effective approach that forces a repaint
        this.editor.root.style.display = 'none';
        void this.editor.root.offsetHeight; // This will force a reflow
        this.editor.root.style.display = 'block';
        
        // Restore selection again after DOM update
        if (savedSelection) {
          this.editor.setSelection(savedSelection);
        }
      }, 10);
      
      // Approach 3: Try again after a longer delay as a fallback
      setTimeout(() => {
        const inlineSuggestions = document.querySelectorAll('.inline-suggestion');
        if (inlineSuggestions.length > 0) {
          inlineSuggestions.forEach(el => {
            el.style.cssText = `
              display: inline !important;
              color: #999 !important;
              opacity: 0.6 !important;
              user-select: none !important;
              pointer-events: none !important;
              background-color: rgba(240, 240, 240, 0.3) !important;
              visibility: visible !important;
              position: relative !important;
              z-index: 5 !important;
            `;
          });
        }
      }, 100);
    } catch (e) {
      console.error('Error showing inline suggestion:', e);
      this.suggestionActive = false;
    }
  }
  
  hideSuggestion() {
    // Alias for removeInlineSuggestion for clarity
    this.removeInlineSuggestion();
  }
  
  removeInlineSuggestion() {
    if (!this.suggestionActive) return;
    
    try {
      // First attempt using DOM approach
      const suggestionElements = this.editor.root.querySelectorAll('.inline-suggestion');
      if (suggestionElements.length > 0) {
        // Get current selection to restore after
        const savedSelection = this.editor.getSelection();
        
        // Remove each suggestion element
        suggestionElements.forEach(el => {
          el.parentNode?.removeChild(el);
        });
        
        // Restore selection if needed
        if (savedSelection) {
          this.editor.setSelection(savedSelection);
        }
      } else {
        // Fallback approach using Quill API
        const content = this.editor.getContents();
        
        // Find and remove all suggestion blots
        for (let i = 0; i < content.ops.length; i++) {
          const op = content.ops[i];
          if (op.attributes && op.attributes.suggestion) {
            // Get the current selection to restore after
            const savedSelection = this.editor.getSelection();
            
            // Remove this suggestion
            const length = op.insert.length;
            const index = this.editor.getText().indexOf(op.insert);
            if (index >= 0) {
              this.editor.deleteText(index, length);
            }
            
            // Restore selection if needed
            if (savedSelection) {
              this.editor.setSelection(savedSelection);
            }
          }
        }
      }
      
      // Force a refresh of the editor content
      this.editor.root.style.display = 'none';
      void this.editor.root.offsetHeight; // Force reflow
      this.editor.root.style.display = '';
    } catch (e) {
      console.error('Error removing inline suggestion:', e);
    }
    
    // Reset suggestion state
    this.suggestionActive = false;
    this.suggestionText = '';
  }
  
  acceptSuggestion() {
    if (!this.suggestionActive || !this.editor) return;
    
    try {
      // Get the current content with the suggestion
      const content = this.editor.getContents();
      
      // Find all suggestion blots
      for (let i = 0; i < content.ops.length; i++) {
        const op = content.ops[i];
        if (op.attributes && op.attributes.suggestion) {
          // Get the suggestion text
          const suggestionText = op.insert;
          const length = suggestionText.length;
          
          // Find the position of the suggestion text in the editor
          const text = this.editor.getText();
          const index = text.indexOf(suggestionText);
          
          if (index >= 0) {
            // Delete the suggestion formatting but keep the text
            this.editor.formatText(index, length, { 'suggestion': false });
            
            // Set cursor position after the accepted suggestion
            this.editor.setSelection(index + length, 0);
          }
        }
      }
      
      // Clear the suggestion state
      this.suggestionActive = false;
      this.suggestionText = '';
      
      // Add to autocompletion cache
      const text = this.editor.getText();
      const selection = this.editor.getSelection();
      if (selection) {
        const textBeforeCursor = text.substring(0, selection.index);
        // Don't cache too much context
        const lastFewWords = textBeforeCursor.split(/\s+/).slice(-10).join(' ').trim();
        if (lastFewWords.length > 0 && this.suggestionText.length > 0) {
          this.addToCompletionCache(lastFewWords, this.suggestionText);
        }
      }
    } catch (error) {
      console.error('Error accepting suggestion:', error);
    }
  }
  
  handleKeyDown(event) {
    // If editor is not initialized, don't handle keyboard events
    if (!this.editor) {
      return;
    }
    
    // Tab key to accept suggestion
    if (event.key === 'Tab' && this.suggestionActive) {
      event.preventDefault();
      event.stopPropagation();  // Prevent default tab behavior
      this.acceptSuggestion();
      return false;  // Make sure tab doesn't propagate
    }
    
    // Alt+Enter to generate content (cross-browser support)
    if ((event.key === 'Enter' && event.altKey) || (event.keyCode === 13 && event.altKey)) {
      event.preventDefault();
      event.stopPropagation(); // Prevent the event from bubbling up
      
      // Cancel any active suggestion first
      if (this.suggestionActive) {
        this.hideSuggestion();
      }
      
      // Get text before cursor to use as prompt
      const selection = this.editor.getSelection();
      if (selection) {
        const text = this.editor.getText();
        const textBeforeCursor = text.substring(0, selection.index);
        
        // Get the last several words to use as context
        // More words provide better context for generation
        const lastFewWords = textBeforeCursor.split(/\s+/).slice(-15).join(' ').trim();
        
        if (lastFewWords.length > 0) {
          // Show a brief visual feedback that generation is happening
          this.updateSaveStatus('Generating');
          
          // Small delay to ensure UI updates before potentially intensive operation
          setTimeout(() => {
            // Generate content using text before cursor as prompt
            this.insertLLMResponse(lastFewWords, true);
          }, 10);
        } else {
          // If there's no text before cursor, show the generate dialog instead
          this.showGenerateContentDialog();
        }
      }
      
      return false; // Ensure the event is fully handled
    }
  }
  
  async loadDocuments() {
    if (!this.userId) return;
    
    try {
      // Try to get documents from database via API
      try {
        const response = await fetch(`/api/docs/list`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          this.documents = data.documents || [];
          // dedupe by id
          this.documents = Array.from(new Map(this.documents.map(d => [d.id, d])).values());
        } else {
          // API endpoint not available, use localStorage as fallback
          console.log("API endpoint not available, using localStorage fallback");
          this.loadDocumentsFromLocalStorage();
        }
      } catch (error) {
        // Network error or API not available, use localStorage as fallback
        console.log("API error, using localStorage fallback:", error);
        this.loadDocumentsFromLocalStorage();
      }
      
      this.renderDocumentsList();
      
      // If there are documents, load the first one
      if (this.documents.length > 0) {
        this.loadDocument(this.documents[0].id);
      } else {
        this.createNewDocument();
      }
    } catch (error) {
      console.error('Error loading documents:', error);
      // Fallback to empty state
      this.documents = [];
      this.renderDocumentsList();
      this.createNewDocument();
    }
  }
  
  loadDocumentsFromLocalStorage() {
    // Get documents from localStorage
    try {
      const storedDocs = localStorage.getItem(`tgdocs-documents-${this.userId}`);
      if (storedDocs) {
        this.documents = JSON.parse(storedDocs);
        // dedupe by id
        this.documents = Array.from(new Map(this.documents.map(d => [d.id, d])).values());
      } else {
        this.documents = [];
      }
    } catch (e) {
      console.error('Error loading from localStorage:', e);
      this.documents = [];
    }
  }
  
  renderDocumentsList() {
    // Clear list
    this.documentsList.innerHTML = '';
    
    // Add each document to the list
    this.documents.forEach(doc => {
      const docItem = document.createElement('div');
      docItem.className = 'tgdocs-document-item';
      if (this.currentDocId === doc.id) {
        docItem.classList.add('active');
      }
      
      const title = document.createElement('h4');
      title.className = 'tgdocs-document-title';
      title.textContent = doc.title || 'Untitled Document';
      
      const date = document.createElement('div');
      date.className = 'tgdocs-document-date';
      date.textContent = this.formatDate(doc.updatedAt);
      
      // Create wrapper for document info
      const docInfo = document.createElement('div');
      docInfo.className = 'tgdocs-document-info';
      docInfo.appendChild(title);
      docInfo.appendChild(date);
      
      // Create delete button
      const deleteBtn = document.createElement('button');
      deleteBtn.className = 'tgdocs-document-delete';
      deleteBtn.innerHTML = '<i class="material-icons">delete</i>';
      deleteBtn.title = 'Delete document';
      deleteBtn.style.border = 'none';
      deleteBtn.style.background = 'transparent';
      deleteBtn.style.cursor = 'pointer';
      deleteBtn.style.color = '#999';
      deleteBtn.style.padding = '4px';
      deleteBtn.style.opacity = '0';
      deleteBtn.style.transition = 'opacity 0.3s';
      
      // Show delete button on hover
      docItem.addEventListener('mouseenter', () => {
        deleteBtn.style.opacity = '1';
      });
      
      docItem.addEventListener('mouseleave', () => {
        deleteBtn.style.opacity = '0';
      });
      
      // Handle delete button click
      deleteBtn.addEventListener('click', (event) => {
        event.stopPropagation(); // Prevent document selection
        this.deleteDocument(doc.id);
      });
      
      docItem.appendChild(docInfo);
      docItem.appendChild(deleteBtn);
      
      // Add click event to load document
      docItem.addEventListener('click', () => {
        this.loadDocument(doc.id);
      });
      
      // Add data attribute for document ID
      docItem.dataset.id = doc.id;
      
      this.documentsList.appendChild(docItem);
    });
  }
  
  formatDate(timestamp) {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric' 
    });
  }
  
  async loadDocument(docId) {
    // skip invalid id
    if (!docId) return;
    try {
      // Try to load from API first
      try {
        const response = await fetch(`/api/docs/get?id=${docId}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        if (response.ok) {
          const docData = await response.json();
          this.currentDocId = docId;
          this.currentDocData = docData;
          
          // Update title
          this.docTitleInput.value = docData.title || '';
          
          // Update editor content
          this.editor.setContents(JSON.parse(docData.content));
          
          // Update active document in list
          this.renderDocumentsList();
          return;
        }
      } catch (error) {
        console.log("API error when loading document, using localStorage:", error);
      }
      
      // Fallback to localStorage if API fails
      const doc = this.documents.find(d => d.id === docId);
      if (doc) {
        this.currentDocId = docId;
        this.currentDocData = doc;
        
        // Update title
        this.docTitleInput.value = doc.title || '';
        
        // Update editor content
        this.editor.setContents(JSON.parse(doc.content));
        
        // Update active document in list
        this.renderDocumentsList();
      } else {
        throw new Error('Document not found in localStorage');
      }
    } catch (error) {
      console.error('Error loading document:', error);
      this.showMessage('Error loading document', 'error');
    }
  }
  
  async saveCurrentDocument() {
    if (!this.userId) {
      this.showLoginPrompt();
      return;
    }
    
    // Get raw content for saving
    const content = JSON.stringify(this.editor.getContents());
    const title = this.docTitleInput.value || 'Untitled Document';
    
    const documentData = {
      title,
      content
    };
    
    if (this.currentDocId) {
      documentData.id = this.currentDocId;
    } else {
      // Generate a new ID if this is a new document
      documentData.id = 'doc_' + Date.now();
    }
    
    try {
      // Try to save to API first
      let apiSaveSuccessful = false;
      
      try {
        const response = await fetch('/api/docs/save', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(documentData)
        });
        
        if (response.ok) {
          const result = await response.json();
          apiSaveSuccessful = true;
          
          // Update current document ID if it was a new document
          if (!this.currentDocId) {
            this.currentDocId = result.id || documentData.id;
            documentData.id = this.currentDocId;
          }
        }
      } catch (error) {
        console.log("API error when saving, using localStorage:", error);
      }
      
      // If API save failed, save to localStorage
      if (!apiSaveSuccessful) {
        this.saveDocumentToLocalStorage(documentData);
      }
      
      // Update documents array and persist
      if (apiSaveSuccessful) {
        const idx = this.documents.findIndex(d => d.id === documentData.id);
        if (idx >= 0) this.documents[idx] = documentData;
        else this.documents.push(documentData);
        localStorage.setItem(`tgdocs-documents-${this.userId}`, JSON.stringify(this.documents));
      }
      
      // Show success message
      this.updateSaveStatus('Saved');
      
      // Update current document ID
      this.currentDocId = documentData.id;
      
      // Refresh documents list
      this.loadDocumentsFromLocalStorage();
      this.renderDocumentsList();
    } catch (error) {
      console.error('Error saving document:', error);
      this.updateSaveStatus('Save failed');
    }
  }
  
  saveDocumentToLocalStorage(documentData) {
    // Save the document to localStorage
    try {
      // Add timestamp
      documentData.updatedAt = new Date().toISOString();
      if (!documentData.createdAt) {
        documentData.createdAt = documentData.updatedAt;
      }
      
      // Update or add the document in the documents array
      const existingIndex = this.documents.findIndex(d => d.id === documentData.id);
      if (existingIndex >= 0) {
        this.documents[existingIndex] = documentData;
      } else {
        this.documents.push(documentData);
      }
      
      // Save to localStorage
      localStorage.setItem(`tgdocs-documents-${this.userId}`, JSON.stringify(this.documents));
      
      console.log("Document saved to localStorage:", documentData.id);
    } catch (e) {
      console.error('Error saving to localStorage:', e);
      throw e;
    }
  }
  
  async autosaveCurrentDocument() {
    try {
      // Check if editor and required elements exist
      if (!this.editor || !this.docTitleInput) {
        console.warn('Editor or document title input not initialized for autosave');
        return;
      }
      
      if (!this.userId) {
        return;
      }
      
      // Get raw content for autosaving
      const content = JSON.stringify(this.editor.getContents());
      const title = this.docTitleInput.value || 'Untitled Document';
      
      const documentData = {
        title,
        content
      };
      
      if (this.currentDocId) {
        documentData.id = this.currentDocId;
      } else {
        // Generate a new ID if this is a new document
        documentData.id = 'doc_' + Date.now();
      }
      
      // Try to autosave to API first
      let apiSaveSuccessful = false;
      
      try {
        // First try the autosave endpoint
        let response = await fetch('/api/docs/autosave', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(documentData)
        });
        
        // If autosave endpoint fails, try the regular save endpoint
        if (!response.ok) {
          response = await fetch('/api/docs/save', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(documentData)
          });
        }
        
        if (response.ok) {
          const result = await response.json();
          apiSaveSuccessful = true;
          
          // Update current document ID if it was a new document
          if (!this.currentDocId) {
            this.currentDocId = result.id || documentData.id;
            documentData.id = this.currentDocId;
          }
        }
      } catch (error) {
        console.log("API error when autosaving, using localStorage:", error);
      }
      
      // If API save failed, save to localStorage
      if (!apiSaveSuccessful) {
        this.saveDocumentToLocalStorage(documentData);
      }
      
      // Update current document ID
      this.currentDocId = documentData.id;
      
      // Show success message
      this.updateSaveStatus('Saved');
    } catch (e) {
      console.error('Error in autosaveCurrentDocument:', e);
      this.updateSaveStatus('Autosave failed');
    }
  }
  
  createNewDocument() {
    // Clear current document ID and data
    this.currentDocId = null;
    this.currentDocData = null;
    
    // Clear title
    this.docTitleInput.value = 'Untitled Document';
    
    // Clear editor content
    this.editor.setContents([{ insert: '\n' }]);
    
    // Update active document in list
    this.renderDocumentsList();
    
    // Save the new document immediately to get an ID
    this.saveCurrentDocument();
  }
  
  exportCurrentDocument() {
    const content = this.editor.getContents();
    const title = this.docTitleInput.value || 'untitled-document';
    
    // Convert to markdown
    const converter = new QuillDeltaToMarkdownConverter(content);
    const markdown = converter.convert();
    
    // Create download link
    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title.replace(/\s+/g, '-').toLowerCase()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
  
  showLoginPrompt() {
    // Check if login prompt already exists
    if (document.querySelector('.tgdocs-login-prompt')) {
      return;
    }
    
    // Create login prompt
    const loginPrompt = document.createElement('div');
    loginPrompt.className = 'tgdocs-login-prompt';
    
    // Create login message
    const loginMessage = document.createElement('div');
    loginMessage.className = 'tgdocs-login-message';
    loginMessage.innerHTML = `
      <h2>Welcome to Text Generator Docs</h2>
      <p>Please sign in to continue:</p>
      <div class="tgdocs-login-options">
        <button id="login-with-google" class="tgdocs-login-button">Sign in with Google</button>
        <div class="tgdocs-login-divider">or</div>
        <div class="tgdocs-secret-input-container">
          <input type="text" id="secret-key-input" class="tgdocs-secret-input" placeholder="Enter your secret key">
          <button id="continue-with-secret" class="tgdocs-login-button">Continue</button>
        </div>
        <div class="tgdocs-login-divider">or</div>
        <button id="continue-offline" class="tgdocs-login-button">Continue Offline</button>
      </div>
    `;
    
    // Append login prompt to body
    document.body.appendChild(loginPrompt);
    loginPrompt.appendChild(loginMessage);
    
    // Add event listeners for login options
    document.getElementById('login-with-google').addEventListener('click', () => {
      // Redirect to Google login
      window.location.href = '/login';
    });
    
    document.getElementById('continue-with-secret').addEventListener('click', () => {
      const secretInput = document.getElementById('secret-key-input');
      const secret = secretInput.value.trim();
      
      if (secret) {
        // Store secret key
        this.secret = secret;
        this.setSecretKey(secret);
        
        // Set user ID based on secret
        this.userId = 'user_' + this.hashString(secret);
        
        // Remove login prompt
        loginPrompt.remove();
        
        // Load documents
        this.loadDocuments();
      } else {
        alert('Please enter a valid secret key');
      }
    });
    
    document.getElementById('continue-offline').addEventListener('click', () => {
      // Use anonymous user ID
      this.userId = this.anonymousUserId;
      
      // Remove login prompt
      loginPrompt.remove();
      
      // Load documents from localStorage
      this.loadDocumentsFromLocalStorage();
      this.renderDocumentsList();
      
      // Create new document if none exist
      if (this.documents.length === 0) {
        this.createNewDocument();
      } else {
        this.loadDocument(this.documents[0].id);
      }
    });
    
    // Focus on secret key input
    setTimeout(() => {
      document.getElementById('secret-key-input').focus();
    }, 100);
  }
  
  showMessage(message, type = 'success') {
    const snackbar = document.createElement('div');
    snackbar.className = `mdl-snackbar mdl-snackbar--${type}`;
    snackbar.textContent = message;
    document.body.appendChild(snackbar);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
      document.body.removeChild(snackbar);
    }, 3000);
  }
  
  handleTitleChange() {
    // Clear any existing debounce for title changes
    clearTimeout(this.titleChangeDebounceTimer);
    
    // Show saving indicator
    this.updateSaveStatus('Saving');
    
    // Debounce title changes (1 second)
    this.titleChangeDebounceTimer = setTimeout(() => {
      this.autosaveCurrentDocument();
    }, 1000);
  }
  
  getSecretKey() {
    // First check if there's a secret in the cookie
    const match = document.cookie.match(new RegExp('(^| )secret=([^;]+)'));
    if (match) return match[2];
    
    // Then check local storage
    const storedSecret = localStorage.getItem('textGeneratorSecret');
    if (storedSecret) return storedSecret;
    
    // Use default API key if none found
    return 'YIvld9Ih72n0BgfrW81mSEqm08Pm0nO2';
  }
  
  setSecretKey(secret) {
    // Store the secret key in both cookie and local storage
    document.cookie = `secret=${secret}; path=/; max-age=2592000`; // 30 days
    localStorage.setItem('textGeneratorSecret', secret);
    this.secret = secret;
  }
  
  showGenerateContentDialog() {
    // Create dialog for generation options
    const dialog = document.createElement('div');
    dialog.className = 'tgdocs-generate-dialog';
    
    // Create dialog content
    const dialogContent = document.createElement('div');
    dialogContent.className = 'tgdocs-generate-dialog-content';
    
    // Add title and description based on whether Claude is enabled
    const title = document.createElement('h3');
    title.textContent = this.useClaudeForBulk ? 'Generate Content with Claude' : 'Generate Content';
    dialogContent.appendChild(title);
    
    const description = document.createElement('p');
    if (this.useClaudeForBulk) {
      description.innerHTML = 'Enter a prompt below to generate high-quality content using Claude.<br>The AI will continue writing from your prompt.';
    } else {
      description.textContent = 'Enter a prompt below to generate content. The AI will continue writing from your prompt.';
    }
    dialogContent.appendChild(description);
    
    // Add textarea for prompt
    const promptTextarea = document.createElement('textarea');
    promptTextarea.id = 'generate-prompt';
    promptTextarea.className = 'tgdocs-generate-prompt';
    promptTextarea.placeholder = 'Describe what you want to generate...';
    
    // Get the current selection from the editor
    const selection = this.editor.getSelection();
    if (selection) {
      // Get the text before the cursor
      const text = this.editor.getText();
      const cursorPosition = selection.index;
      
      // Get the last 200 characters before the cursor
      const startPos = Math.max(0, cursorPosition - 200);
      const contextText = text.substring(startPos, cursorPosition);
      
      // Set the context text as the initial value of the textarea
      promptTextarea.value = contextText;
    }
    
    dialogContent.appendChild(promptTextarea);
    
    // Add model indicator if using Claude
    if (this.useClaudeForBulk) {
      const modelIndicator = document.createElement('div');
      modelIndicator.className = 'tgdocs-model-indicator';
      modelIndicator.innerHTML = '<span class="model-badge">Claude</span> Powered by Anthropic\'s advanced AI model';
      dialogContent.appendChild(modelIndicator);
    }
    
    // Add actions
    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'tgdocs-generate-actions';
    
    // Add cancel button
    const cancelButton = document.createElement('button');
    cancelButton.id = 'generate-cancel';
    cancelButton.className = 'mdl-button mdl-js-button';
    cancelButton.textContent = 'Cancel';
    actionsDiv.appendChild(cancelButton);
    
    // Add generate button
    const generateButton = document.createElement('button');
    generateButton.id = 'generate-submit';
    generateButton.className = 'mdl-button mdl-js-button mdl-button--raised mdl-button--colored';
    generateButton.textContent = 'Generate';
    actionsDiv.appendChild(generateButton);
    
    dialogContent.appendChild(actionsDiv);
    
    // Append dialog to body
    document.body.appendChild(dialog);
    dialog.appendChild(dialogContent);
    
    // Add event listeners
    document.getElementById('generate-cancel').addEventListener('click', () => {
      dialog.remove();
    });
    
    document.getElementById('generate-submit').addEventListener('click', () => {
      const prompt = document.getElementById('generate-prompt').value.trim();
      if (prompt) {
        this.insertLLMResponse(prompt, true);
        dialog.remove();
      }
    });
    
    // Focus on prompt input
    setTimeout(() => {
      document.getElementById('generate-prompt').focus();
    }, 100);
  }
  
  /**
   * Delete a document with undo functionality
   * @param {string} docId - The ID of the document to delete
   */
  deleteDocument(docId) {
    // Find the document
    const docIndex = this.documents.findIndex(d => d.id === docId);
    if (docIndex === -1) return;
    
    // Store document for potential restoration
    const docToDelete = this.documents[docIndex];
    
    // If this is the currently loaded document, create a new one
    const isCurrentDoc = this.currentDocId === docId;
    
    // Hide from UI immediately
    const docItem = this.documentsList.querySelector(`.tgdocs-document-item[data-id="${docId}"]`);
    if (docItem) {
      docItem.style.height = `${docItem.offsetHeight}px`;
      docItem.style.overflow = 'hidden';
      docItem.style.transition = 'all 0.3s';
      
      // Animate out
      setTimeout(() => {
        docItem.style.height = '0px';
        docItem.style.opacity = '0';
        docItem.style.padding = '0';
        docItem.style.margin = '0';
      }, 10);
    }
    
    // Remove from documents array
    this.documents.splice(docIndex, 1);
    
    // Update localStorage
    localStorage.setItem(`tgdocs-documents-${this.userId}`, JSON.stringify(this.documents));
    
    // If it was the current doc, create a new one
    if (isCurrentDoc) {
      this.createNewDocument();
    }
    
    // Create undo toast
    const toast = document.createElement('div');
    toast.className = 'tgdocs-undo-toast';
    toast.innerHTML = `
      <span>Document deleted</span>
      <button class="tgdocs-undo-button">UNDO</button>
    `;
    
    // Style the toast
    toast.style.position = 'fixed';
    toast.style.bottom = '20px';
    toast.style.left = '50%';
    toast.style.transform = 'translateX(-50%)';
    toast.style.backgroundColor = '#333';
    toast.style.color = 'white';
    toast.style.padding = '12px 24px';
    toast.style.borderRadius = '4px';
    toast.style.display = 'flex';
    toast.style.alignItems = 'center';
    toast.style.justifyContent = 'space-between';
    toast.style.gap = '12px';
    toast.style.boxShadow = '0 3px 6px rgba(0,0,0,0.16)';
    toast.style.zIndex = '2000';
    toast.style.animation = 'fadeIn 0.3s ease-out';
    
    // Style the undo button
    const undoBtn = toast.querySelector('.tgdocs-undo-button');
    undoBtn.style.backgroundColor = 'transparent';
    undoBtn.style.border = 'none';
    undoBtn.style.color = '#4caf50';
    undoBtn.style.fontWeight = 'bold';
    undoBtn.style.cursor = 'pointer';
    undoBtn.style.padding = '4px 8px';
    
    // Add fade-in animation
    const style = document.createElement('style');
    style.textContent = `
      @keyframes fadeIn {
        from { opacity: 0; transform: translate(-50%, 20px); }
        to { opacity: 1; transform: translate(-50%, 0); }
      }
    `;
    document.head.appendChild(style);
    
    // Append toast to body
    document.body.appendChild(toast);
    
    // Set timeout for deletion (8 seconds)
    const deleteTimeout = setTimeout(async () => {
      // Animate out
      toast.style.animation = 'fadeOut 0.3s ease-in forwards';
      setTimeout(() => {
        if (toast.parentNode) {
          document.body.removeChild(toast);
        }
      }, 300);
      
      // Attempt to delete via API
      try {
        const response = await fetch(`/api/docs/delete?id=${docId}`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        if (!response.ok) {
          console.warn(`API delete failed, document already removed from local storage`);
        }
      } catch (error) {
        console.warn('Error deleting document via API, already removed locally:', error);
      }
    }, 8000);
    
    // Handle undo button click
    undoBtn.addEventListener('click', () => {
      // Clear delete timeout
      clearTimeout(deleteTimeout);
      
      // Restore document in the array
      this.documents.splice(docIndex, 0, docToDelete);
      
      // Update localStorage
      localStorage.setItem(`tgdocs-documents-${this.userId}`, JSON.stringify(this.documents));
      
      // Re-render document list
      this.renderDocumentsList();
      
      // Reload the document if it was the current one
      if (isCurrentDoc) {
        this.loadDocument(docId);
      }
      
      // Remove toast
      toast.style.animation = 'fadeOut 0.3s ease-in forwards';
      setTimeout(() => {
        if (toast.parentNode) {
          document.body.removeChild(toast);
        }
      }, 300);
    });
    
    // Add fade-out animation
    style.textContent += `
      @keyframes fadeOut {
        from { opacity: 1; transform: translate(-50%, 0); }
        to { opacity: 0; transform: translate(-50%, 20px); }
      }
    `;
  }
}

/**
 * Utility class to convert Quill Delta format to Markdown
 */
class QuillDeltaToMarkdownConverter {
  constructor(delta) {
    this.delta = delta;
  }
  
  convert() {
    let markdown = '';
    const ops = this.delta.ops || [];
    
    ops.forEach(op => {
      if (op.insert) {
        if (typeof op.insert === 'string') {
          let text = op.insert;
          
          // Apply formatting based on attributes
          if (op.attributes) {
            if (op.attributes.bold) text = `**${text}**`;
            if (op.attributes.italic) text = `*${text}*`;
            if (op.attributes.code) text = '`' + text + '`';
            if (op.attributes.link) text = `[${text}](${op.attributes.link})`;
            // More formatting options...
          }
          
          markdown += text;
        } else if (op.insert.image) {
          markdown += `![Image](${op.insert.image})\n\n`;
        }
      }
    });
    
    return markdown;
  }
  
  initializeImageUpload() {
    // Handle paste events for image upload
    if (this.editor) {
      this.editor.root.addEventListener('paste', this.handlePaste.bind(this));
    }
    
    // Handle drag and drop for image upload
    if (this.editor) {
      this.editor.root.addEventListener('dragover', this.handleDragOver.bind(this));
      this.editor.root.addEventListener('drop', this.handleDrop.bind(this));
    }
  }
  
  handlePaste(event) {
    const items = event.clipboardData.items;
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item.type.indexOf('image') !== -1) {
        event.preventDefault();
        const file = item.getAsFile();
        this.uploadImage(file);
        break;
      }
    }
  }
  
  handleDragOver(event) {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'copy';
  }
  
  handleDrop(event) {
    event.preventDefault();
    const files = event.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      if (file.type.indexOf('image') !== -1) {
        this.uploadImage(file);
      }
    }
  }
  
  convertImageToWebP(file, quality = 85) {
    return new Promise((resolve, reject) => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      const img = new Image();
      
      img.onload = () => {
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
        
        canvas.toBlob((blob) => {
          if (blob) {
            resolve(blob);
          } else {
            reject(new Error('Failed to convert image to WebP'));
          }
        }, 'image/webp', quality / 100);
      };
      
      img.onerror = () => reject(new Error('Failed to load image'));
      img.src = URL.createObjectURL(file);
    });
  }
  
  async uploadImage(file) {
    try {
      // Convert to WebP
      const webpBlob = await this.convertImageToWebP(file, 85);
      
      // Create form data
      const formData = new FormData();
      formData.append('file', webpBlob, 'image.webp');
      
      // Upload to server
      const response = await fetch('/api/upload-image', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }
      
      const result = await response.json();
      
      if (result.success) {
        // Insert image markdown into editor
        const selection = this.editor.getSelection();
        const index = selection ? selection.index : this.editor.getLength();
        
        const imageMarkdown = `![Image](${result.url})`;
        this.editor.insertText(index, imageMarkdown);
        
        // Update save status
        this.updateSaveStatus('Image uploaded');
      } else {
        throw new Error('Upload failed');
      }
    } catch (error) {
      console.error('Error uploading image:', error);
      this.updateSaveStatus('Image upload failed');
    }
  }
}

/**
 * Utility class to convert Markdown to Quill Delta format
 * This handles common markdown from LLM responses
 */
class MarkdownToQuillDelta {
  constructor(markdown) {
    this.markdown = markdown;
  }
  
  convert() {
    if (!this.markdown) return { ops: [] };
    
    const delta = { ops: [] };
    let text = this.markdown;
    
    // Process markdown line by line
    const lines = text.split('\n');
    
    for (let i = 0; i < lines.length; i++) {
      let line = lines[i];
      
      // Handle headers
      const headerMatch = line.match(/^(#{1,6})\s+(.+)$/);
      if (headerMatch) {
        const headerLevel = headerMatch[1].length;
        const headerText = headerMatch[2];
        delta.ops.push({ 
          insert: headerText,
          attributes: { header: headerLevel }
        });
        delta.ops.push({ insert: '\n' });
        continue;
      }
      
      // Handle bullet lists
      const bulletMatch = line.match(/^(\s*)[*\-+]\s+(.+)$/);
      if (bulletMatch) {
        const indentLevel = bulletMatch[1].length;
        const listText = bulletMatch[2];
        delta.ops.push({ insert: listText });
        delta.ops.push({ 
          insert: '\n',
          attributes: { list: 'bullet' }
        });
        continue;
      }
      
      // Handle numbered lists
      const numberedMatch = line.match(/^(\s*)\d+\.\s+(.+)$/);
      if (numberedMatch) {
        const indentLevel = numberedMatch[1].length;
        const listText = numberedMatch[2];
        delta.ops.push({ insert: listText });
        delta.ops.push({ 
          insert: '\n',
          attributes: { list: 'ordered' }
        });
        continue;
      }
      
      // Handle blockquotes
      const quoteMatch = line.match(/^>\s+(.+)$/);
      if (quoteMatch) {
        const quoteText = quoteMatch[1];
        delta.ops.push({ insert: quoteText });
        delta.ops.push({ 
          insert: '\n',
          attributes: { blockquote: true }
        });
        continue;
      }
      
      // Handle code blocks
      if (line.startsWith('```')) {
        let language = line.substring(3).trim(); // Extract language if specified
        let codeBlock = '';
        let j = i + 1;
        
        // Collect all lines until the closing backticks
        while (j < lines.length && !lines[j].startsWith('```')) {
          codeBlock += lines[j] + '\n';
          j++;
        }
        
        // Apply syntax highlighting if language is specified and if we're using highlight.js
        if (language && window.hljs) {
          try {
            // Create a temporary element to apply highlight.js
            const tempEl = document.createElement('div');
            tempEl.innerHTML = `<pre><code class="language-${language}">${codeBlock}</code></pre>`;
            
            // Use highlight.js to add syntax highlighting
            window.hljs.highlightElement(tempEl.querySelector('code'));
            
            // The highlighted code now has spans with classes
            // We need to extract the HTML content for Quill
            delta.ops.push({ 
              insert: codeBlock,
              attributes: { 
                'code-block': true,
                'data-language': language
              }
            });
          } catch (e) {
            // Fallback if highlighting fails
            console.warn('Syntax highlighting failed:', e);
            delta.ops.push({ 
              insert: codeBlock,
              attributes: { 'code-block': true }
            });
          }
        } else {
          // Regular code block without specified language
          delta.ops.push({ 
            insert: codeBlock,
            attributes: { 'code-block': true }
          });
        }
        
        // Skip processed lines
        i = j < lines.length ? j : lines.length - 1;
        continue;
      }
      
      // Handle inline formatting
      // We need to process each line for bold, italic, code, etc.
      let processedLine = line;
      let formattedSegments = [];
      
      // A more comprehensive approach would involve parsing the markdown properly
      // This is a simplified version that handles basic inline formatting
      
      // Handle inline code
      let codeRegex = /`([^`]+)`/g;
      let codeMatch;
      let lastIndex = 0;
      
      while ((codeMatch = codeRegex.exec(processedLine)) !== null) {
        // Text before the code
        if (codeMatch.index > lastIndex) {
          formattedSegments.push({
            text: processedLine.substring(lastIndex, codeMatch.index),
            attributes: {}
          });
        }
        
        // The code itself
        formattedSegments.push({
          text: codeMatch[1],
          attributes: { code: true }
        });
        
        lastIndex = codeMatch.index + codeMatch[0].length;
      }
      
      // Add remaining text
      if (lastIndex < processedLine.length) {
        formattedSegments.push({
          text: processedLine.substring(lastIndex),
          attributes: {}
        });
      }
      
      // If no inline code was found, reset formatted segments
      if (formattedSegments.length === 0) {
        formattedSegments = [{ text: processedLine, attributes: {} }];
      }
      
      // Process bold and italic in each segment
      let newSegments = [];
      for (const segment of formattedSegments) {
        if (Object.keys(segment.attributes).length > 0 && segment.attributes.code) {
          // Skip formatting for code segments
          newSegments.push(segment);
          continue;
        }
        
        // Process bold (**text**)
        let boldSegments = [];
        let boldText = segment.text;
        let boldRegex = /\*\*([^*]+)\*\*/g;
        let boldMatch;
        let boldLastIndex = 0;
        
        while ((boldMatch = boldRegex.exec(boldText)) !== null) {
          // Text before the bold
          if (boldMatch.index > boldLastIndex) {
            boldSegments.push({
              text: boldText.substring(boldLastIndex, boldMatch.index),
              attributes: { ...segment.attributes }
            });
          }
          
          // The bold text
          boldSegments.push({
            text: boldMatch[1],
            attributes: { ...segment.attributes, bold: true }
          });
          
          boldLastIndex = boldMatch.index + boldMatch[0].length;
        }
        
        // Add remaining text
        if (boldLastIndex < boldText.length) {
          boldSegments.push({
            text: boldText.substring(boldLastIndex),
            attributes: { ...segment.attributes }
          });
        }
        
        // If no bold was found, use the original segment
        if (boldSegments.length === 0) {
          boldSegments = [segment];
        }
        
        // Process italic in each bold segment
        for (const boldSegment of boldSegments) {
          let italicText = boldSegment.text;
          let italicRegex = /\*([^*]+)\*/g;
          let italicMatch;
          let italicLastIndex = 0;
          let italicSegments = [];
          
          while ((italicMatch = italicRegex.exec(italicText)) !== null) {
            // Text before the italic
            if (italicMatch.index > italicLastIndex) {
              italicSegments.push({
                text: italicText.substring(italicLastIndex, italicMatch.index),
                attributes: { ...boldSegment.attributes }
              });
            }
            
            // The italic text
            italicSegments.push({
              text: italicMatch[1],
              attributes: { ...boldSegment.attributes, italic: true }
            });
            
            italicLastIndex = italicMatch.index + italicMatch[0].length;
          }
          
          // Add remaining text
          if (italicLastIndex < italicText.length) {
            italicSegments.push({
              text: italicText.substring(italicLastIndex),
              attributes: { ...boldSegment.attributes }
            });
          }
          
          // If no italic was found, use the bold segment
          if (italicSegments.length === 0) {
            italicSegments = [boldSegment];
          }
          
          // Add all processed segments
          newSegments.push(...italicSegments);
        }
      }
      
      // Add all formatted segments to the delta
      for (const segment of newSegments) {
        delta.ops.push({
          insert: segment.text,
          attributes: Object.keys(segment.attributes).length > 0 ? segment.attributes : undefined
        });
      }
      
      // Add newline
      delta.ops.push({ insert: '\n' });
    }
    
    return delta;
  }
}

// Add a function to the TextGeneratorDocs class to insert markdown
TextGeneratorDocs.prototype.insertMarkdown = function(markdown) {
  if (!markdown) return;
  
  // Convert markdown to delta
  const converter = new MarkdownToQuillDelta(markdown);
  const delta = converter.convert();
  
  // Get current selection
  const selection = this.editor.getSelection();
  if (selection) {
    // Insert at current cursor position
    this.editor.updateContents(
      new Delta().retain(selection.index).delete(selection.length).concat(delta)
    );
  } else {
    // Append to the end if no selection
    this.editor.updateContents(
      new Delta().retain(this.editor.getLength() - 1).concat(delta)
    );
  }
};

// Insert LLM response into the editor, handling markdown content
TextGeneratorDocs.prototype.insertLLMResponse = async function(prompt, isBulkGeneration = false) {
  if (!prompt || prompt.trim() === '') return;
  
  // Show loading indicator
  this.updateSaveStatus('Generating');
  
  // Save current cursor position
  const savedSelection = this.editor ? this.editor.getSelection() : null;
  
  try {
    // Determine if we should use Claude for this generation
    const useClaudeForThisRequest = isBulkGeneration && this.useClaudeForBulk;
    
    let data = null;
    
    if (useClaudeForThisRequest) {
      // Use Claude API for bulk generation
      this.updateSaveStatus('Using Claude for high-quality generation');
      
      // Generate content using the Claude API endpoint
      const response = await fetch('/api/v1/generate-large', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'secret': this.secret
        },
        body: JSON.stringify({
          text: prompt,
          number_of_results: 1,
          max_length: 1000,
          max_sentences: 20,
          min_probability: 0,
          stop_sequences: [],
          top_p: 0.9,
          top_k: 40,
          temperature: 0.8,
          repetition_penalty: 1.17,
          seed: 0,
          model: "claude-3-sonnet-20240229"
        })
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`Claude API Error (${response.status}): ${errorText}`);
        this.updateSaveStatus(`Generation failed: ${response.status} error`);
        return;
      }
      
      data = await response.json();
    } else {
      // Generate content using the standard API with adjusted settings
      const generationSettings = {...this.generationSettings};
      
      if (isBulkGeneration) {
        // For bulk generation, use appropriate settings
        generationSettings.min_probability = 0;
        generationSettings.max_length = 1000;
        generationSettings.max_sentences = 20;
        generationSettings.temperature = 0.8;
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
      
      data = await response.json();
    }
    
    // If no data or empty array, return null
    if (!data || !Array.isArray(data) || data.length === 0) {
      console.warn('Empty or invalid response from API');
      this.updateSaveStatus('Generation received empty response');
      return;
    }
    
    // Process the response correctly - extract the generated text that comes after the prompt
    const generatedText = data[0].generated_text.substring(prompt.length);
    
    if (generatedText && generatedText.trim() !== '') {
      // Make sure cursor position is still valid
      if (savedSelection && this.editor) {
        // Restore cursor position
        this.editor.setSelection(savedSelection);
      }
      
      // Check if the response contains markdown by looking for common markers
      const containsMarkdown = /(\#{1,6}\s+.+)|(\*\*.*?\*\*)|(\*[^\*]+?\*)|(\`[^\`]+?\`)|(\[[^\]]+?\]\([^\)]+?\))|(\>\s+.*?)|(^\s*[\*\-+]\s+.*?)|(^\s*\d+\.\s+.*?)|(\`\`\`[\s\S]*?\`\`\`)/m.test(generatedText);
      
      if (containsMarkdown) {
        // Get current cursor position again in case it changed
        const currentSelection = this.editor.getSelection();
        // Insert as markdown
        this.insertMarkdown(generatedText);
        // Restore focus to editor after markdown insertion
        if (this.editor) {
          this.editor.focus();
        }
      } else {
        // Insert as plain text at cursor position
        const currentSelection = this.editor.getSelection() || savedSelection;
        if (currentSelection) {
          this.editor.insertText(currentSelection.index, generatedText);
          // Set the cursor to the end of the inserted text
          this.editor.setSelection(currentSelection.index + generatedText.length, 0);
        } else {
          // Fallback to appending at the end if selection is lost
          this.editor.insertText(this.editor.getLength() - 1, generatedText);
        }
      }
      
      // Update save status
      this.updateSaveStatus('Content inserted');
      
      // Autosave after inserting content
      this.autosaveCurrentDocument();
    } else {
      this.updateSaveStatus('Generated empty content');
    }
  } catch (error) {
    console.error('Error generating content:', error);
    this.updateSaveStatus('Generation failed');
  }
}; 