/**
 * Text Generator Docs - A Medium-style WYSIWYG editor with AI-powered autocomplete
 */

// Import Quill Delta for operations
const Delta = Quill.import('delta');

const TGDocsTableUtils = (() => {
  function normalizeClipboardText(text) {
    if (typeof text !== 'string') return '';
    return text
      .replace(/\r\n/g, '\n')
      .replace(/\r/g, '\n')
      .replace(/^\n+|\n+$/g, '');
  }

  function parseCsvLine(line) {
    const cells = [];
    let current = '';
    let inQuotes = false;

    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      const next = line[i + 1];

      if (char === '"' && inQuotes && next === '"') {
        current += '"';
        i++;
      } else if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === ',' && !inQuotes) {
        cells.push(current);
        current = '';
      } else {
        current += char;
      }
    }

    cells.push(current);
    return cells;
  }

  function normalizeRows(rows) {
    const meaningfulRows = rows
      .map(row => row.map(cell => String(cell == null ? '' : cell).replace(/\u00a0/g, ' ').trim()))
      .filter(row => row.some(cell => cell.length > 0));

    if (meaningfulRows.length === 0) return null;

    const maxColumns = Math.max(...meaningfulRows.map(row => row.length));
    const hasEnoughCellData = meaningfulRows.some(row => row.filter(cell => cell.length > 0).length >= 2);

    if (maxColumns < 2 || !hasEnoughCellData) return null;

    return meaningfulRows.map(row => {
      const paddedRow = row.slice(0, maxColumns);
      while (paddedRow.length < maxColumns) {
        paddedRow.push('');
      }
      return paddedRow;
    });
  }

  function parseDelimitedRows(text) {
    const normalized = normalizeClipboardText(text);
    if (!normalized.trim()) return null;

    const lines = normalized
      .split('\n')
      .filter(line => line.trim().length > 0 || line.includes('\t'));

    if (lines.length === 0) return null;

    if (lines.some(line => line.includes('\t'))) {
      return normalizeRows(lines.map(line => line.split('\t')));
    }

    if (lines.length < 2 || !lines.every(line => line.includes(','))) {
      return null;
    }

    const csvRows = lines.map(parseCsvLine);
    if (!csvRows.every(row => row.length >= 2)) {
      return null;
    }

    return normalizeRows(csvRows);
  }

  function cellLooksNumeric(cell) {
    return /^[\s$+-]*\d[\d,]*(?:\.\d+)?%?\s*$/.test(cell);
  }

  function shouldUseFirstRowAsHeader(rows) {
    if (!rows || rows.length < 2) return false;

    const firstRow = rows[0];
    const bodyRows = rows.slice(1);
    const firstRowHasText = firstRow.some(cell => /[A-Za-z]/.test(cell));
    const firstNumericCells = firstRow.filter(cellLooksNumeric).length;
    const bodyHasNumericCell = bodyRows.some(row => row.some(cellLooksNumeric));

    return firstRowHasText && firstNumericCells <= Math.floor(firstRow.length / 2) && bodyHasNumericCell;
  }

  function sanitizeMarkdownCell(cell) {
    return String(cell == null ? '' : cell)
      .replace(/\s+/g, ' ')
      .replace(/\|/g, '\\|')
      .trim();
  }

  function formatMarkdownRow(cells) {
    return `| ${cells.map(sanitizeMarkdownCell).join(' | ')} |`;
  }

  function buildMarkdownTableFromRows(rows, options = {}) {
    const normalizedRows = normalizeRows(rows);
    if (!normalizedRows) return '';

    const columnCount = normalizedRows[0].length;
    const useFirstRowAsHeader = typeof options.useFirstRowAsHeader === 'boolean'
      ? options.useFirstRowAsHeader
      : shouldUseFirstRowAsHeader(normalizedRows);
    const header = useFirstRowAsHeader
      ? normalizedRows[0]
      : Array.from({ length: columnCount }, (_, index) => `Column ${index + 1}`);
    const bodyRows = useFirstRowAsHeader ? normalizedRows.slice(1) : normalizedRows;
    const rowsToRender = bodyRows.length > 0 ? bodyRows : [Array(columnCount).fill('')];
    const separator = Array(columnCount).fill('---');

    return [
      formatMarkdownRow(header),
      formatMarkdownRow(separator),
      ...rowsToRender.map(formatMarkdownRow)
    ].join('\n') + '\n';
  }

  function buildBlankMarkdownTable(columns = 3, rows = 2) {
    const columnCount = Math.max(2, columns);
    const rowCount = Math.max(1, rows);
    const header = Array.from({ length: columnCount }, (_, index) => `Column ${index + 1}`);
    const separator = Array(columnCount).fill('---');
    const bodyRows = Array.from({ length: rowCount }, () => Array(columnCount).fill(''));

    return [
      formatMarkdownRow(header),
      formatMarkdownRow(separator),
      ...bodyRows.map(formatMarkdownRow)
    ].join('\n') + '\n';
  }

  function convertDelimitedTextToMarkdownTable(text) {
    const rows = parseDelimitedRows(text);
    if (!rows) return '';
    return buildMarkdownTableFromRows(rows);
  }

  function getMarkdownTableCells(line) {
    const trimmed = String(line || '').trim();
    if (!trimmed.includes('|')) return [];
    return trimmed
      .replace(/^\|/, '')
      .replace(/\|$/, '')
      .split('|')
      .map(cell => cell.trim());
  }

  function isMarkdownTableRow(line) {
    const cells = getMarkdownTableCells(line);
    return cells.length >= 2;
  }

  function isMarkdownTableSeparator(line) {
    const cells = getMarkdownTableCells(line);
    return cells.length >= 2 && cells.every(cell => /^:?-{3,}:?$/.test(cell));
  }

  function containsMarkdownTable(text) {
    const lines = normalizeClipboardText(text).split('\n');
    for (let i = 0; i < lines.length - 1; i++) {
      if (isMarkdownTableRow(lines[i]) && isMarkdownTableSeparator(lines[i + 1])) {
        return true;
      }
    }
    return false;
  }

  return {
    buildBlankMarkdownTable,
    buildMarkdownTableFromRows,
    containsMarkdownTable,
    convertDelimitedTextToMarkdownTable,
    isMarkdownTableRow,
    isMarkdownTableSeparator,
    parseDelimitedRows
  };
})();

if (typeof globalThis !== 'undefined') {
  globalThis.TGDocsTableUtils = TGDocsTableUtils;
}

class TextGeneratorDocs {
  // Auto-title the document after this much idle time following an edit
  static get AUTO_TITLE_IDLE_MS() { return 6000; }
  // ...but only once there is enough written to name
  static get AUTO_TITLE_MIN_CHARS() { return 120; }
  // Autosave debounce - short enough that other open pages stay live
  static get AUTOSAVE_DEBOUNCE_MS() { return 2500; }

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
    this.insertTableButton = safeGetElement(options.insertTableButton);
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
      seed: 0,
      enable_thinking: false
    };
    
    this.currentDocId = null;
    this.currentDocData = null;
    this.documents = [];
    this.debounceTimeout = null;
    // Unique per tab so live-sync events from this tab can be ignored locally
    this.clientId = 'tab_' + Math.random().toString(36).slice(2) + '_' + Date.now();
    this.isApplyingRemoteChange = false;
    this.autoTitlePending = false;
    this.isGenerating = false;
    this.suggestionText = '';
    this.suggestionActive = false;
    // Use the secretKey from options if provided, otherwise fall back to getSecretKey()
    this.secret = options.secretKey || this.getSecretKey();
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

    // Defer to a microtask so subclass constructors finish before init runs
    this.initPromise = Promise.resolve().then(() => this.init());
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
    // Guard against double initialization (constructor + explicit init() call)
    if (this._initStarted) return this.initPromise;
    this._initStarted = true;

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
    
    // Check subscription status and enforce premium restrictions
    await this.checkSubscriptionStatus();
    
    // Live updates across every open page of the editor
    this.initLiveSync();

    // Load documents if authenticated
    if ((isAuthenticated || this.userId) && this.documentsList) {
      await this.loadDocuments();
    }
  }

  //------------------------------------------------------
  // Live sync (multi-tab / multi-device)
  //------------------------------------------------------

  initLiveSync() {
    // Same-browser tabs: instant, no server round trip
    try {
      if (typeof BroadcastChannel !== 'undefined') {
        this.syncChannel = new BroadcastChannel('tgdocs-live');
        this.syncChannel.onmessage = (event) => this.handleRemoteUpdate(event.data);
      }
    } catch (e) {
      console.warn('BroadcastChannel unavailable, falling back to SSE only:', e);
    }

    // Other browsers/devices: server-sent events
    this.connectDocumentEvents();

    // Flush pending work when the tab is hidden or closed
    const flush = () => {
      if (this.currentDocId && this.hasUnsavedChanges) {
        this.autosaveCurrentDocument({ keepalive: true });
      }
    };
    window.addEventListener('pagehide', flush);
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') flush();
    });
  }

  connectDocumentEvents() {
    if (typeof EventSource === 'undefined') return;
    try {
      if (this.eventSource) {
        this.eventSource.close();
      }
      this.eventSource = new EventSource('/api/docs/events');
      this.eventSource.onmessage = (event) => {
        try {
          this.handleRemoteUpdate(JSON.parse(event.data));
        } catch (e) {
          console.warn('Bad live-sync payload:', e);
        }
      };
      this.eventSource.onerror = () => {
        // Reconnect with a bounded backoff
        if (this.eventSource) {
          this.eventSource.close();
          this.eventSource = null;
        }
        this.sseBackoff = Math.min((this.sseBackoff || 2000) * 2, 60000);
        clearTimeout(this.sseReconnectTimer);
        this.sseReconnectTimer = setTimeout(() => this.connectDocumentEvents(), this.sseBackoff);
      };
      this.eventSource.onopen = () => {
        this.sseBackoff = 2000;
      };
    } catch (e) {
      console.warn('Could not open live document stream:', e);
    }
  }

  /**
   * Broadcast a document change so other open pages update live
   */
  broadcastDocumentUpdate(documentData) {
    if (!this.syncChannel || !documentData || !documentData.id) return;
    try {
      this.syncChannel.postMessage({
        type: 'doc-update',
        client_id: this.clientId,
        document: {
          id: documentData.id,
          title: documentData.title,
          content: documentData.content,
          updated_at: documentData.updatedAt || new Date().toISOString()
        }
      });
    } catch (e) {
      console.warn('Failed to broadcast document update:', e);
    }
  }

  /**
   * Apply an update that came from another tab/device
   */
  handleRemoteUpdate(payload) {
    if (!payload || payload.client_id === this.clientId) return;

    if (payload.type === 'doc-delete') {
      this.documents = this.documents.filter(d => d.id !== payload.id);
      if (this.documentsList) this.renderDocumentsList();
      return;
    }

    const doc = payload.document;
    if (!doc || !doc.id) return;

    // Keep the sidebar list fresh
    const idx = this.documents.findIndex(d => d.id === doc.id);
    if (idx >= 0) {
      this.documents[idx] = { ...this.documents[idx], ...doc, updatedAt: doc.updated_at };
    } else {
      this.documents.unshift({ ...doc, updatedAt: doc.updated_at });
    }

    if (doc.id !== this.currentDocId) {
      if (this.documentsList) this.renderDocumentsList();
      return;
    }

    // Don't clobber what the user is typing right now in this tab
    if (this.hasUnsavedChanges && Date.now() - (this.lastLocalEditAt || 0) < 3000) {
      return;
    }

    this.applyRemoteContent(doc);
    if (this.documentsList) this.renderDocumentsList();
  }

  applyRemoteContent(doc) {
    if (!this.editor) return;
    try {
      if (doc.title !== undefined && this.docTitleInput && this.docTitleInput.value !== doc.title) {
        this.docTitleInput.value = doc.title || '';
      }
      if (!doc.content) return;

      const incoming = typeof doc.content === 'string' ? JSON.parse(doc.content) : doc.content;
      const current = JSON.stringify(this.editor.getContents());
      if (current === JSON.stringify(incoming)) return;

      // Preserve the caret across the remote update
      const selection = this.editor.getSelection();
      this.isApplyingRemoteChange = true;
      this.editor.setContents(incoming, 'silent');
      if (selection) {
        const max = this.editor.getLength() - 1;
        this.editor.setSelection(Math.min(selection.index, max), selection.length || 0, 'silent');
      }
      this.updateSaveStatus('Updated from another tab');
    } catch (e) {
      console.warn('Could not apply remote document content:', e);
    } finally {
      this.isApplyingRemoteChange = false;
    }
  }

  //------------------------------------------------------
  // Last-opened document tracking
  //------------------------------------------------------

  lastDocStorageKey() {
    return `tgdocs-last-doc-${this.userId || 'anon'}`;
  }

  rememberLastDocument(docId) {
    if (!docId) return;
    try {
      localStorage.setItem(this.lastDocStorageKey(), docId);
      // Legacy key kept in sync for older code paths
      localStorage.setItem('lastEditedDocument', docId);
    } catch (e) {
      console.warn('Could not persist last document id:', e);
    }
  }

  getLastDocumentId() {
    try {
      return localStorage.getItem(this.lastDocStorageKey()) || localStorage.getItem('lastEditedDocument');
    } catch (e) {
      return null;
    }
  }
  
  initEditor() {
    try {
      // Check if Quill has already been initialized on this element
      if (this.editorContainer.classList.contains('ql-container')) {
        console.warn('Quill already initialized on this container, skipping...');
        // Get the existing Quill instance if needed
        const existingQuill = Quill.find(this.editorContainer);
        if (existingQuill) {
          this.editor = existingQuill;
          return;
        }
      }
      
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

    if (this.insertTableButton) {
      if (!this._boundInsertEmptyMarkdownTable) {
        this._boundInsertEmptyMarkdownTable = () => {
          this.insertEmptyMarkdownTable();
        };
      }
      this.insertTableButton.removeEventListener('click', this._boundInsertEmptyMarkdownTable);
      this.insertTableButton.addEventListener('click', this._boundInsertEmptyMarkdownTable);
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
            if (userData.secret) {
              this.secret = userData.secret;
              this.setSecretKey(userData.secret);
            }
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
  
  async checkSubscriptionStatus() {
    try {
      // Check if user is subscribed
      const isSubscribed = await isUserSubscribed();
      
      if (!isSubscribed) {
        // User is not subscribed, disable AI features
        this.disableAIFeatures();
      } else {
        // User is subscribed, enable AI features
        this.enableAIFeatures();
      }
    } catch (error) {
      console.error('Error checking subscription status:', error);
      // On error, disable AI features to be safe
      this.disableAIFeatures();
    }
  }
  
  disableAIFeatures() {
    // Disable AI generation buttons
    if (this.generateContentButton) {
      this.generateContentButton.disabled = true;
      this.generateContentButton.title = 'Premium feature - Subscribe to access';
    }
    
    // Add click handlers to show subscription modal
    if (this.generateContentButton) {
      this.generateContentButton.addEventListener('click', (e) => {
        e.preventDefault();
        if (window.subscriptionModal) { subscriptionModal.show(); };
      });
    }
    
    // Disable autocomplete by setting a flag
    this.aiDisabled = true;
  }
  
  enableAIFeatures() {
    // Enable AI generation buttons
    if (this.generateContentButton) {
      this.generateContentButton.disabled = false;
      this.generateContentButton.title = 'Write from Cursor (Ctrl+Space)';
    }
    
    // Enable autocomplete
    this.aiDisabled = false;
  }
  
  handleEditorChange(delta, oldDelta, source) {
    // If editor isn't initialized, don't proceed
    if (!this.editor) {
      return;
    }
    
    if (source !== 'user') return;
    if (this.isApplyingRemoteChange) return;

    this.hasUnsavedChanges = true;
    this.lastLocalEditAt = Date.now();

    // AI naming once enough has been written
    this.scheduleAutoTitle();

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

    // Debounce autosave - fast so other open pages see the change live
    this.autosaveTimeout = setTimeout(() => {
      this.autosaveCurrentDocument();
    }, TextGeneratorDocs.AUTOSAVE_DEBOUNCE_MS);
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
      // Check if AI features are disabled due to subscription
      if (this.aiDisabled) {
        return;
      }
      
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
      text: prompt,
      enable_thinking: false
    };
    
    try {
      // Determine the correct API endpoint based on environment
      const isLocal = window.location.hostname.includes('localhost') || 
                     window.location.hostname.includes('127.0.0.1') || 
                     window.location.hostname.includes('0.0.0.0');
      const apiEndpoint = isLocal ? '/api/v1/generate' : 'https://api.text-generator.io/api/v1/generate';
      
      // Use the correct API endpoint for text generation with secret key in header
      const response = await fetch(apiEndpoint, {
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
      
      // Newest first so "most recent" is a meaningful fallback
      this.documents.sort((a, b) => {
        const at = new Date(a.updatedAt || a.updated_at || a.createdAt || 0).getTime();
        const bt = new Date(b.updatedAt || b.updated_at || b.createdAt || 0).getTime();
        return bt - at;
      });

      this.renderDocumentsList();

      // Which document to reopen: ?doc= wins, then the remembered one,
      // then the most recently updated.
      const urlDocId = new URLSearchParams(window.location.search).get('doc');
      const rememberedId = this.getLastDocumentId();

      // Clean up the backlog of blank "Untitled Document" rows from older
      // builds first, so the pick below can't land on a doc being deleted.
      await this.pruneEmptyDocuments(urlDocId || rememberedId);

      const exists = (id) => id && this.documents.some(d => d.id === id);

      let targetId = null;
      if (exists(urlDocId)) targetId = urlDocId;
      else if (exists(rememberedId)) targetId = rememberedId;
      else if (this.documents.length > 0) targetId = this.documents[0].id;

      if (targetId) {
        await this.loadDocument(targetId);
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

  /**
   * Ask the server to drop untitled+empty documents left over from older builds
   */
  async pruneEmptyDocuments(keepId = null) {
    const keep = keepId || this.currentDocId || null;
    const blank = this.documents.filter(d =>
      d.id !== keep && (!d.title || d.title === 'Untitled Document') && this.isBlankContent(d.content)
    );
    if (blank.length === 0) return;

    try {
      const response = await fetch('/api/docs/prune-empty', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keep })
      });
      if (!response.ok) return;
      const result = await response.json();
      const removed = new Set(result.ids || []);
      if (removed.size === 0) return;
      this.documents = this.documents.filter(d => !removed.has(d.id));
      this.renderDocumentsList();
      console.log(`Removed ${removed.size} empty untitled documents`);
    } catch (e) {
      console.log('Could not prune empty documents:', e);
    }
  }

  /**
   * True when a stored Quill delta contains no actual text
   */
  isBlankContent(content) {
    if (!content) return true;
    try {
      const delta = typeof content === 'string' ? JSON.parse(content) : content;
      const ops = Array.isArray(delta) ? delta : (delta.ops || []);
      // An embed (image, video, ...) counts as real content
      if (ops.some(op => op && op.insert !== undefined && typeof op.insert !== 'string')) {
        return false;
      }
      const text = ops
        .map(op => (op && typeof op.insert === 'string' ? op.insert : ''))
        .join('');
      return text.trim().length === 0;
    } catch (e) {
      return String(content).trim().length === 0;
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
    if (!this.documentsList) return;

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
      date.textContent = this.formatDate(doc.updatedAt || doc.updated_at || doc.createdAt);
      
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
          this.hasUnsavedChanges = false;
          this.rememberLastDocument(docId);

          // Update title
          this.docTitleInput.value = docData.title || '';

          // Update editor content
          if (docData.content) {
            this.editor.setContents(JSON.parse(docData.content), 'silent');
          } else {
            this.editor.setContents([{ insert: '\n' }], 'silent');
          }

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
        this.hasUnsavedChanges = false;
        this.rememberLastDocument(docId);

        // Update title
        this.docTitleInput.value = doc.title || '';

        // Update editor content
        if (doc.content) {
          this.editor.setContents(JSON.parse(doc.content), 'silent');
        } else {
          this.editor.setContents([{ insert: '\n' }], 'silent');
        }

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

    // Never persist an untitled, empty document - that is what created the
    // pile of "Untitled Document" entries on every page load.
    if (!this.currentDocId && this.isBlankContent(content) && title === 'Untitled Document') {
      this.updateSaveStatus('');
      return;
    }

    const documentData = {
      title,
      content,
      client_id: this.clientId
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
          if (result.skipped === 'empty') {
            // Server agreed there was nothing worth storing
            this.updateSaveStatus('');
            return;
          }
          apiSaveSuccessful = true;

          // Update current document ID if it was a new document
          if (!this.currentDocId) {
            this.currentDocId = result.id || documentData.id;
            documentData.id = this.currentDocId;
          }
          documentData.updatedAt = result.updated_at || new Date().toISOString();
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
        if (idx >= 0) this.documents[idx] = { ...this.documents[idx], ...documentData };
        else this.documents.unshift(documentData);
        localStorage.setItem(`tgdocs-documents-${this.userId}`, JSON.stringify(this.documents));
      }

      // Show success message
      this.updateSaveStatus('Saved');

      // Update current document ID
      this.currentDocId = documentData.id;
      this.hasUnsavedChanges = false;
      this.rememberLastDocument(this.currentDocId);
      this.broadcastDocumentUpdate(documentData);

      // Refresh documents list
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
  
  async autosaveCurrentDocument(options = {}) {
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

      // Don't create a row for an untitled, empty document
      if (!this.currentDocId && this.isBlankContent(content) && title === 'Untitled Document') {
        this.updateSaveStatus('');
        return;
      }

      const documentData = {
        title,
        content,
        client_id: this.clientId
      };

      if (this.currentDocId) {
        documentData.id = this.currentDocId;
      } else {
        // Generate a new ID if this is a new document
        documentData.id = 'doc_' + Date.now();
      }

      // Try to autosave to API first
      let apiSaveSuccessful = false;
      const useUnloadTransport = Boolean(options.keepalive);
      const requestBody = JSON.stringify(documentData);
      
      try {
        if (useUnloadTransport && typeof navigator !== 'undefined' && navigator.sendBeacon) {
          const blob = new Blob([requestBody], { type: 'application/json' });
          if (navigator.sendBeacon('/api/docs/autosave', blob)) {
            apiSaveSuccessful = true;
            documentData.updatedAt = new Date().toISOString();
            try {
              this.saveDocumentToLocalStorage(documentData);
            } catch (backupError) {
              console.warn('Could not keep local autosave backup:', backupError);
            }
          }
        }

        if (!apiSaveSuccessful) {
          const autosaveRequest = {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: requestBody
          };
          if (useUnloadTransport) {
            autosaveRequest.keepalive = true;
          }

          // First try the autosave endpoint
          let response = await fetch('/api/docs/autosave', autosaveRequest);
          
          // If autosave endpoint fails, try the regular save endpoint
          if (!response.ok && !useUnloadTransport) {
            response = await fetch('/api/docs/save', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json'
              },
              body: requestBody
            });
          }
          
          if (response.ok) {
            const result = await response.json();
            if (result.skipped === 'empty') {
              this.updateSaveStatus('');
              return;
            }
            apiSaveSuccessful = true;

            // Update current document ID if it was a new document
            if (!this.currentDocId) {
              this.currentDocId = result.id || documentData.id;
              documentData.id = this.currentDocId;
            }
            documentData.updatedAt = result.updated_at || new Date().toISOString();
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
      this.hasUnsavedChanges = false;
      this.rememberLastDocument(this.currentDocId);

      // Keep the sidebar and every other open page in sync
      const idx = this.documents.findIndex(d => d.id === documentData.id);
      if (idx >= 0) this.documents[idx] = { ...this.documents[idx], ...documentData };
      else this.documents.unshift(documentData);
      if (this.documentsList) this.renderDocumentsList();
      this.broadcastDocumentUpdate(documentData);

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
    this.hasUnsavedChanges = false;
    this.autoTitleDone = false;
    clearTimeout(this.autoTitleTimeout);

    // Leave the title blank so the AI can name it once there's something to name
    this.docTitleInput.value = '';
    this.docTitleInput.placeholder = 'Untitled Document';

    // Clear editor content
    this.editor.setContents([{ insert: '\n' }], 'silent');

    // Update active document in list
    this.renderDocumentsList();

    // Deliberately NOT saved here - the document is persisted on the first
    // real edit, so opening the editor no longer creates a blank row.
    this.updateSaveStatus('');
  }

  //------------------------------------------------------
  // Automatic AI titling
  //------------------------------------------------------

  /**
   * True when the title is still the placeholder and can be replaced
   */
  titleIsAuto() {
    const title = (this.docTitleInput && this.docTitleInput.value || '').trim();
    return title === '' || title === 'Untitled Document';
  }

  /**
   * Schedule an AI-generated title once the user has written enough.
   * Called from the editor change handlers.
   */
  scheduleAutoTitle() {
    if (this.autoTitleDone || this.userEditedTitle) return;
    if (!this.titleIsAuto()) return;

    clearTimeout(this.autoTitleTimeout);
    this.autoTitleTimeout = setTimeout(() => {
      this.generateDocumentTitle();
    }, TextGeneratorDocs.AUTO_TITLE_IDLE_MS);
  }

  /**
   * Name the document with the text-generator model based on what was written
   */
  async generateDocumentTitle(force = false) {
    if (!this.editor || !this.docTitleInput) return;
    if (this.autoTitlePending) return;
    if (!force && (this.autoTitleDone || this.userEditedTitle || !this.titleIsAuto())) return;

    const text = this.editor.getText().trim();
    if (text.length < TextGeneratorDocs.AUTO_TITLE_MIN_CHARS) return;

    this.autoTitlePending = true;
    try {
      // Without AI access, name it from the opening line rather than
      // burning a request that will be rejected
      if (this.aiDisabled) {
        const fallback = this.fallbackTitle(text);
        if (fallback) {
          this.docTitleInput.value = fallback;
          this.autoTitleDone = true;
          await this.autosaveCurrentDocument();
        }
        return;
      }

      const excerpt = text.slice(0, 1200);
      const title = await this.fetchGeneratedTitle(excerpt);
      const cleaned = this.cleanGeneratedTitle(title) || this.fallbackTitle(text);

      if (cleaned && (force || this.titleIsAuto())) {
        this.docTitleInput.value = cleaned;
        this.autoTitleDone = true;
        this.showMessage(`Named "${cleaned}"`);
        await this.autosaveCurrentDocument();
      }
    } catch (e) {
      console.log('Auto title generation failed, using fallback:', e);
      const fallback = this.fallbackTitle(this.editor.getText().trim());
      if (fallback && this.titleIsAuto()) {
        this.docTitleInput.value = fallback;
        this.autoTitleDone = true;
        await this.autosaveCurrentDocument();
      }
    } finally {
      this.autoTitlePending = false;
    }
  }

  /**
   * Ask the text-generator model for a short document title
   */
  async fetchGeneratedTitle(excerpt) {
    const prompt =
      'Write a short, specific title (3 to 8 words) for the document below. ' +
      'Reply with the title only, no quotes and no explanation.\n\n' +
      'Document:\n' + excerpt + '\n\nTitle:';

    const response = await fetch('/api/v1/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'secret': this.secret
      },
      body: JSON.stringify({
        text: prompt,
        number_of_results: 1,
        max_length: 24,
        max_sentences: 1,
        min_probability: 0,
        stop_sequences: ['\n'],
        top_p: 0.9,
        top_k: 40,
        temperature: 0.5,
        repetition_penalty: 1.1,
        seed: 0,
        enable_thinking: false
      })
    });

    if (!response.ok) {
      throw new Error(`Title generation failed: ${response.status}`);
    }

    const data = await response.json();
    if (!Array.isArray(data) || data.length === 0) {
      throw new Error('Empty title response');
    }

    const generated = data[0].generated_text || '';
    // The API echoes the prompt back, so take only the continuation
    return generated.startsWith(prompt) ? generated.slice(prompt.length) : generated;
  }

  /**
   * Normalize a model-generated title into something usable as a filename
   */
  cleanGeneratedTitle(raw) {
    if (!raw) return '';
    let title = String(raw).split('\n').map(l => l.trim()).find(l => l.length > 0) || '';
    title = title.replace(/^["'`*#\s]+|["'`*\s]+$/g, '');
    title = title.replace(/^(title|document title)\s*[:\-]\s*/i, '');
    title = title.replace(/[\r\n\t]+/g, ' ').replace(/\s{2,}/g, ' ').trim();
    title = title.replace(/[.,;:]+$/, '');
    if (title.length > 70) {
      title = title.slice(0, 70).replace(/\s+\S*$/, '').trim();
    }
    // Reject degenerate output
    if (title.length < 3 || /^untitled/i.test(title)) return '';
    return title;
  }

  /**
   * Deterministic title from the first line of text, used when the model fails
   */
  fallbackTitle(text) {
    if (!text) return '';
    const firstLine = text.split('\n').map(l => l.trim()).find(l => l.length > 0) || '';
    const words = firstLine.split(/\s+/).filter(Boolean).slice(0, 8);

    // Don't leave the title dangling on a joining word
    const trailing = /^(the|a|an|and|or|but|of|to|in|on|for|with|that|which|is|was|at|by|from)$/i;
    while (words.length > 1 && trailing.test(words[words.length - 1])) {
      words.pop();
    }

    const title = words.join(' ').replace(/[.,;:]+$/, '').trim();
    return title.length >= 3 ? title : '';
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
    if (typeof showLoginModal === 'function') {
      const subtitle = document.querySelector('#login-modal .auth-modal-subtitle');
      if (subtitle) {
        subtitle.textContent = 'Sign in to save and sync your documents';
      }
      showLoginModal();
      return;
    }

    window.location.href = '/login';
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

    // A title the user typed themselves wins over AI naming
    if (!this.titleIsAuto()) {
      this.userEditedTitle = true;
      this.autoTitleDone = true;
      clearTimeout(this.autoTitleTimeout);
    }

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
    
    return '';
  }
  
  setSecretKey(secret) {
    // Store the secret key in both cookie and local storage
    document.cookie = `secret=${secret}; path=/; max-age=2592000`; // 30 days
    localStorage.setItem('textGeneratorSecret', secret);
    this.secret = secret;
  }
  
  showGenerateContentDialog() {
    // Check if AI features are disabled due to subscription
    if (this.aiDisabled) {
      if (window.subscriptionModal) { subscriptionModal.show(); };
      return;
    }
    
    // Create dialog for generation options
    const dialog = document.createElement('div');
    dialog.className = 'tgdocs-generate-dialog';
    
    // Create dialog content
    const dialogContent = document.createElement('div');
    dialogContent.className = 'tgdocs-generate-dialog-content';
    
    // Add title and description based on whether bulk generation is enabled
    const title = document.createElement('h3');
    title.textContent = this.useClaudeForBulk ? 'Generate Content with DeepSeek Flash' : 'Generate Content';
    dialogContent.appendChild(title);

    const description = document.createElement('p');
    if (this.useClaudeForBulk) {
      description.innerHTML = 'Enter a prompt below to generate high-quality content using DeepSeek V4 Flash.<br>The AI will continue writing from your prompt.';
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
    
    // Add model indicator if using bulk generation
    if (this.useClaudeForBulk) {
      const modelIndicator = document.createElement('div');
      modelIndicator.className = 'tgdocs-model-indicator';
      modelIndicator.innerHTML = '<span class="model-badge">DeepSeek Flash</span> Powered by DeepSeek V4 Flash';
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

    // If it was the current doc, open the next most recent one instead of
    // spawning a blank untitled document
    if (isCurrentDoc) {
      try {
        localStorage.removeItem(this.lastDocStorageKey());
        localStorage.removeItem('lastEditedDocument');
      } catch (e) { /* ignore */ }

      if (this.documents.length > 0) {
        this.loadDocument(this.documents[0].id);
      } else {
        this.createNewDocument();
      }
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

  convertDelimitedTextToMarkdownTable(text) {
    return TGDocsTableUtils.convertDelimitedTextToMarkdownTable(text);
  }

  insertEmptyMarkdownTable() {
    const markdownTable = TGDocsTableUtils.buildBlankMarkdownTable(3, 2);
    this.insertMarkdownTable(markdownTable);
    this.updateSaveStatus('Table inserted');
  }

  getTableInsertionText(markdownTable, index, deleteLength = 0) {
    let insertionText = String(markdownTable || '').trim();
    if (!insertionText) return '';

    const beforeIndex = Math.max(0, index - 1);
    const beforeText = index > 0 ? this.editor.getText(beforeIndex, 1) : '\n';
    const afterText = this.editor.getText(index + deleteLength, 1);

    if (beforeText !== '\n') {
      insertionText = '\n' + insertionText;
    }

    if (afterText && afterText !== '\n') {
      insertionText += '\n';
    }

    return insertionText + '\n';
  }

  insertMarkdownTable(markdownTable) {
    if (!this.editor || !markdownTable) return;

    const selection = this.editor.getSelection();
    const index = selection ? selection.index : Math.max(0, this.editor.getLength() - 1);
    const deleteLength = selection ? selection.length : 0;
    const insertionText = this.getTableInsertionText(markdownTable, index, deleteLength);

    if (!insertionText) return;

    this.editor.updateContents(
      new Delta().retain(index).delete(deleteLength).insert(insertionText),
      'user'
    );
    this.editor.setSelection(index + insertionText.length, 0, 'silent');
    this.editor.focus();
  }
  
  initializeImageUpload() {
    // Handle paste events for image upload
    if (this.editor) {
      this.editor.root.addEventListener('paste', this.handlePaste.bind(this), true);
    }
    
    // Handle drag and drop for image upload
    if (this.editor) {
      this.editor.root.addEventListener('dragover', this.handleDragOver.bind(this));
      this.editor.root.addEventListener('drop', this.handleDrop.bind(this));
    }
  }
  
  handlePaste(event) {
    if (event.defaultPrevented || !event.clipboardData) {
      return;
    }

    const items = event.clipboardData.items || [];
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item.type.indexOf('image') !== -1) {
        event.preventDefault();
        const file = item.getAsFile();
        this.uploadImage(file);
        return;
      }
    }

    const plainText = event.clipboardData.getData('text/plain');
    const markdownTable = this.convertDelimitedTextToMarkdownTable(plainText);

    if (markdownTable) {
      event.preventDefault();
      this.insertMarkdownTable(markdownTable);
      this.updateSaveStatus('Table inserted');
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

      // Preserve Markdown table blocks as editable Markdown text.
      if (
        TGDocsTableUtils.isMarkdownTableRow(line) &&
        i + 1 < lines.length &&
        TGDocsTableUtils.isMarkdownTableSeparator(lines[i + 1])
      ) {
        const tableLines = [line, lines[i + 1]];
        let j = i + 2;

        while (j < lines.length && TGDocsTableUtils.isMarkdownTableRow(lines[j])) {
          tableLines.push(lines[j]);
          j++;
        }

        delta.ops.push({ insert: tableLines.join('\n') + '\n' });
        i = j - 1;
        continue;
      }
      
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
    // Determine if we should use bulk generation for this request
    const useClaudeForThisRequest = isBulkGeneration && this.useClaudeForBulk;
    
    let data = null;
    
    if (useClaudeForThisRequest) {
      // Use the large-text endpoint for bulk generation
      this.updateSaveStatus('Using DeepSeek V4 Flash for high-quality generation');
      
      // Generate content using the large-text endpoint
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
          model: "deepseek-v4-flash"
        })
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`Large-text generation error (${response.status}): ${errorText}`);
        this.updateSaveStatus(`Generation failed: ${response.status} error`);
        return;
      }
      
      data = await response.json();
    } else {
      // Generate content using the standard API with adjusted settings
      const generationSettings = {...this.generationSettings};
      generationSettings.enable_thinking = false;
      
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
      const containsMarkdown = TGDocsTableUtils.containsMarkdownTable(generatedText) ||
        /(\#{1,6}\s+.+)|(\*\*.*?\*\*)|(\*[^\*]+?\*)|(\`[^\`]+?\`)|(\[[^\]]+?\]\([^\)]+?\))|(\>\s+.*?)|(^\s*[\*\-+]\s+.*?)|(^\s*\d+\.\s+.*?)|(\`\`\`[\s\S]*?\`\`\`)/m.test(generatedText);
      
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
