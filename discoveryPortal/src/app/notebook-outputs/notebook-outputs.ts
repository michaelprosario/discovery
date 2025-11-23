import { Component, inject, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { NotebookApiService } from '../infrastructure/http/notebook-api.service';
import { OutputApiService } from '../infrastructure/http/output-api.service';
import { NotebookResponse, OutputSummaryResponse } from '../core/models';
import { LoadingComponent } from '../shared/components/loading/loading.component';

@Component({
  selector: 'app-notebook-outputs',
  standalone: true,
  imports: [CommonModule, RouterModule, LoadingComponent],
  templateUrl: './notebook-outputs.html',
  styleUrl: './notebook-outputs.scss',
})
export class NotebookOutputs implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private notebookService = inject(NotebookApiService);
  private outputService = inject(OutputApiService);
  private cdr = inject(ChangeDetectorRef);

  notebook: NotebookResponse | null = null;
  outputs: OutputSummaryResponse[] = [];
  notebookId: string | null = null;
  isLoading = true;

  ngOnInit() {
    this.notebookId = this.route.snapshot.paramMap.get('id');
    if (this.notebookId) {
      this.loadData(this.notebookId);
    }
  }

  viewOutput(output: OutputSummaryResponse) {
    if (this.notebookId && output.id) {
      this.router.navigate(['/edit-notebook', this.notebookId, 'outputs', output.id]);
    }
  }

  deleteOutput(output: OutputSummaryResponse) {
    if (confirm(`Are you sure you want to delete output "${output.title}"?`)) {
      if (output.id) {
        this.outputService.deleteOutput(output.id).subscribe({
          next: () => {
            this.loadData(this.notebookId!);
          },
          error: (err) => {
            console.error('Error deleting output', err);
            alert('Failed to delete output');
          }
        });
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
    return new Date(dateString).toLocaleDateString();
  }

  loadData(id: string) {
    this.isLoading = true;
    
    // Load notebook details
    this.notebookService.getNotebook(id).subscribe({
      next: (notebook) => {
        this.notebook = notebook;
        
        // Load outputs for this notebook
        this.outputService.listOutputs({ notebook_id: id }).subscribe({
          next: (response) => {
            this.outputs = response.outputs;
            this.isLoading = false;
            this.cdr.detectChanges();
          },
          error: (err) => {
            console.error('Error loading outputs', err);
            this.isLoading = false;
            this.cdr.detectChanges();
          }
        });
      },
      error: (err) => {
        console.error('Error loading notebook', err);
        this.isLoading = false;
        this.cdr.detectChanges();
      }
    });
  }
}
