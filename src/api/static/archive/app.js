// Discovery Research Notebook - JavaScript Application

// ===== THEME MANAGEMENT =====
class ThemeManager {
    constructor() {
        // Check for saved theme preference or default to system preference
        this.theme = this.getInitialTheme();
        this.init();
    }

    getInitialTheme() {
        // First, check if user has a saved preference
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            return savedTheme;
        }
        
        // If no saved preference, check system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        
        // Default to light mode
        return 'light';
    }

    init() {
        this.applyTheme(this.theme);
        this.setupToggleListener();
        this.setupSystemThemeListener();
    }

    setupToggleListener() {
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }
    }

    setupSystemThemeListener() {
        // Listen for system theme changes
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                // Only auto-switch if user hasn't set a preference
                if (!localStorage.getItem('theme')) {
                    this.applyTheme(e.matches ? 'dark' : 'light');
                }
            });
        }
    }

    toggleTheme() {
        this.theme = this.theme === 'light' ? 'dark' : 'light';
        this.applyTheme(this.theme);
        localStorage.setItem('theme', this.theme);
    }

    applyTheme(theme) {
        this.theme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        
        // Update toggle button icon
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            const icon = themeToggle.querySelector('i');
            if (icon) {
                if (theme === 'dark') {
                    icon.className = 'fas fa-sun';
                    themeToggle.title = 'Switch to Light Mode';
                } else {
                    icon.className = 'fas fa-moon';
                    themeToggle.title = 'Switch to Dark Mode';
                }
            }
        }
    }

    getTheme() {
        return this.theme;
    }
}

// Initialize theme manager when DOM is ready
let themeManager;
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        themeManager = new ThemeManager();
    });
} else {
    themeManager = new ThemeManager();
}

class DiscoveryApp {
    constructor() {
        this.currentNotebook = null;
        this.notebooks = [];
        this.sources = [];
        this.outputs = [];
        this.apiBase = '/api';
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.setupModals();
        await this.loadNotebooks();
        this.showWelcomeOrFirstNotebook();
    }

    setupEventListeners() {
        // Header actions
        document.getElementById('newNotebookBtn').addEventListener('click', () => this.showCreateNotebookModal());
        document.getElementById('createFirstNotebookBtn').addEventListener('click', () => this.showCreateNotebookModal());
        document.getElementById('searchToggleBtn').addEventListener('click', () => this.toggleSearchPanel());
        document.getElementById('closeSearchBtn').addEventListener('click', () => this.closeSearchPanel());
        
        // Search
        document.getElementById('globalSearchBtn').addEventListener('click', () => this.performGlobalSearch());
        document.getElementById('globalSearchInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.performGlobalSearch();
        });
        
        // Sidebar
        document.getElementById('refreshNotebooksBtn').addEventListener('click', () => this.loadNotebooks());
        document.getElementById('sortSelect').addEventListener('change', () => this.loadNotebooks());
        document.getElementById('notebooksFilter').addEventListener('input', () => this.filterNotebooks());
        
        // Notebook actions
        document.getElementById('editNotebookBtn').addEventListener('click', () => this.showEditNotebookModal());
        document.getElementById('deleteNotebookBtn').addEventListener('click', () => this.confirmDeleteNotebook());
        document.getElementById('moreActionsBtn').addEventListener('click', () => this.toggleDropdown('moreActionsBtn'));
        document.getElementById('ingestNotebookBtn').addEventListener('click', () => this.ingestNotebook());
        document.getElementById('searchSimilarBtn').addEventListener('click', () => this.showSemanticSearchModal());
        
        
        // Source actions
        document.getElementById('addFileSourceBtn').addEventListener('click', () => this.showAddFileSourceModal());
        document.getElementById('addUrlSourceBtn').addEventListener('click', () => this.showAddUrlSourceModal());
        document.getElementById('addTextSourceBtn').addEventListener('click', () => this.showAddTextSourceModal());
        document.getElementById('addBySearchBtn').addEventListener('click', () => this.showSearchSourceModal());
        document.getElementById('sourcesFilter').addEventListener('input', () => this.filterSources());
        document.getElementById('sourceTypeFilter').addEventListener('change', () => this.filterSources());
        
        // Output actions
        document.getElementById('refreshOutputsBtn').addEventListener('click', () => this.loadOutputs());
        document.getElementById('downloadOutputBtn').addEventListener('click', () => this.downloadCurrentOutput());
        document.getElementById('deleteOutputFromViewerBtn').addEventListener('click', () => this.deleteCurrentOutput());
        
        // Forms
        document.getElementById('notebookForm').addEventListener('submit', (e) => this.handleNotebookSubmit(e));
        document.getElementById('fileSourceForm').addEventListener('submit', (e) => this.handleFileSourceSubmit(e));
        document.getElementById('urlSourceForm').addEventListener('submit', (e) => this.handleUrlSourceSubmit(e));
        document.getElementById('textSourceForm').addEventListener('submit', (e) => this.handleTextSourceSubmit(e));
        document.getElementById('searchSourceForm').addEventListener('submit', (e) => this.handleSearchSourceSubmit(e));
        
        // File input auto-name
        document.getElementById('sourceFile').addEventListener('change', () => this.autoFillFileName());
        
        // QA actions
        document.getElementById('qaToggleBtn').addEventListener('click', () => this.toggleQaSection());
        document.getElementById('closeQaBtn').addEventListener('click', () => this.closeQaSection());
        document.getElementById('askQuestionBtn').addEventListener('click', () => this.askQuestion());
        document.getElementById('questionInput').addEventListener('input', () => this.updateAskButtonState());
        document.getElementById('questionInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                e.preventDefault();
                this.askQuestion();
            }
        });
        
        // Mind map generation
        document.getElementById('generateMindMapBtn').addEventListener('click', () => this.openMindMapViewer());
        
        // Blog post generation
        document.getElementById('generateBlogPostBtn').addEventListener('click', () => this.showBlogPostModal());
        document.getElementById('blogPostForm').addEventListener('submit', (e) => this.handleBlogPostSubmit(e));
        document.getElementById('regenerateBlogPostBtn').addEventListener('click', () => this.regenerateBlogPost());
        document.getElementById('copyBlogPostBtn').addEventListener('click', () => this.copyBlogPost());
        document.getElementById('downloadBlogPostBtn').addEventListener('click', () => this.downloadBlogPost());
        document.getElementById('editBlogPostBtn').addEventListener('click', () => this.editBlogPost());
        document.getElementById('saveBlogPostBtn').addEventListener('click', () => this.saveBlogPost());
        
        // Semantic search
        document.getElementById('executeSemanticSearchBtn').addEventListener('click', () => this.executeSemanticSearch());
        
        // Close dropdowns when clicking outside
        document.addEventListener('click', (e) => this.handleDocumentClick(e));
    }

    setupModals() {
        // Setup modal close buttons
        document.querySelectorAll('.modal-close, [data-modal]').forEach(btn => {
            btn.addEventListener('click', () => {
                const modalId = btn.getAttribute('data-modal') || btn.closest('.modal').id;
                this.closeModal(modalId);
            });
        });
        
        // Close modals when clicking overlay
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(modal.id);
                }
            });
        });
    }

    // API Methods
    async apiCall(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.apiBase}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
                throw new Error(errorData.error || `HTTP ${response.status}`);
            }
            
            // Handle 204 No Content responses (like DELETE operations)
            if (response.status === 204) {
                return null;
            }
            
            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            this.showToast('Error', error.message, 'error');
            throw error;
        }
    }

    // Notebook Methods
    async loadNotebooks() {
        try {
            this.showLoading('Loading notebooks...');
            const sortBy = document.getElementById('sortSelect').value;
            const sortOrder = sortBy === 'name' ? 'asc' : 'desc';
            
            const response = await this.apiCall(`/notebooks?sort_by=${sortBy}&sort_order=${sortOrder}`);
            this.notebooks = response.notebooks;
            this.renderNotebooks();
        } catch (error) {
            console.error('Failed to load notebooks:', error);
        } finally {
            this.hideLoading();
        }
    }

    renderNotebooks() {
        const container = document.getElementById('notebooksList');
        const filter = document.getElementById('notebooksFilter').value.toLowerCase();
        
        const filteredNotebooks = this.notebooks.filter(notebook => 
            notebook.name.toLowerCase().includes(filter) ||
            (notebook.description && notebook.description.toLowerCase().includes(filter)) ||
            notebook.tags.some(tag => tag.toLowerCase().includes(filter))
        );
        
        if (filteredNotebooks.length === 0) {
            container.innerHTML = '<div class="loading">No notebooks found</div>';
            return;
        }
        
        container.innerHTML = filteredNotebooks.map(notebook => `
            <div class="notebook-item ${this.currentNotebook?.id === notebook.id ? 'active' : ''}" 
                 data-id="${notebook.id}" onclick="app.selectNotebook('${notebook.id}')">
                <div class="notebook-item-name">${this.escapeHtml(notebook.name)}</div>
                ${notebook.description ? `<div class="notebook-item-description">${this.escapeHtml(notebook.description)}</div>` : ''}
                <div class="notebook-item-stats">
                    <span>${notebook.source_count} sources</span>
                    <span>${this.formatDate(notebook.updated_at)}</span>
                </div>
                ${notebook.tags.length > 0 ? `
                    <div class="notebook-item-tags">
                        ${notebook.tags.map(tag => `<span class="tag">${this.escapeHtml(tag)}</span>`).join('')}
                    </div>
                ` : ''}
            </div>
        `).join('');
    }

    async selectNotebook(notebookId) {
        try {
            this.showLoading('Loading notebook...');
            const notebook = await this.apiCall(`/notebooks/${notebookId}`);
            this.currentNotebook = notebook;
            this.renderNotebookView();
            await this.loadSources();
            await this.loadOutputs();
            
            // Update active state in sidebar
            document.querySelectorAll('.notebook-item').forEach(item => {
                item.classList.toggle('active', item.getAttribute('data-id') === notebookId);
            });
        } catch (error) {
            console.error('Failed to select notebook:', error);
        } finally {
            this.hideLoading();
        }
    }

    renderNotebookView() {
        if (!this.currentNotebook) return;
        
        document.getElementById('welcomeScreen').classList.add('hidden');
        document.getElementById('notebookView').classList.remove('hidden');
        
        document.getElementById('notebookTitle').textContent = this.currentNotebook.name;
        document.getElementById('notebookDescription').textContent = this.currentNotebook.description || 'No description';
        document.getElementById('sourceCount').textContent = `${this.currentNotebook.source_count} sources`;
        document.getElementById('lastModified').textContent = `Last modified: ${this.formatDate(this.currentNotebook.updated_at)}`;
        
        // Render tags
        const tagsContainer = document.getElementById('notebookTags');
        tagsContainer.innerHTML = this.currentNotebook.tags.map(tag => 
            `<span class="tag">${this.escapeHtml(tag)}</span>`
        ).join('');
    }

    showCreateNotebookModal() {
        document.getElementById('notebookModalTitle').textContent = 'Create New Notebook';
        document.getElementById('saveNotebookBtn').textContent = 'Create Notebook';
        document.getElementById('notebookForm').reset();
        this.showModal('notebookModal');
    }

    showEditNotebookModal() {
        if (!this.currentNotebook) return;
        
        document.getElementById('notebookModalTitle').textContent = 'Edit Notebook';
        document.getElementById('saveNotebookBtn').textContent = 'Save Changes';
        
        // Fill form with current values
        document.getElementById('notebookName').value = this.currentNotebook.name;
        document.getElementById('notebookDescriptionInput').value = this.currentNotebook.description || '';
        document.getElementById('notebookTagsInput').value = this.currentNotebook.tags.join(', ');
        
        this.showModal('notebookModal');
    }

    async handleNotebookSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const data = {
            name: formData.get('name').trim(),
            description: formData.get('description').trim() || null,
            tags: formData.get('tags').split(',').map(tag => tag.trim()).filter(tag => tag)
        };
        
        try {
            this.showLoading('Saving notebook...');
            
            if (this.currentNotebook && document.getElementById('notebookModalTitle').textContent.includes('Edit')) {
                // Update existing notebook
                const updated = await this.apiCall(`/notebooks/${this.currentNotebook.id}`, {
                    method: 'PUT',
                    body: JSON.stringify(data)
                });
                this.currentNotebook = updated;
                this.renderNotebookView();
                this.showToast('Success', 'Notebook updated successfully', 'success');
            } else {
                // Create new notebook
                const created = await this.apiCall('/notebooks', {
                    method: 'POST',
                    body: JSON.stringify(data)
                });
                this.showToast('Success', 'Notebook created successfully', 'success');
                await this.selectNotebook(created.id);
            }
            
            this.closeModal('notebookModal');
            await this.loadNotebooks();
        } catch (error) {
            console.error('Failed to save notebook:', error);
        } finally {
            this.hideLoading();
        }
    }

    confirmDeleteNotebook() {
        if (!this.currentNotebook) return;
        
        this.showConfirmation(
            'Delete Notebook',
            `Are you sure you want to delete "${this.currentNotebook.name}"? This action cannot be undone.`,
            async () => {
                try {
                    this.showLoading('Deleting notebook...');
                    await this.apiCall(`/notebooks/${this.currentNotebook.id}?cascade=true`, {
                        method: 'DELETE'
                    });
                    this.showToast('Success', 'Notebook deleted successfully', 'success');
                    this.currentNotebook = null;
                    this.showWelcomeScreen();
                    await this.loadNotebooks();
                } catch (error) {
                    console.error('Failed to delete notebook:', error);
                } finally {
                    this.hideLoading();
                }
            }
        );
    }

    // Source Methods
    async loadSources() {
        if (!this.currentNotebook) return;
        
        try {
            const response = await this.apiCall(`/sources/notebook/${this.currentNotebook.id}`);
            this.sources = response.sources;
            this.renderSources();
        } catch (error) {
            console.error('Failed to load sources:', error);
        }
    }

    renderSources() {
        const container = document.getElementById('sourcesList');
        const filter = document.getElementById('sourcesFilter').value.toLowerCase();
        const typeFilter = document.getElementById('sourceTypeFilter').value;
        
        let filteredSources = this.sources.filter(source => {
            const matchesText = source.name.toLowerCase().includes(filter) ||
                              source.extracted_text.toLowerCase().includes(filter);
            const matchesType = !typeFilter || source.source_type === typeFilter;
            return matchesText && matchesType && !source.deleted_at;
        });
        
        if (filteredSources.length === 0) {
            container.innerHTML = `
                <div class="no-sources">
                    <i class="fas fa-folder-open"></i>
                    <p>No sources yet. Add files or URLs to get started.</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = filteredSources.map(source => {
            const icon = this.getSourceIcon(source);
            const preview = source.extracted_text.substring(0, 200) + (source.extracted_text.length > 200 ? '...' : '');
            
            return `
                <div class="source-item" data-id="${source.id}">
                    <div class="source-item-header">
                        <div class="source-item-name">${this.escapeHtml(source.name)}</div>
                        <div class="source-item-actions">
                            ${source.source_type === 'url' && source.url ? `
                            <a href="${source.url}" target="_blank" class="btn btn-icon btn-sm" title="Open URL">
                                <i class="fas fa-external-link-alt"></i>
                            </a>
                            ` : ''}
                            <button class="btn btn-icon btn-sm" onclick="app.viewSource('${source.id}')" title="View Content">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn btn-icon btn-sm" onclick="app.renameSource('${source.id}')" title="Rename">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-icon btn-sm" onclick="app.deleteSource('${source.id}')" title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    <div class="source-item-type">
                        <i class="${icon}"></i>
                        <span>${source.source_type === 'file' ? source.file_type?.toUpperCase() || 'FILE' : source.source_type === 'text' ? 'TEXT' : 'URL'}</span>
                        ${source.file_size ? `<span>${this.formatFileSize(source.file_size)}</span>` : ''}
                    </div>
                    <div class="source-item-preview">${this.escapeHtml(preview)}</div>
                    <div class="source-item-meta">
                        <span>Added ${this.formatDate(source.created_at)}</span>
                        <span>${source.extracted_text.length} characters</span>
                    </div>
                </div>
            `;
        }).join('');
    }

    getSourceIcon(source) {
        if (source.source_type === 'url') return 'fas fa-link';
        if (source.source_type === 'text') return 'fas fa-align-left';
        
        const fileType = source.file_type?.toLowerCase();
        switch (fileType) {
            case 'pdf': return 'fas fa-file-pdf';
            case 'doc':
            case 'docx': return 'fas fa-file-word';
            case 'txt': return 'fas fa-file-alt';
            case 'md': return 'fab fa-markdown';
            default: return 'fas fa-file';
        }
    }

    showAddFileSourceModal() {
        if (!this.currentNotebook) {
            this.showToast('Error', 'Please select a notebook first', 'error');
            return;
        }
        
        document.getElementById('fileSourceForm').reset();
        this.showModal('fileSourceModal');
    }

    showAddUrlSourceModal() {
        if (!this.currentNotebook) {
            this.showToast('Error', 'Please select a notebook first', 'error');
            return;
        }
        
        document.getElementById('urlSourceForm').reset();
        this.showModal('urlSourceModal');
    }

    showAddTextSourceModal() {
        if (!this.currentNotebook) {
            this.showToast('Error', 'Please select a notebook first', 'error');
            return;
        }
        
        document.getElementById('textSourceForm').reset();
        this.showModal('textSourceModal');
    }

    autoFillFileName() {
        const fileInput = document.getElementById('sourceFile');
        const nameInput = document.getElementById('sourceFileName');
        
        if (fileInput.files.length > 0 && !nameInput.value) {
            const fileName = fileInput.files[0].name;
            const nameWithoutExt = fileName.substring(0, fileName.lastIndexOf('.')) || fileName;
            nameInput.value = nameWithoutExt;
        }
    }

    async handleFileSourceSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const file = formData.get('file');
        const name = formData.get('name').trim();
        
        if (!file || !name) {
            this.showToast('Error', 'Please provide both file and name', 'error');
            return;
        }
        
        try {
            this.showLoading('Uploading and processing file...');
            
            const fileContent = await this.readFileAsBase64(file);
            const fileType = file.name.split('.').pop().toLowerCase();
            
            const data = {
                notebook_id: this.currentNotebook.id,
                name: name,
                file_content: fileContent,
                file_type: fileType
            };
            
            await this.apiCall('/sources/file', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            
            this.showToast('Success', 'File source added successfully', 'success');
            this.closeModal('fileSourceModal');
            await this.loadSources();
            await this.loadNotebooks(); // Refresh to update source count
        } catch (error) {
            console.error('Failed to add file source:', error);
        } finally {
            this.hideLoading();
        }
    }

    readFileAsBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
                const base64String = reader.result.split(',')[1];
                resolve(base64String);
            };
            reader.onerror = (error) => {
                reject(error);
            };
            reader.readAsDataURL(file);
        });
    }

    async handleUrlSourceSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const url = formData.get('url').trim();
        const title = formData.get('title').trim();
        
        if (!url) {
            this.showToast('Error', 'Please provide a URL', 'error');
            return;
        }
        
        try {
            this.showLoading('Fetching and processing URL...');
            
            const data = {
                notebook_id: this.currentNotebook.id,
                url: url,
                title: title || null
            };
            
            await this.apiCall('/sources/url', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            
            this.showToast('Success', 'URL source added successfully', 'success');
            this.closeModal('urlSourceModal');
            await this.loadSources();
            await this.loadNotebooks(); // Refresh to update source count
        } catch (error) {
            console.error('Failed to add URL source:', error);
        } finally {
            this.hideLoading();
        }
    }

    async handleTextSourceSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const title = formData.get('title').trim();
        const content = formData.get('content').trim();
        
        if (!title || !content) {
            this.showToast('Error', 'Please provide both title and content', 'error');
            return;
        }
        
        try {
            this.showLoading('Adding text source...');
            
            const data = {
                notebook_id: this.currentNotebook.id,
                title: title,
                content: content
            };
            
            await this.apiCall('/sources/text', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            
            this.showToast('Success', 'Text source added successfully', 'success');
            this.closeModal('textSourceModal');
            await this.loadSources();
            await this.loadNotebooks(); // Refresh to update source count
        } catch (error) {
            console.error('Failed to add text source:', error);
        } finally {
            this.hideLoading();
        }
    }

    showSearchSourceModal() {
        if (!this.currentNotebook) {
            this.showToast('Error', 'Please select a notebook first', 'error');
            return;
        }
        
        document.getElementById('searchSourceForm').reset();
        document.getElementById('searchSourceResults').classList.add('hidden');
        document.getElementById('searchSourceResultsList').innerHTML = '';
        this.showModal('searchSourceModal');
    }

    async handleSearchSourceSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const searchPhrase = formData.get('searchPhrase').trim();
        const maxResults = parseInt(formData.get('maxArticles'));
        
        if (!searchPhrase) {
            this.showToast('Error', 'Please enter a search phrase', 'error');
            return;
        }
        
        try {
            this.showLoading('Searching for articles and adding sources...');
            
            const data = {
                notebook_id: this.currentNotebook.id,
                search_phrase: searchPhrase,
                max_results: maxResults
            };
            
            const response = await this.apiCall('/sources/search-and-add', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            
            this.displaySearchSourceResults(response);
            
            // Show success message with details
            if (response.total_added === response.total_found) {
                this.showToast('Success', `Successfully added all ${response.total_added} sources!`, 'success');
            } else if (response.total_added > 0) {
                this.showToast('Partial Success', `Added ${response.total_added} of ${response.total_found} sources`, 'warning');
            } else {
                this.showToast('Warning', 'No sources were added. Check the results for details.', 'warning');
            }
            
            // Refresh sources and notebooks list
            await this.loadSources();
            await this.loadNotebooks();
            
            // Close modal after delay to let users see the results
            setTimeout(() => {
                this.closeModal('searchSourceModal');
            }, 3000);
        } catch (error) {
            console.error('Failed to search and add sources:', error);
        } finally {
            this.hideLoading();
        }
    }

    displaySearchSourceResults(response) {
        const resultsContainer = document.getElementById('searchSourceResults');
        const resultsList = document.getElementById('searchSourceResultsList');
        
        resultsContainer.classList.remove('hidden');
        
        if (response.results.length === 0) {
            resultsList.innerHTML = '<p class="text-muted">No articles found.</p>';
            return;
        }
        
        const summary = `<div class="mb-2"><strong>Summary:</strong> ${response.total_added} of ${response.total_found} sources added successfully</div>`;
        
        resultsList.innerHTML = summary + response.results.map(result => `
            <div class="search-source-result-item">
                <div class="search-source-result-header">
                    <div class="search-source-result-title">${this.escapeHtml(result.title)}</div>
                    <span class="search-source-result-status ${result.success ? 'success' : 'error'}">
                        ${result.success ? '✓ Added' : '✗ Failed'}
                    </span>
                </div>
                <div class="search-source-result-url">
                    <a href="${result.url}" target="_blank" rel="noopener noreferrer">${this.escapeHtml(result.url)}</a>
                </div>
                ${result.error ? `<div class="search-source-result-error">Error: ${this.escapeHtml(result.error)}</div>` : ''}
            </div>
        `).join('');
    }

    showSearchSourceModal() {
        if (!this.currentNotebook) {
            this.showToast('Error', 'Please select a notebook first', 'error');
            return;
        }
        
        document.getElementById('searchSourceForm').reset();
        document.getElementById('searchSourceResults').classList.add('hidden');
        document.getElementById('searchSourceResultsList').innerHTML = '';
        this.showModal('searchSourceModal');
    }

    async handleSearchSourceSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const searchPhrase = formData.get('searchPhrase').trim();
        const maxResults = parseInt(formData.get('maxArticles'));
        
        if (!searchPhrase) {
            this.showToast('Error', 'Please provide a search phrase', 'error');
            return;
        }
        
        try {
            this.showLoading('Searching for articles and adding sources...');
            
            const data = {
                notebook_id: this.currentNotebook.id,
                search_phrase: searchPhrase,
                max_results: maxResults
            };
            
            const response = await this.apiCall('/sources/search-and-add', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            
            this.displaySearchSourceResults(response);
            
            if (response.total_added > 0) {
                this.showToast('Success', `Added ${response.total_added} of ${response.total_found} sources successfully`, 'success');
                await this.loadSources();
                await this.loadNotebooks(); // Refresh to update source count
            } else {
                this.showToast('Warning', 'No sources could be added. Check the results for details.', 'warning');
            }
        } catch (error) {
            console.error('Failed to search and add sources:', error);
        } finally {
            this.hideLoading();
        }
    }

    displaySearchSourceResults(response) {
        const resultsContainer = document.getElementById('searchSourceResults');
        const resultsList = document.getElementById('searchSourceResultsList');
        
        resultsContainer.classList.remove('hidden');
        
        if (response.results.length === 0) {
            resultsList.innerHTML = '<div class="text-center text-muted">No articles found for your search.</div>';
            return;
        }
        
        resultsList.innerHTML = response.results.map(result => `
            <div class="search-source-result-item">
                <div class="search-source-result-header">
                    <div class="search-source-result-title">${this.escapeHtml(result.title)}</div>
                    <div class="search-source-result-status ${result.success ? 'success' : 'error'}">
                        ${result.success ? 'Added' : 'Failed'}
                    </div>
                </div>
                <div class="search-source-result-url">${this.escapeHtml(result.url)}</div>
                ${result.error ? `<div class="search-source-result-error">Error: ${this.escapeHtml(result.error)}</div>` : ''}
            </div>
        `).join('');
    }

    async viewSource(sourceId) {
        try {
            this.showLoading('Loading source content...');
            const source = await this.apiCall(`/sources/${sourceId}`);
            
            document.getElementById('sourceViewerTitle').textContent = source.name;
            document.getElementById('sourceContent').textContent = source.extracted_text;
            document.getElementById('sourceContentLoader').style.display = 'none';
            
            this.showModal('sourceViewerModal');
        } catch (error) {
            console.error('Failed to view source:', error);
        } finally {
            this.hideLoading();
        }
    }

    async renameSource(sourceId) {
        const source = this.sources.find(s => s.id === sourceId);
        if (!source) return;
        
        const newName = prompt('Enter new name for source:', source.name);
        if (!newName || newName.trim() === source.name) return;
        
        try {
            this.showLoading('Renaming source...');
            await this.apiCall(`/sources/${sourceId}/rename`, {
                method: 'PATCH',
                body: JSON.stringify({ new_name: newName.trim() })
            });
            
            this.showToast('Success', 'Source renamed successfully', 'success');
            await this.loadSources();
        } catch (error) {
            console.error('Failed to rename source:', error);
        } finally {
            this.hideLoading();
        }
    }

    async deleteSource(sourceId) {
        const source = this.sources.find(s => s.id === sourceId);
        if (!source) return;
        
        this.showConfirmation(
            'Delete Source',
            `Are you sure you want to delete "${source.name}"?`,
            async () => {
                try {
                    this.showLoading('Deleting source...');
                    await this.apiCall(`/sources/${sourceId}?notebook_id=${this.currentNotebook.id}`, {
                        method: 'DELETE'
                    });
                    this.showToast('Success', 'Source deleted successfully', 'success');
                    await this.loadSources();
                    await this.loadNotebooks(); // Refresh to update source count
                } catch (error) {
                    console.error('Failed to delete source:', error);
                } finally {
                    this.hideLoading();
                }
            }
        );
    }

    // Output Methods
    async loadOutputs() {
        if (!this.currentNotebook) return;
        
        try {
            const response = await this.apiCall(`/outputs?notebook_id=${this.currentNotebook.id}`);
            this.outputs = response.outputs || [];
            this.renderOutputs();
        } catch (error) {
            console.error('Failed to load outputs:', error);
        }
    }

    renderOutputs() {
        const container = document.getElementById('outputsList');
        
        if (!this.outputs || this.outputs.length === 0) {
            container.innerHTML = `
                <div class="no-outputs">
                    <i class="fas fa-file-alt"></i>
                    <p>No outputs yet. Generate blog posts or other outputs to see them here.</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = this.outputs.map(output => {
            const icon = this.getOutputIcon(output.output_type);
            const preview = "";
            const statusBadge = this.getOutputStatusBadge(output.status);
            
            return `
                <div class="output-item" data-id="${output.id}">
                    <div class="output-item-header">
                        <div class="output-item-title">${this.escapeHtml(output.title)}</div>
                        <div class="output-item-actions">
                            <button class="btn btn-icon btn-sm" onclick="app.viewOutput('${output.id}')" title="View">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn btn-icon btn-sm" onclick="app.downloadOutput('${output.id}')" title="Download">
                                <i class="fas fa-download"></i>
                            </button>
                            <button class="btn btn-icon btn-sm" onclick="app.deleteOutput('${output.id}')" title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    <div class="output-item-type">
                        <i class="${icon}"></i>
                        <span>${this.formatOutputType(output.output_type)}</span>
                        ${statusBadge}
                    </div>
                    <div class="output-item-preview">${this.escapeHtml(preview)}</div>
                    <div class="output-item-meta">
                        <div class="output-item-stats">
                            <span>${output.word_count || 0} words</span>
                            <span>Created ${this.formatDate(output.created_at)}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    getOutputIcon(outputType) {
        switch (outputType) {
            case 'blog_post': return 'fas fa-pen-fancy';
            case 'summary': return 'fas fa-file-alt';
            case 'report': return 'fas fa-file-contract';
            default: return 'fas fa-file';
        }
    }

    getOutputPreview(output) {
        if (!output.content) return 'No content available';
        
        // Remove HTML tags and get first 200 characters
        const plainText = output.content.replace(/<[^>]*>/g, '').replace(/\n/g, ' ');
        return plainText.substring(0, 200) + (plainText.length > 200 ? '...' : '');
    }

    getOutputStatusBadge(status) {
        const badges = {
            'completed': '<span style="color: #48bb78;">●</span>',
            'in_progress': '<span style="color: #ed8936;">●</span>',
            'failed': '<span style="color: #f56565;">●</span>',
            'draft': '<span style="color: #a0aec0;">●</span>'
        };
        return badges[status] || '';
    }

    formatOutputType(outputType) {
        const types = {
            'blog_post': 'Blog Post',
            'summary': 'Summary',
            'report': 'Report',
            'analysis': 'Analysis'
        };
        return types[outputType] || outputType;
    }

    async viewOutput(outputId) {
        try {
            this.showLoading('Loading output...');
            const output = await this.apiCall(`/outputs/${outputId}`);
            
            document.getElementById('outputViewerTitle').textContent = output.title;
            document.getElementById('outputContent').innerHTML = this.formatBlogPostContent(output.content);
            document.getElementById('outputContentLoader').style.display='none';
            
            // Store current output for download/delete actions
            this.currentOutput = output;
            
            this.showModal('outputViewerModal');
        } catch (error) {
            console.error('Failed to view output:', error);
        } finally {
            this.hideLoading();
        }
    }

    async downloadOutput(outputId) {
        try {
            this.showLoading('Preparing download...');
            const output = await this.apiCall(`/outputs/${outputId}`);
            
            // Create plain text version
            const plainText = output.content
                .replace(/<[^>]*>/g, '')
                .replace(/&nbsp;/g, ' ')
                .replace(/&amp;/g, '&')
                .replace(/&lt;/g, '<')
                .replace(/&gt;/g, '>')
                .replace(/&quot;/g, '"');
            
            const blob = new Blob([plainText], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `${output.title}.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            this.showToast('Success', 'Output downloaded', 'success');
        } catch (error) {
            console.error('Failed to download output:', error);
            this.showToast('Error', 'Failed to download output', 'error');
        } finally {
            this.hideLoading();
        }
    }

    deleteOutput(outputId) {
        const output = this.outputs.find(o => o.id === outputId);
        if (!output) return;
        
        this.showConfirmation(
            'Delete Output',
            `Are you sure you want to delete "${output.title}"? This action cannot be undone.`,
            async () => {
                try {
                    this.showLoading('Deleting output...');
                    await this.apiCall(`/outputs/${outputId}`, {
                        method: 'DELETE'
                    });
                    this.showToast('Success', 'Output deleted successfully', 'success');
                    await this.loadOutputs();
                    
                    // Close the viewer modal if it's open
                    if (this.currentOutput && this.currentOutput.id === outputId) {
                        this.closeModal('outputViewerModal');
                        this.currentOutput = null;
                    }
                } catch (error) {
                    console.error('Failed to delete output:', error);
                } finally {
                    this.hideLoading();
                }
            }
        );
    }

    async downloadCurrentOutput() {
        if (!this.currentOutput) return;
        await this.downloadOutput(this.currentOutput.id);
    }

    deleteCurrentOutput() {
        if (!this.currentOutput) return;
        
        // Close the modal first, then show confirmation
        this.closeModal('outputViewerModal');
        this.deleteOutput(this.currentOutput.id);
    }

    // Vector Search Methods
    async ingestNotebook() {
        if (!this.currentNotebook) return;
        
        try {
            this.showLoading('Ingesting notebook into vector database...');
            const response = await this.apiCall(`/notebooks/${this.currentNotebook.id}/ingest`, {
                method: 'POST',
                body: JSON.stringify({
                    chunk_size: 1000,
                    overlap: 200,
                    force_reingest: false
                })
            });
            
            this.showToast('Success', `Ingested ${response.chunks_ingested} chunks successfully`, 'success');
        } catch (error) {
            console.error('Failed to ingest notebook:', error);
        } finally {
            this.hideLoading();
        }
    }

    showSemanticSearchModal() {
        if (!this.currentNotebook) {
            this.showToast('Error', 'Please select a notebook first', 'error');
            return;
        }
        
        document.getElementById('semanticSearchQuery').value = '';
        document.getElementById('semanticSearchResults').innerHTML = '';
        this.showModal('semanticSearchModal');
    }

    async executeSemanticSearch() {
        const query = document.getElementById('semanticSearchQuery').value.trim();
        const limit = document.getElementById('searchResultLimit').value;
        
        if (!query) {
            this.showToast('Error', 'Please enter a search query', 'error');
            return;
        }
        
        try {
            this.showLoading('Searching...');
            const response = await this.apiCall(
                `/notebooks/${this.currentNotebook.id}/similar?query=${encodeURIComponent(query)}&limit=${limit}`
            );
            
            this.renderSemanticSearchResults(response.results);
        } catch (error) {
            console.error('Failed to perform semantic search:', error);
        } finally {
            this.hideLoading();
        }
    }

    renderSemanticSearchResults(results) {
        const container = document.getElementById('semanticSearchResults');
        
        if (results.length === 0) {
            container.innerHTML = '<div class="text-center text-muted mt-3">No results found</div>';
            return;
        }
        
        container.innerHTML = results.map((result, index) => `
            <div class="search-result-item">
                <div class="search-result-header">
                    <div class="search-result-title">Result ${index + 1} - ${result.source_name || 'Unknown Source'}</div>
                    <div class="search-result-score">Score: ${(result.certainty * 100).toFixed(1)}%</div>
                </div>
                <div class="search-result-content">${this.escapeHtml(result.text)}</div>
                <div class="search-result-meta">
                    <span>Chunk ${result.chunk_index}</span>
                    <span>Distance: ${result.distance?.toFixed(4) || 'N/A'}</span>
                </div>
            </div>
        `).join('');
    }

    // UI Helper Methods
    filterNotebooks() {
        this.renderNotebooks();
    }

    filterSources() {
        this.renderSources();
    }

    toggleSearchPanel() {
        const panel = document.getElementById('searchPanel');
        panel.classList.toggle('hidden');
        if (!panel.classList.contains('hidden')) {
            document.getElementById('globalSearchInput').focus();
        }
    }

    closeSearchPanel() {
        document.getElementById('searchPanel').classList.add('hidden');
        document.getElementById('searchResults').innerHTML = '';
    }

    async performGlobalSearch() {
        const query = document.getElementById('globalSearchInput').value.trim();
        if (!query) return;
        
        // Placeholder for global search functionality
        this.showToast('Info', 'Global search not yet implemented', 'warning');
    }

    showWelcomeOrFirstNotebook() {
        if (this.notebooks.length === 0) {
            this.showWelcomeScreen();
        } else if (!this.currentNotebook) {
            // Auto-select first notebook
            this.selectNotebook(this.notebooks[0].id);
        }
    }

    showWelcomeScreen() {
        document.getElementById('welcomeScreen').classList.remove('hidden');
        document.getElementById('notebookView').classList.add('hidden');
    }

    toggleDropdown(buttonId) {
        const button = document.getElementById(buttonId);
        const dropdown = button.closest('.dropdown');
        dropdown.classList.toggle('active');
    }

    handleDocumentClick(e) {
        // Close dropdowns when clicking outside
        if (!e.target.closest('.dropdown')) {
            document.querySelectorAll('.dropdown.active').forEach(dropdown => {
                dropdown.classList.remove('active');
            });
        }
    }

    generateOutput() {
        // Placeholder for output generation
        this.showToast('Info', 'Output generation not yet implemented', 'warning');
    }

    // Modal Methods
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        
        // Check if we need to compensate for scrollbar
        const hasVerticalScrollbar = document.body.scrollHeight > window.innerHeight;
        
        if (hasVerticalScrollbar) {
            document.body.classList.add('modal-open');
        } else {
            document.body.style.overflow = 'hidden';
        }
        
        modal.classList.add('active');
        
        // Focus trap - focus first focusable element
        setTimeout(() => {
            const focusableElements = modal.querySelectorAll('input, textarea, select, button:not([disabled])');
            if (focusableElements.length > 0) {
                focusableElements[0].focus();
            }
        }, 100);
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        modal.classList.remove('active');
        
        // Reset body styles
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        
        // Return focus to the body
        document.body.focus();
    }

    showConfirmation(title, message, onConfirm) {
        document.getElementById('confirmationTitle').textContent = title;
        document.getElementById('confirmationMessage').textContent = message;
        
        const confirmBtn = document.getElementById('confirmActionBtn');
        confirmBtn.onclick = () => {
            this.closeModal('confirmationModal');
            onConfirm();
        };
        
        this.showModal('confirmationModal');
    }

    // Loading Methods
    showLoading(message = 'Loading...') {
        document.getElementById('loadingMessage').textContent = message;
        document.getElementById('loadingOverlay').classList.remove('hidden');
    }

    hideLoading() {
        document.getElementById('loadingOverlay').classList.add('hidden');
    }

    // Toast Notifications
    showToast(title, message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <div class="toast-title">${this.escapeHtml(title)}</div>
                <div class="toast-message">${this.escapeHtml(message)}</div>
            </div>
            <button class="toast-close">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        const container = document.getElementById('toastContainer');
        container.appendChild(toast);
        
        // Show toast
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Auto remove after 5 seconds
        setTimeout(() => this.removeToast(toast), 5000);
        
        // Manual close
        toast.querySelector('.toast-close').addEventListener('click', () => this.removeToast(toast));
    }

    removeToast(toast) {
        toast.classList.remove('show');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }

    // QA Methods
    toggleQaSection() {
        const qaSection = document.getElementById('qaSection');
        const sourcesSection = document.querySelector('.sources-section');
        
        if (qaSection.classList.contains('hidden')) {
            this.showQaSection();
        } else {
            this.closeQaSection();
        }
    }

    showQaSection() {
        if (!this.currentNotebook) {
            this.showToast('Error', 'Please select a notebook first', 'error');
            return;
        }

        const qaSection = document.getElementById('qaSection');
        const sourcesSection = document.querySelector('.sources-section');
        
        qaSection.classList.remove('hidden');
        sourcesSection.style.marginBottom = '0';
        
        // Clear previous conversation
        this.clearQaConversation();
        
        // Focus on question input
        document.getElementById('questionInput').focus();
        
        // Scroll to QA section
        qaSection.scrollIntoView({ behavior: 'smooth' });
    }

    closeQaSection() {
        const qaSection = document.getElementById('qaSection');
        qaSection.classList.add('hidden');
    }

    clearQaConversation() {
        const conversation = document.getElementById('qaConversation');
        conversation.innerHTML = `
            <div class="qa-welcome">
                <i class="fas fa-question-circle"></i>
                <p>Ask questions about your notebook content. I'll search through your sources and provide answers with citations.</p>
            </div>
        `;
    }

    updateAskButtonState() {
        const questionInput = document.getElementById('questionInput');
        const askButton = document.getElementById('askQuestionBtn');
        
        askButton.disabled = !questionInput.value.trim();
    }

    async askQuestion() {
        const questionInput = document.getElementById('questionInput');
        const question = questionInput.value.trim();
        
        if (!question) {
            this.showToast('Error', 'Please enter a question', 'error');
            return;
        }

        if (!this.currentNotebook) {
            this.showToast('Error', 'No notebook selected', 'error');
            return;
        }

        // Get QA parameters
        const maxSources = document.getElementById('qaMaxSources').value;
        const temperature = parseFloat(document.getElementById('qaTemperature').value);

        // Add question to conversation
        this.addQuestionToConversation(question);
        
        // Clear input
        questionInput.value = '';
        this.updateAskButtonState();

        // Show loading state
        this.addLoadingToConversation();

        try {
            const response = await this.apiCall(`/notebooks/${this.currentNotebook.id}/qa`, {
                method: 'POST',
                body: JSON.stringify({
                    question: question,
                    max_sources: parseInt(maxSources),
                    temperature: temperature,
                    max_tokens: 1500
                })
            });

            // Remove loading
            this.removeLoadingFromConversation();
            
            // Add answer to conversation
            this.addAnswerToConversation(response);

        } catch (error) {
            console.error('QA Error:', error);
            this.removeLoadingFromConversation();
            this.addErrorToConversation(error.message);
        }
    }

    addQuestionToConversation(question) {
        const conversation = document.getElementById('qaConversation');
        
        // Remove welcome message if present
        const welcome = conversation.querySelector('.qa-welcome');
        if (welcome) {
            welcome.remove();
        }

        const timestamp = new Date().toLocaleTimeString();
        
        const questionHtml = `
            <div class="qa-item">
                <div class="qa-question">
                    <div class="qa-question-text">${this.escapeHtml(question)}</div>
                    <div class="qa-question-meta">
                        <span><i class="fas fa-user"></i> You</span>
                        <span>${timestamp}</span>
                    </div>
                </div>
            </div>
        `;
        
        conversation.insertAdjacentHTML('beforeend', questionHtml);
        this.scrollToBottom(conversation);
    }

    addLoadingToConversation() {
        const conversation = document.getElementById('qaConversation');
        const lastItem = conversation.querySelector('.qa-item:last-child');
        
        const loadingHtml = `
            <div class="qa-loading" id="qaLoadingIndicator">
                <i class="fas fa-spinner fa-spin"></i>
                <span>Searching sources and generating answer...</span>
            </div>
        `;
        
        if (lastItem) {
            lastItem.insertAdjacentHTML('beforeend', loadingHtml);
        } else {
            conversation.insertAdjacentHTML('beforeend', loadingHtml);
        }
        
        this.scrollToBottom(conversation);
    }

    removeLoadingFromConversation() {
        const loading = document.getElementById('qaLoadingIndicator');
        if (loading) {
            loading.remove();
        }
    }

    addAnswerToConversation(response) {
        const conversation = document.getElementById('qaConversation');
        const lastItem = conversation.querySelector('.qa-item:last-child');
        
        // Format answer content (convert markdown-like formatting)
        const formattedAnswer = this.formatAnswerContent(response.answer);
        
        // Calculate confidence percentage
        const confidencePercent = response.confidence_score ? Math.round(response.confidence_score * 100) : 0;
        
        const answerHtml = `
            <div class="qa-answer">
                <div class="qa-answer-content">${formattedAnswer}</div>
                <div class="qa-answer-meta">
                    <div class="qa-confidence">
                        <span>Confidence:</span>
                        <div class="qa-confidence-bar">
                            <div class="qa-confidence-fill" style="width: ${confidencePercent}%"></div>
                        </div>
                        <span>${confidencePercent}%</span>
                    </div>
                    <span><i class="fas fa-clock"></i> ${response.processing_time_ms}ms</span>
                </div>
                ${this.renderQaSources(response.sources)}
            </div>
        `;
        
        if (lastItem) {
            lastItem.insertAdjacentHTML('beforeend', answerHtml);
        } else {
            conversation.insertAdjacentHTML('beforeend', answerHtml);
        }
        
        this.scrollToBottom(conversation);
    }

    addErrorToConversation(errorMessage) {
        const conversation = document.getElementById('qaConversation');
        const lastItem = conversation.querySelector('.qa-item:last-child');
        
        const errorHtml = `
            <div class="qa-error">
                <i class="fas fa-exclamation-triangle"></i>
                Sorry, I couldn't answer your question: ${this.escapeHtml(errorMessage)}
            </div>
        `;
        
        if (lastItem) {
            lastItem.insertAdjacentHTML('beforeend', errorHtml);
        } else {
            conversation.insertAdjacentHTML('beforeend', errorHtml);
        }
        
        this.scrollToBottom(conversation);
    }

    formatAnswerContent(content) {
        // Basic markdown-like formatting
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .replace(/^/, '<p>')
            .replace(/$/, '</p>')
            .replace(/<p><\/p>/g, '');
    }

    renderQaSources(sources) {
        if (!sources || sources.length === 0) {
            return '';
        }

        const sourcesHtml = sources.map(source => {
            const score = Math.round(source.relevance_score * 100);
            const preview = source.text.length > 100 ? 
                source.text.substring(0, 100) + '...' : 
                source.text;
            
            const fullSource = this.sources.find(s => s.id === source.source_id);
            const isUrlSource = fullSource && fullSource.source_type === 'url' && fullSource.url;

            const sourceItemContent = `
                <div class="qa-source-item-header">
                    <span class="qa-source-name">${source.source_name || 'Unknown Source'}</span>
                    <span class="qa-source-score">${score}%</span>
                </div>
                <div class="qa-source-preview">${this.escapeHtml(preview)}</div>
            `;

            if (isUrlSource) {
                return `
                    <div class="qa-source-item">
                        <a href="${fullSource.url}" target="_blank" rel="noopener noreferrer" class="qa-source-link">
                            ${sourceItemContent}
                        </a>
                        <button class="btn btn-icon btn-sm qa-source-view-btn" onclick="app.viewQaSource('${source.source_id}')" title="View Content">
                            <i class="fas fa-eye"></i>
                        </button>
                    </div>
                `;
            } else {
                return `
                    <div class="qa-source-item">
                        <div onclick="app.viewQaSource('${source.source_id}')" style="cursor: pointer; flex-grow: 1;">
                            ${sourceItemContent}
                        </div>
                        <button class="btn btn-icon btn-sm qa-source-view-btn" onclick="app.viewQaSource('${source.source_id}')" title="View Content">
                            <i class="fas fa-eye"></i>
                        </button>
                    </div>
                `;
            }
        }).join('');

        return `
            <div class="qa-sources">
                <div class="qa-sources-title" onclick="this.nextElementSibling.classList.toggle('hidden'); this.querySelector('.qa-sources-toggle i').classList.toggle('fa-chevron-down'); this.querySelector('.qa-sources-toggle i').classList.toggle('fa-chevron-up');">
                    <i class="fas fa-book"></i>
                    <span>Sources (${sources.length})</span>
                    <button class="btn btn-icon btn-sm qa-sources-toggle">
                        <i class="fas fa-chevron-down"></i>
                    </button>
                </div>
                <div class="qa-sources-list hidden">
                    ${sourcesHtml}
                </div>
            </div>
        `;
    }

    viewQaSource(sourceId, chunkIndex) {
        if (!sourceId) return;
        
        // Find and view the source
        const source = this.sources.find(s => s.id === sourceId);
        if (source) {
            this.viewSource(source);
        }
    }

    scrollToBottom(element) {
        setTimeout(() => {
            element.scrollTop = element.scrollHeight;
        }, 100);
    }

    // Blog Post Generation Methods
    // ===== MIND MAP GENERATION =====
    
    openMindMapViewer() {
        if (!this.currentNotebook) {
            this.showToast('Error', 'Please select a notebook first', 'error');
            return;
        }

        // Open the mind map viewer in a new window
        const viewerUrl = `/api/notebooks/${this.currentNotebook.id}/mindmap/viewer`;
        window.open(viewerUrl, '_blank', 'width=1400,height=900');
    }

    // ===== BLOG POST GENERATION =====
    
    showBlogPostModal() {
        if (!this.currentNotebook) {
            this.showToast('Error', 'No notebook selected', 'error');
            return;
        }

        if (!this.sources || this.sources.length === 0) {
            this.showToast('Warning', 'This notebook has no sources. Add some sources to generate a meaningful blog post.', 'warning');
        }

        // Reset modal state
        this.resetBlogPostModal();
        
        // Set default title based on notebook
        document.getElementById('blogPostTitle').value = `${this.currentNotebook.name} - Insights and Analysis`;
        
        this.showModal('blogPostModal');
    }

    resetBlogPostModal() {
        // Reset form
        document.getElementById('blogPostForm').reset();
        
        // Hide progress and result sections
        document.getElementById('blogPostProgress').classList.add('hidden');
        document.getElementById('blogPostResult').classList.add('hidden');
        
        // Reset progress state
        document.querySelectorAll('.progress-step').forEach(step => {
            step.classList.remove('active', 'completed');
        });
        document.querySelector('.progress-fill').style.width = '0%';
        
        // Reset buttons
        document.getElementById('generateBlogPostSubmitBtn').classList.remove('hidden');
        document.getElementById('saveBlogPostBtn').classList.add('hidden');
        
        // Reset default values
        document.getElementById('blogPostTone').value = 'informative';
        document.getElementById('blogPostWordCount').value = '550';
        document.getElementById('includeReferences').checked = true;
    }

    async handleBlogPostSubmit(event) {
        event.preventDefault();
        
        if (!this.currentNotebook) {
            this.showToast('Error', 'No notebook selected', 'error');
            return;
        }

        const formData = new FormData(event.target);
        const blogPostData = {
            title: formData.get('title').trim(),
            prompt: formData.get('prompt')?.trim() || null,
            tone: formData.get('tone'),
            target_word_count: parseInt(formData.get('wordCount')),
            template: formData.get('template') || null,
            include_references: formData.get('includeReferences') === 'on'
        };

        if (!blogPostData.title) {
            this.showToast('Error', 'Please enter a title', 'error');
            return;
        }

        try {
            await this.generateBlogPost(blogPostData);
        } catch (error) {
            console.error('Blog post generation error:', error);
            this.showToast('Error', 'Failed to generate blog post', 'error');
            this.resetBlogPostGenerationUI();
        }
    }

    async generateBlogPost(blogPostData) {
        // Show progress section
        document.getElementById('blogPostProgress').classList.remove('hidden');
        document.getElementById('generateBlogPostSubmitBtn').classList.add('hidden');
        
        const startTime = Date.now();
        
        try {
            // Step 1: Extract content
            this.updateGenerationProgress('extract', 'active');
            await this.delay(500); // Visual feedback
            
            // Step 2: Generate content
            this.updateGenerationProgress('extract', 'completed');
            this.updateGenerationProgress('generate', 'active');
            this.updateProgressBar(40);
            
            // Make API call
            const response = await this.apiCall(`/notebooks/${this.currentNotebook.id}/generate-blog-post`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(blogPostData)
            });

            this.updateProgressBar(80);
            
            // Step 3: Complete
            this.updateGenerationProgress('generate', 'completed');
            this.updateGenerationProgress('complete', 'active');
            await this.delay(300);
            
            this.updateGenerationProgress('complete', 'completed');
            this.updateProgressBar(100);
            
            const endTime = Date.now();
            const generationTime = Math.round((endTime - startTime) / 1000);
            
            // Show result
            this.displayBlogPostResult(response, generationTime);
            
        } catch (error) {
            throw error;
        }
    }

    updateGenerationProgress(step, status) {
        const stepElement = document.querySelector(`[data-step="${step}"]`);
        if (stepElement) {
            stepElement.classList.remove('active', 'completed');
            if (status) {
                stepElement.classList.add(status);
            }
        }
    }

    updateProgressBar(percentage) {
        const progressFill = document.querySelector('.progress-fill');
        if (progressFill) {
            progressFill.style.width = `${percentage}%`;
        }
    }

    displayBlogPostResult(blogPost, generationTime) {
        // Hide progress, show result
        document.getElementById('blogPostProgress').classList.add('hidden');
        document.getElementById('blogPostResult').classList.remove('hidden');
        
        // Set content
        const contentDiv = document.getElementById('blogPostContent');
        contentDiv.innerHTML = this.formatBlogPostContent(blogPost.content);
        
        // Update stats
        const wordCount = this.countWords(blogPost.content);
        document.getElementById('blogPostWordCountDisplay').textContent = `${wordCount} words`;
        document.getElementById('blogPostGenTime').textContent = `Generated in ${generationTime}s`;
        
        // Store for later actions
        this.currentBlogPost = blogPost;
        
        // Show save button
        document.getElementById('saveBlogPostBtn').classList.remove('hidden');
        
        // Refresh outputs list to show the new blog post
        this.loadOutputs();
    }

    formatBlogPostContent(content) {
        // Convert markdown-like formatting to HTML
        return content
            .replace(/^# (.+)$/gm, '<h1>$1</h1>')
            .replace(/^## (.+)$/gm, '<h2>$1</h2>')
            .replace(/^### (.+)$/gm, '<h3>$1</h3>')
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/^(.+)$/gm, '<p>$1</p>')
            .replace(/<p><h([1-6])>/g, '<h$1>')
            .replace(/<\/h([1-6])><\/p>/g, '</h$1>')
            .replace(/<p><\/p>/g, '');
    }

    countWords(text) {
        // Remove HTML tags and count words
        const plainText = text.replace(/<[^>]*>/g, '');
        return plainText.trim().split(/\s+/).filter(word => word.length > 0).length;
    }

    async copyBlogPost() {
        if (!this.currentBlogPost) return;
        
        try {
            // Create plain text version
            const plainText = this.currentBlogPost.content
                .replace(/<[^>]*>/g, '')
                .replace(/&nbsp;/g, ' ')
                .replace(/&amp;/g, '&')
                .replace(/&lt;/g, '<')
                .replace(/&gt;/g, '>')
                .replace(/&quot;/g, '"');
            
            await navigator.clipboard.writeText(plainText);
            this.showToast('Success', 'Blog post copied to clipboard', 'success');
        } catch (error) {
            console.error('Copy error:', error);
            this.showToast('Error', 'Failed to copy blog post', 'error');
        }
    }

    downloadBlogPost() {
        if (!this.currentBlogPost) return;
        
        try {
            // Create plain text version
            const plainText = this.currentBlogPost.content
                .replace(/<[^>]*>/g, '')
                .replace(/&nbsp;/g, ' ')
                .replace(/&amp;/g, '&')
                .replace(/&lt;/g, '<')
                .replace(/&gt;/g, '>')
                .replace(/&quot;/g, '"');
            
            const blob = new Blob([plainText], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `${this.currentNotebook.name}_blog_post.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            this.showToast('Success', 'Blog post downloaded', 'success');
        } catch (error) {
            console.error('Download error:', error);
            this.showToast('Error', 'Failed to download blog post', 'error');
        }
    }

    editBlogPost() {
        if (!this.currentBlogPost) return;
        
        // Make content editable
        const contentDiv = document.getElementById('blogPostContent');
        contentDiv.contentEditable = true;
        contentDiv.classList.add('editing');
        contentDiv.focus();
        
        // Change button to save
        const editBtn = document.getElementById('editBlogPostBtn');
        editBtn.innerHTML = '<i class="fas fa-save"></i> Save Changes';
        editBtn.onclick = () => this.saveEditedBlogPost();
        
        this.showToast('Info', 'Blog post is now editable. Click "Save Changes" when done.', 'info');
    }

    saveEditedBlogPost() {
        const contentDiv = document.getElementById('blogPostContent');
        
        // Update current blog post content
        this.currentBlogPost.content = contentDiv.innerHTML;
        
        // Make content non-editable
        contentDiv.contentEditable = false;
        contentDiv.classList.remove('editing');
        
        // Restore edit button
        const editBtn = document.getElementById('editBlogPostBtn');
        editBtn.innerHTML = '<i class="fas fa-edit"></i> Edit';
        editBtn.onclick = () => this.editBlogPost();
        
        // Update word count
        const wordCount = this.countWords(this.currentBlogPost.content);
        document.getElementById('blogPostWordCountDisplay').textContent = `${wordCount} words`;
        
        this.showToast('Success', 'Blog post changes saved', 'success');
    }

    async saveBlogPost() {
        if (!this.currentBlogPost) return;
        
        try {
            // Blog post is already saved in the database when generated
            // This could trigger additional actions like adding to a collection
            this.showToast('Success', 'Blog post has been saved', 'success');
            this.closeModal('blogPostModal');
            
            // Refresh outputs to show the new blog post
            await this.loadOutputs();
        } catch (error) {
            console.error('Save error:', error);
            this.showToast('Error', 'Failed to save blog post', 'error');
        }
    }

    resetBlogPostGenerationUI() {
        // Reset progress section
        document.getElementById('blogPostProgress').classList.add('hidden');
        document.getElementById('generateBlogPostSubmitBtn').classList.remove('hidden');
        
        // Reset progress state
        document.querySelectorAll('.progress-step').forEach(step => {
            step.classList.remove('active', 'completed');
        });
        document.querySelector('.progress-fill').style.width = '0%';
    }

    async regenerateBlogPost() {
        if (!this.currentNotebook) {
            this.showToast('Error', 'No notebook selected', 'error');
            return;
        }

        // Extract current form data from the form
        const form = document.getElementById('blogPostForm');
        const formData = new FormData(form);
        const blogPostData = {
            title: formData.get('title').trim(),
            prompt: formData.get('prompt')?.trim() || null,
            tone: formData.get('tone'),
            target_word_count: parseInt(formData.get('wordCount')),
            template: formData.get('template') || null,
            include_references: formData.get('includeReferences') === 'on'
        };

        if (!blogPostData.title) {
            this.showToast('Error', 'Please enter a title', 'error');
            return;
        }

        // Show confirmation without changing UI state yet
        this.showConfirmation(
            'Regenerate Blog Post',
            'Are you sure you want to regenerate the blog post? This will replace the current content.',
            async () => {
                try {
                    // Show a brief "starting regeneration" message
                    this.showToast('Info', 'Starting regeneration...', 'info');
                    
                    // Small delay for better UX
                    await this.delay(300);
                    
                    // Now hide the result section and start regeneration
                    document.getElementById('blogPostResult').classList.add('hidden');
                    
                    // Reset the generation UI to show form and progress
                    document.getElementById('generateBlogPostSubmitBtn').classList.remove('hidden');
                    document.getElementById('saveBlogPostBtn').classList.add('hidden');
                    
                    // Start the generation process
                    await this.generateBlogPost(blogPostData);
                } catch (error) {
                    console.error('Blog post regeneration error:', error);
                    this.showToast('Error', 'Failed to regenerate blog post', 'error');
                    
                    // Restore the result section on error
                    document.getElementById('blogPostResult').classList.remove('hidden');
                    document.getElementById('generateBlogPostSubmitBtn').classList.add('hidden');
                    document.getElementById('saveBlogPostBtn').classList.remove('hidden');
                }
            }
        );
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Utility Methods
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) {
            return 'Today';
        } else if (diffDays === 1) {
            return 'Yesterday';
        } else if (diffDays < 7) {
            return `${diffDays} days ago`;
        } else {
            return date.toLocaleDateString();
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// Initialize the application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new DiscoveryApp();
});

// Global error handling
window.addEventListener('error', (e) => {
    console.error('Global error:', e.error);
    if (window.app) {
        window.app.showToast('Error', 'An unexpected error occurred', 'error');
    }
});

window.addEventListener('unhandledrejection', (e) => {
    console.error('Unhandled promise rejection:', e.reason);
    if (window.app) {
        window.app.showToast('Error', 'An unexpected error occurred', 'error');
    }
});