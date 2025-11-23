import { Component, inject, OnInit, ChangeDetectorRef, AfterViewInit, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { OutputApiService } from '../infrastructure/http/output-api.service';
import { NotebookApiService } from '../infrastructure/http/notebook-api.service';
import { OutputResponse, NotebookResponse } from '../core/models';
import { LoadingComponent } from '../shared/components/loading/loading.component';

// Declare global markmap types
declare const markmap: {
  Transformer: any;
  Markmap: any;
};

@Component({
  selector: 'app-view-output',
  standalone: true,
  imports: [CommonModule, RouterModule, LoadingComponent],
  templateUrl: './view-output.html',
  styleUrl: './view-output.scss',
})
export class ViewOutput implements OnInit, AfterViewInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private outputService = inject(OutputApiService);
  private notebookService = inject(NotebookApiService);
  private cdr = inject(ChangeDetectorRef);

  @ViewChild('markmapContainer', { static: false }) markmapContainer?: ElementRef<SVGElement>;

  output: OutputResponse | null = null;
  notebook: NotebookResponse | null = null;
  notebookId: string | null = null;
  outputId: string | null = null;
  isLoading = true;
  isMindMap = false;
  markmapInstance: any = null;

  ngOnInit() {
    this.notebookId = this.route.snapshot.paramMap.get('id');
    this.outputId = this.route.snapshot.paramMap.get('outputId');
    
    if (this.outputId) {
      this.loadOutput(this.outputId);
    }
  }

  ngAfterViewInit() {
    // Render mindmap if applicable - wait a bit longer for the view to be fully ready
    if (this.isMindMap && this.output?.content && this.markmapContainer) {
      console.log('ngAfterViewInit: scheduling mindmap render');
      setTimeout(() => this.renderMindMap(), 300);
    }
  }

  deleteOutput() {
    if (this.output && confirm(`Are you sure you want to delete output "${this.output.title}"?`)) {
      if (this.outputId) {
        this.outputService.deleteOutput(this.outputId).subscribe({
          next: () => {
            this.router.navigate(['/edit-notebook', this.notebookId, 'outputs']);
          },
          error: (err) => {
            console.error('Error deleting output', err);
            alert('Failed to delete output');
          }
        });
      }
    }
  }

  copyToClipboard() {
    if (this.output?.content) {
      navigator.clipboard.writeText(this.output.content).then(() => {
        alert('Content copied to clipboard!');
      }).catch(err => {
        console.error('Failed to copy content', err);
        alert('Failed to copy content');
      });
    }
  }

  downloadMarkdown() {
    if (!this.output?.content) {
      return;
    }

    const blob = new Blob([this.output.content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${this.output.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}-${Date.now()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  renderMindMap() {
    if (!this.output?.content || !this.markmapContainer) {
      console.log('Cannot render mindmap: missing content or container', {
        hasContent: !!this.output?.content,
        hasContainer: !!this.markmapContainer
      });
      return;
    }

    try {
      console.log('Attempting to render mindmap with content:', this.output.content.substring(0, 100));
      
      // Wait for markmap to be loaded
      if (typeof markmap === 'undefined') {
        console.error('markmap is not loaded');
        setTimeout(() => this.renderMindMap(), 500);
        return;
      }

      const { Transformer, Markmap } = markmap;
      
      if (!Transformer || !Markmap) {
        console.error('Transformer or Markmap not available');
        return;
      }

      const transformer = new Transformer();
      const { root } = transformer.transform(this.output.content);
      
      console.log('Transformed markdown to tree:', root);
      
      this.markmapInstance = Markmap.create(
        this.markmapContainer.nativeElement,
        {
          color: (node: any) => {
            // Use depth-based coloring
            const colors = ['#5B8FF9', '#5AD8A6', '#5D7092', '#F6BD16', '#E86452', '#6DC8EC', '#945FB9', '#FF9845'];
            return colors[node.depth % colors.length];
          },
          duration: 500,
          maxWidth: 300,
        },
        root
      );
      
      console.log('Mindmap instance created successfully');
    } catch (error) {
      console.error('Error rendering mindmap:', error);
    }
  }

  expandAll() {
    if (this.markmapInstance) {
      const expandNode = (node: any) => {
        if (node.children && node.children.length > 0) {
          if (!node.payload) node.payload = {};
          node.payload.fold = 0;
          node.children.forEach(expandNode);
        }
      };

      if (this.markmapInstance.state && this.markmapInstance.state.data) {
        expandNode(this.markmapInstance.state.data);
        this.markmapInstance.renderData();
      }
    }
  }

  collapseAll() {
    if (this.markmapInstance) {
      const collapseNode = (node: any) => {
        if (node.children && node.children.length > 0) {
          if (!node.payload) node.payload = {};
          node.payload.fold = 1;
          node.children.forEach(collapseNode);
        }
      };

      if (this.markmapInstance.state && this.markmapInstance.state.data) {
        collapseNode(this.markmapInstance.state.data);
        this.markmapInstance.renderData();
      }
    }
  }

  getStatusClass(status: string): string {
    const statusMap: Record<string, string> = {
      'draft': 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
      'generating': 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
      'completed': 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      'failed': 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
    };
    return statusMap[status] || statusMap['draft'];
  }

  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleString();
  }

  loadOutput(id: string) {
    this.isLoading = true;
    
    this.outputService.getOutput(id).subscribe({
      next: (output) => {
        this.output = output;
        this.isMindMap = output.output_type === 'mind_map';
        
        console.log('Output loaded:', { 
          type: output.output_type, 
          isMindMap: this.isMindMap,
          contentLength: output.content?.length 
        });
        
        // Load notebook details
        this.notebookService.getNotebook(output.notebook_id).subscribe({
          next: (notebook) => {
            this.notebook = notebook;
            this.isLoading = false;
            this.cdr.detectChanges();
            
            // Render mindmap after view is ready and data is loaded
            if (this.isMindMap && this.markmapContainer) {
              console.log('Data loaded, scheduling mindmap render');
              setTimeout(() => this.renderMindMap(), 500);
            }
          },
          error: (err) => {
            console.error('Error loading notebook', err);
            this.isLoading = false;
            this.cdr.detectChanges();
          }
        });
      },
      error: (err) => {
        console.error('Error loading output', err);
        this.isLoading = false;
        this.cdr.detectChanges();
      }
    });
  }
}
