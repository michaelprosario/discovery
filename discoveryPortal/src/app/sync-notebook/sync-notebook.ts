import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { VectorSearchApiService } from '../infrastructure/http/vector-search-api.service';
import { LoadingComponent } from '../shared/components/loading/loading.component';

@Component({
  selector: 'app-sync-notebook',
  standalone: true,
  imports: [CommonModule, LoadingComponent],
  templateUrl: './sync-notebook.html',
  styleUrl: './sync-notebook.scss',
})
export class SyncNotebook implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private vectorSearchService = inject(VectorSearchApiService);

  notebookId: string | null = null;
  isLoading = true;
  errorMessage: string | null = null;

  ngOnInit() {
    this.notebookId = this.route.snapshot.paramMap.get('id');
    if (this.notebookId) {
      this.syncWithVectorDatabase(this.notebookId);
    } else {
      this.errorMessage = 'No notebook ID provided';
      this.isLoading = false;
    }
  }

  syncWithVectorDatabase(notebookId: string) {
    this.isLoading = true;
    this.errorMessage = null;

    this.vectorSearchService.ingestNotebook(notebookId).subscribe({
      next: (response) => {
        console.log('Sync completed:', response);
        this.isLoading = false;
        
        // Navigate back to edit-notebook after a brief delay to show success
        setTimeout(() => {
          this.router.navigate(['/edit-notebook', notebookId]);
        }, 1500);
      },
      error: (err) => {
        console.error('Error syncing with vector database:', err);
        this.errorMessage = err.error?.detail || 'Failed to sync with vector database';
        this.isLoading = false;
      }
    });
  }

  goBack() {
    if (this.notebookId) {
      this.router.navigate(['/edit-notebook', this.notebookId]);
    } else {
      this.router.navigate(['/list-notebooks']);
    }
  }
}
