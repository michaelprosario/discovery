import { Component, inject, OnInit, ChangeDetectorRef, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { QaApiService } from '../infrastructure/http/qa-api.service';
import { NotebookApiService } from '../infrastructure/http/notebook-api.service';
import { SourceApiService } from '../infrastructure/http/source-api.service';
import { ChatMessage, NotebookResponse, QaSourceItem, SourceResponse } from '../core/models';
import { LoadingComponent } from '../shared/components/loading/loading.component';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, LoadingComponent],
  templateUrl: './chat.html',
  styleUrl: './chat.scss',
})
export class ChatComponent implements OnInit {
  @ViewChild('messagesContainer') private messagesContainer!: ElementRef;
  
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private qaService = inject(QaApiService);
  private notebookService = inject(NotebookApiService);
  private sourceService = inject(SourceApiService);
  private cdr = inject(ChangeDetectorRef);

  notebook: NotebookResponse | null = null;
  sources: SourceResponse[] = [];
  notebookId: string | null = null;
  isLoading = true;
  
  // Chat state
  messages: ChatMessage[] = [];
  currentQuestion = '';
  isProcessing = false;

  ngOnInit() {
    this.notebookId = this.route.snapshot.paramMap.get('id');
    if (this.notebookId) {
      this.loadNotebookData(this.notebookId);
    }
  }

  ngAfterViewChecked() {
    this.scrollToBottom();
  }

  private scrollToBottom(): void {
    try {
      if (this.messagesContainer) {
        this.messagesContainer.nativeElement.scrollTop = 
          this.messagesContainer.nativeElement.scrollHeight;
      }
    } catch(err) { }
  }

  loadNotebookData(id: string) {
    this.isLoading = true;
    this.notebookService.getNotebook(id).subscribe({
      next: (notebook) => {
        this.notebook = notebook;
        this.loadSources(id);
      },
      error: (err) => {
        console.error('Error loading notebook', err);
        this.isLoading = false;
        alert('Failed to load notebook');
      }
    });
  }

  loadSources(notebookId: string) {
    this.sourceService.listSourcesByNotebook({ notebook_id: notebookId }).subscribe({
      next: (response) => {
        this.sources = response.sources;
        this.isLoading = false;
        this.cdr.detectChanges();
        
        // Add welcome message
        if (this.messages.length === 0) {
          this.addAssistantMessage(
            `Hello! I'm your research assistant for "${this.notebook?.name}". I can help you explore and understand the ${this.sources.length} source(s) you've added to this notebook. What would you like to know?`,
            []
          );
        }
      },
      error: (err) => {
        console.error('Error loading sources', err);
        this.isLoading = false;
      }
    });
  }

  askQuestion() {
    if (!this.currentQuestion.trim() || this.isProcessing || !this.notebookId) {
      return;
    }

    const question = this.currentQuestion.trim();
    this.currentQuestion = '';

    // Add user message
    this.addUserMessage(question);

    // Add loading message
    const loadingMessageId = this.addLoadingMessage();

    // Call API
    this.isProcessing = true;
    this.qaService.askQuestion(this.notebookId, {
      question: question,
      max_sources: 5,
      temperature: 0.3,
      max_tokens: 1500
    }).subscribe({
      next: (response) => {
        this.removeLoadingMessage(loadingMessageId);
        this.addAssistantMessage(response.answer, response.sources);
        this.isProcessing = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error asking question', err);
        this.removeLoadingMessage(loadingMessageId);
        this.addAssistantMessage(
          'Sorry, I encountered an error while processing your question. Please try again.',
          []
        );
        this.isProcessing = false;
        this.cdr.detectChanges();
      }
    });
  }

  private addUserMessage(content: string) {
    const message: ChatMessage = {
      id: this.generateId(),
      role: 'user',
      content,
      timestamp: new Date()
    };
    this.messages.push(message);
    this.cdr.detectChanges();
  }

  private addAssistantMessage(content: string, sources: QaSourceItem[]) {
    const message: ChatMessage = {
      id: this.generateId(),
      role: 'assistant',
      content,
      sources,
      timestamp: new Date(),
      showSources: false // Collapsed by default
    };
    this.messages.push(message);
    this.cdr.detectChanges();
  }

  toggleSources(message: ChatMessage) {
    message.showSources = !message.showSources;
    this.cdr.detectChanges();
  }

  private addLoadingMessage(): string {
    const id = this.generateId();
    const message: ChatMessage = {
      id,
      role: 'assistant',
      content: 'Thinking...',
      timestamp: new Date(),
      isLoading: true
    };
    this.messages.push(message);
    this.cdr.detectChanges();
    return id;
  }

  private removeLoadingMessage(id: string) {
    const index = this.messages.findIndex(m => m.id === id);
    if (index !== -1) {
      this.messages.splice(index, 1);
    }
  }

  private generateId(): string {
    return `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  openSourceLink(sourceId: string | null) {
    if (!sourceId) return;
    
    const source = this.sources.find(s => s.id === sourceId);
    if (source && source.source_type === 'url' && source.url) {
      window.open(source.url, '_blank');
    } else {
      alert('Source link not available');
    }
  }

  getSourceName(sourceId: string | null): string {
    if (!sourceId) return 'Unknown Source';
    const source = this.sources.find(s => s.id === sourceId);
    return source?.name || 'Unknown Source';
  }

  clearChat() {
    if (confirm('Are you sure you want to clear the chat history?')) {
      this.messages = [];
      if (this.notebook) {
        this.addAssistantMessage(
          `Chat cleared. I'm ready to help you explore "${this.notebook.name}" again. What would you like to know?`,
          []
        );
      }
    }
  }

  handleKeyPress(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.askQuestion();
    }
  }

  backToNotebook() {
    if (this.notebookId) {
      this.router.navigate(['/edit-notebook', this.notebookId]);
    }
  }
}
