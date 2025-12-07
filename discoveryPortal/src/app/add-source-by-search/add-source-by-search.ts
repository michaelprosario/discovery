import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { SourceApiService } from '../infrastructure/http/source-api.service';
import { AddSourcesBySearchRequest, AddSourcesBySearchResponse, AddSourcesBySearchResult } from '../core/models';

@Component({
  selector: 'app-add-source-by-search',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './add-source-by-search.html',
  styleUrl: './add-source-by-search.scss'
})
export class AddSourceBySearch implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private sourceService = inject(SourceApiService);

  notebookId: string | null = null;
  searchPhrase: string = '';
  maxResults: number = 5;
  isSearching = false;
  errorMessage: string = '';
  searchResponse: AddSourcesBySearchResponse | null = null;

  ngOnInit() {
    this.notebookId = this.route.snapshot.paramMap.get('id');
    if (!this.notebookId) {
      console.error('No notebook ID provided');
      this.router.navigate(['/list-notebooks']);
    }
  }

  onSubmit() {
    this.errorMessage = '';
    this.searchResponse = null;

    if (!this.notebookId || !this.searchPhrase.trim()) {
      this.errorMessage = 'Search phrase is required';
      return;
    }

    if (this.maxResults < 1 || this.maxResults > 10) {
      this.errorMessage = 'Max results must be between 1 and 10';
      return;
    }

    this.isSearching = true;
    const request: AddSourcesBySearchRequest = {
      notebook_id: this.notebookId,
      search_phrase: this.searchPhrase.trim(),
      max_results: this.maxResults
    };

    this.sourceService.addSourcesBySearch(request).subscribe({
      next: (response) => {
        this.isSearching = false;
        this.searchResponse = response;
      },
      error: (err) => {
        console.error('Error searching and adding sources', err);
        this.isSearching = false;
        this.errorMessage = err.error?.detail?.error || err.error?.detail || 'Failed to search and add sources';
      }
    });
  }

  onCancel() {
    if (this.notebookId) {
      this.router.navigate(['/edit-notebook', this.notebookId]);
    } else {
      this.router.navigate(['/list-notebooks']);
    }
  }

  onDone() {
    if (this.notebookId) {
      this.router.navigate(['/edit-notebook', this.notebookId]);
    } else {
      this.router.navigate(['/list-notebooks']);
    }
  }

  onSearchAgain() {
    this.searchResponse = null;
    this.searchPhrase = '';
    this.errorMessage = '';
  }

  getSuccessCount(): number {
    return this.searchResponse?.results.filter(r => r.success).length || 0;
  }

  getFailureCount(): number {
    return this.searchResponse?.results.filter(r => !r.success).length || 0;
  }
}
