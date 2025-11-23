import { Component, inject, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { OutputApiService } from '../infrastructure/http/output-api.service';
import { NotebookApiService } from '../infrastructure/http/notebook-api.service';
import { OutputResponse, NotebookResponse } from '../core/models';
import { LoadingComponent } from '../shared/components/loading/loading.component';

@Component({
  selector: 'app-view-output',
  standalone: true,
  imports: [CommonModule, RouterModule, LoadingComponent],
  templateUrl: './view-output.html',
  styleUrl: './view-output.scss',
})
export class ViewOutput implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private outputService = inject(OutputApiService);
  private notebookService = inject(NotebookApiService);
  private cdr = inject(ChangeDetectorRef);

  output: OutputResponse | null = null;
  notebook: NotebookResponse | null = null;
  notebookId: string | null = null;
  outputId: string | null = null;
  isLoading = true;

  ngOnInit() {
    this.notebookId = this.route.snapshot.paramMap.get('id');
    this.outputId = this.route.snapshot.paramMap.get('outputId');
    
    if (this.outputId) {
      this.loadOutput(this.outputId);
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
        
        // Load notebook details
        this.notebookService.getNotebook(output.notebook_id).subscribe({
          next: (notebook) => {
            this.notebook = notebook;
            this.isLoading = false;
            this.cdr.detectChanges();
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
