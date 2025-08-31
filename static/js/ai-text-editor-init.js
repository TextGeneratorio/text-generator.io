/**
 * AI Text Editor Initialization
 * Handles the setup and initialization of the enhanced text editor
 * Works with the new authentication system (post-Firebase migration)
 */

(function() {
  'use strict';
  
  // Store user data globally
  let userData = null;
  let textEditor = null;
  let initialized = false;
  
  /**
   * Get user data from the new authentication system
   */
  function fetchUserData() {
    return fetch("/api/get-user/stripe-usage", {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({})
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Failed to get user data: ' + response.status);
      }
      return response.json();
    })
    .then(data => {
      userData = data;
      // Store in localStorage for caching
      if (data && data.secret) {
        localStorage.setItem('userData', JSON.stringify(data));
      }
      return data;
    })
    .catch(error => {
      console.error('Error fetching user data:', error);
      // Try to get from localStorage as fallback
      const stored = localStorage.getItem('userData');
      if (stored) {
        userData = JSON.parse(stored);
        return userData;
      }
      throw error;
    });
  }
  
  /**
   * Initialize the editor after getting user data
   */
  function initializeEditor() {
    // Prevent multiple initialization
    if (initialized) {
      console.log('Editor already initialized, skipping...');
      return;
    }
    
    // Check if required dependencies are loaded
    if (typeof Quill === 'undefined') {
      console.error('Quill editor is not loaded');
      showErrorMessage('Editor dependencies not loaded. Please refresh the page.');
      return;
    }
    
    if (typeof TextGeneratorDocs === 'undefined') {
      console.error('TextGeneratorDocs base class is not loaded');
      showErrorMessage('Editor dependencies not loaded. Please refresh the page.');
      return;
    }
    
    if (typeof EnhancedTextGeneratorDocs === 'undefined') {
      console.error('EnhancedTextGeneratorDocs class is not loaded');
      showErrorMessage('Editor dependencies not loaded. Please refresh the page.');
      return;
    }
    
    if (!userData || !userData.secret) {
      console.error('User authentication data not available');
      showErrorMessage('Authentication required. Please log in.');
      window.location.href = '/login';
      return;
    }
    
    // Configuration options for the editor
    const editorOptions = {
      apiUrl: '/api/v1/generate',
      secretKey: userData.secret,
      editorContainer: document.getElementById('editor'),
      suggestionElement: document.getElementById('autocomplete-suggestion'),
      documentsList: document.getElementById('documents-list'),
      newDocButton: document.getElementById('new-doc-btn'),
      saveDocButton: document.getElementById('save-doc-btn'),
      exportDocButton: document.getElementById('export-doc-btn'),
      docTitleInput: document.getElementById('doc-title'),
      generateContentButton: document.getElementById('generate-content-btn'),
      rewriteContentButton: document.getElementById('rewrite-content-btn'),
      
      // Generation settings
      generationSettings: {
        number_of_results: 1,
        max_length: 500,
        max_sentences: 10,
        min_probability: 0,
        stop_sequences: [],
        top_p: 0.9,
        top_k: 40,
        temperature: 0.75,
        repetition_penalty: 1.17,
        seed: 0
      },
      
      // Editor configuration
      enableAutocomplete: true,
      enableAutosave: true,
      debounceDelay: 500,
      autosaveInterval: 30000
      
      // Note: Quill configuration is handled by the base TextGeneratorDocs class
      // Don't pass modules or theme here to avoid conflicts
    };
    
    try {
      // Initialize the enhanced text editor
      textEditor = new EnhancedTextGeneratorDocs(editorOptions);
      
      // Make editor instance globally accessible for debugging
      window.aiTextEditor = textEditor;
      
      // Mark as initialized
      initialized = true;
      
      // Initialize the editor
      textEditor.init().then(() => {
        console.log('AI Text Editor initialized successfully');
        
        // Set up additional event handlers
        setupEventHandlers();
        
        // Set up keyboard shortcuts dialog if it exists
        setupKeyboardShortcutsDialog();
        
        // Load saved document if exists
        loadSavedDocument();
        
      }).catch(error => {
        console.error('Failed to initialize AI Text Editor:', error);
        showErrorMessage('Failed to initialize the editor. Please refresh the page.');
      });
      
    } catch (error) {
      console.error('Error creating text editor instance:', error);
      showErrorMessage('Error loading the editor. Please check your browser console.');
    }
  }
  
  /**
   * Set up additional event handlers for the editor
   */
  function setupEventHandlers() {
    // Toggle sidebar button handler
    const toggleSidebarBtn = document.getElementById('toggle-sidebar-btn');
    if (toggleSidebarBtn) {
      toggleSidebarBtn.addEventListener('click', () => {
        const sidebar = document.querySelector('.tgdocs-sidebar');
        if (sidebar) {
          sidebar.classList.toggle('collapsed');
        }
      });
    }
    
    // Document title change handler
    const docTitle = document.getElementById('doc-title');
    if (docTitle) {
      docTitle.addEventListener('change', (e) => {
        if (textEditor && textEditor.updateDocumentTitle) {
          textEditor.updateDocumentTitle(e.target.value);
        }
      });
    }
  }
  
  /**
   * Set up keyboard shortcuts dialog
   */
  function setupKeyboardShortcutsDialog() {
    const closeBtn = document.getElementById('close-shortcuts-btn');
    if (closeBtn) {
      closeBtn.addEventListener('click', function() {
        const dialog = document.getElementById('keyboard-shortcuts-dialog');
        if (dialog) {
          dialog.style.display = 'none';
        }
      });
    }
  }
  
  /**
   * Load saved document from localStorage or server
   */
  function loadSavedDocument() {
    if (!textEditor) return;
    
    // Check for document ID in URL params
    const urlParams = new URLSearchParams(window.location.search);
    const docId = urlParams.get('doc');
    
    if (docId) {
      // Load specific document
      if (textEditor.loadDocument) {
        textEditor.loadDocument(docId);
      }
    } else {
      // Check for last edited document in localStorage
      const lastDocId = localStorage.getItem('lastEditedDocument');
      if (lastDocId && textEditor.loadDocument) {
        textEditor.loadDocument(lastDocId);
      } else if (textEditor.createNewDocument) {
        // Create new document
        textEditor.createNewDocument();
      }
    }
  }
  
  /**
   * Show error message to user
   */
  function showErrorMessage(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    errorDiv.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: #f44336;
      color: white;
      padding: 12px 24px;
      border-radius: 4px;
      box-shadow: 0 2px 5px rgba(0,0,0,0.2);
      z-index: 10000;
      font-family: 'Roboto', 'Helvetica', 'Arial', sans-serif;
    `;
    
    document.body.appendChild(errorDiv);
    
    // Remove after 5 seconds
    setTimeout(() => {
      errorDiv.remove();
    }, 5000);
  }
  
  /**
   * Main initialization function
   */
  function init() {
    // First fetch user data, then initialize editor
    fetchUserData()
      .then(() => {
        initializeEditor();
      })
      .catch(error => {
        console.error('Failed to initialize:', error);
        showErrorMessage('Authentication failed. Redirecting to login...');
        setTimeout(() => {
          window.location.href = '/login';
        }, 2000);
      });
  }
  
  // Wait for DOM to be ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    // DOM is already loaded
    init();
  }
  
})();