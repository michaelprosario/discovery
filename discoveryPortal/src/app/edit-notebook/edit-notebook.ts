import { Component, inject, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { forkJoin } from 'rxjs';
import { NotebookApiService } from '../infrastructure/http/notebook-api.service';
import { SourceApiService } from '../infrastructure/http/source-api.service';
import { NotebookResponse, SourceResponse } from '../core/models';
import { LoadingComponent } from '../shared/components/loading/loading.component';

@Component({
  selector: 'app-edit-notebook',
  standalone: true,
  imports: [CommonModule, RouterModule, LoadingComponent],
  templateUrl: './edit-notebook.html',
  styleUrl: './edit-notebook.scss',
})
export class EditNotebook implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private notebookService = inject(NotebookApiService);
  private sourceService = inject(SourceApiService);
  private cdr = inject(ChangeDetectorRef);

  notebook: NotebookResponse | null = null;
  sources: SourceResponse[] = [];
  notebookId: string | null = null;
  isLoading = true;

  ngOnInit() {
    this.notebookId = this.route.snapshot.paramMap.get('id');
    if (this.notebookId) {
      this.loadData(this.notebookId);
    }
  }

  openSource(source: SourceResponse) {
    // console.log(source)
    if(source.source_type === 'url') 
    {
      if (source.url) {
        window.open(source.url, '_blank');
      }
    }
    else
    {
      alert('fix me - implement opening non-url sources');
    }
  }

  deleteSource(source: SourceResponse) {
    if (confirm(`Are you sure you want to delete source "${source.name}"?`)) {
      if (this.notebookId && source.id) {
        this.sourceService.deleteSource(source.id, this.notebookId).subscribe({
          next: () => {
            this.loadData(this.notebookId!);
          },
          error: (err) => {
            console.error('Error deleting source', err);
            alert('Failed to delete source');
          }
        });
      }
    }
  }

  deleteNotebook() {
    if (this.notebook && confirm(`Are you sure you want to delete notebook "${this.notebook.name}"?`)) {
      if (this.notebookId) {
        this.notebookService.deleteNotebook(this.notebookId, true).subscribe({
          next: () => {
            this.router.navigate(['/list-notebooks']);
          },
          error: (err) => {
            console.error('Error deleting notebook', err);
            alert('Failed to delete notebook');
          }
        });
      }
    }
  }

  loadData(id: string) {
    this.isLoading = true;
    forkJoin({
      notebook: this.notebookService.getNotebook(id),
      sources: this.sourceService.listSourcesByNotebook({ notebook_id: id })
    }).subscribe({
      next: (results) => {
        this.notebook = results.notebook;
        this.sources = results.sources.sources;
        this.isLoading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error loading data', err);
        this.isLoading = false;
        this.cdr.detectChanges();
      }
    });
  }
}
