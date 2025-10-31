// Discovery Research Notebook - JavaScript Application

class DiscoveryApp {
    constructor() {
        this.currentNotebook = null;
        this.notebooks = [];
        this.sources = [];
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
        document.getElementById('generateOutputBtn').addEventListener('click', () => this.generateOutput());
        
        // Source actions
        document.getElementById('addFileSourceBtn').addEventListener('click', () => this.showAddFileSourceModal());
        document.getElementById('addUrlSourceBtn').addEventListener('click', () => this.showAddUrlSourceModal());
        document.getElementById('addBySearchBtn').addEventListener('click', () => this.showSearchSourceModal());
        document.getElementById('sourcesFilter').addEventListener('input', () => this.filterSources());
        document.getElementById('sourceTypeFilter').addEventListener('change', () => this.filterSources());
        
        // Forms
        document.getElementById('notebookForm').addEventListener('submit', (e) => this.handleNotebookSubmit(e));
        document.getElementById('fileSourceForm').addEventListener('submit', (e) => this.handleFileSourceSubmit(e));
        document.getElementById('urlSourceForm').addEventListener('submit', (e) => this.handleUrlSourceSubmit(e));
        document.getElementById('searchSourceForm').addEventListener('submit', (e) => this.handleSearchSourceSubmit(e));
        
        // File input auto-name
        document.getElementById('sourceFile').addEventListener('change', () => this.autoFillFileName());
        
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
                        <span>${source.source_type === 'file' ? source.file_type?.toUpperCase() || 'FILE' : 'URL'}</span>
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
            
            // For demo purposes, we'll simulate file upload
            // In real implementation, you'd upload the file to a server endpoint
            const fileType = file.name.split('.').pop().toLowerCase();
            
            const data = {
                notebook_id: this.currentNotebook.id,
                name: name,
                file_path: `/uploads/${file.name}`, // Simulated path
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
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        modal.classList.remove('active');
        document.body.style.overflow = '';
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