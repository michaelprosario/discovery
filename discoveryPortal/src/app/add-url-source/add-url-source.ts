import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { SourceApiService } from '../infrastructure/http/source-api.service';
import { ImportUrlSourceRequest } from '../core/models';

@Component({
  selector: 'app-add-url-source',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './add-url-source.html',
  styleUrl: './add-url-source.scss'
})
export class AddUrlSource implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private sourceService = inject(SourceApiService);

  notebookId: string | null = null;
  url: string = '';
  title: string = '';
  isSubmitting = false;
  errorMessage: string = '';

  ngOnInit() {
    this.notebookId = this.route.snapshot.paramMap.get('id');
    if (!this.notebookId) {
      console.error('No notebook ID provided');
      this.router.navigate(['/list-notebooks']);
    }
  }

  isValidUrl(urlString: string): boolean {
    try {
      const url = new URL(urlString);
      return url.protocol === 'http:' || url.protocol === 'https:';
    } catch {
      return false;
    }
  }

  onSubmit() {
    this.errorMessage = '';

    if (!this.notebookId || !this.url) {
      this.errorMessage = 'URL is required';
      return;
    }

    if (!this.isValidUrl(this.url)) {
      this.errorMessage = 'Please enter a valid URL (must start with http:// or https://)';
      return;
    }

    this.isSubmitting = true;
    const request: ImportUrlSourceRequest = {
      notebook_id: this.notebookId,
      url: this.url,
      title: this.title || null
    };

    this.sourceService.importUrlSource(request).subscribe({
      next: () => {
        this.isSubmitting = false;
        this.router.navigate(['/edit-notebook', this.notebookId]);
      },
      error: (err) => {
        console.error('Error adding URL source', err);
        this.isSubmitting = false;
        this.errorMessage = err.error?.detail || 'Failed to add URL source';
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
}
