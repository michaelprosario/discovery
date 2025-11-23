import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { SourceApiService } from '../infrastructure/http/source-api.service';
import { ImportTextSourceRequest } from '../core/models';

@Component({
  selector: 'app-add-text-source',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './add-text-source.html',
  styleUrl: './add-text-source.scss'
})
export class AddTextSource implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private sourceService = inject(SourceApiService);

  notebookId: string | null = null;
  title: string = '';
  content: string = '';
  isSubmitting = false;

  ngOnInit() {
    this.notebookId = this.route.snapshot.paramMap.get('id');
    if (!this.notebookId) {
      console.error('No notebook ID provided');
      this.router.navigate(['/list-notebooks']);
    }
  }

  onSubmit() {
    if (!this.notebookId || !this.title || !this.content) {
      return;
    }

    this.isSubmitting = true;
    const request: ImportTextSourceRequest = {
      notebook_id: this.notebookId,
      title: this.title,
      content: this.content
    };

    this.sourceService.importTextSource(request).subscribe({
      next: () => {
        this.isSubmitting = false;
        this.router.navigate(['/edit-notebook', this.notebookId]);
      },
      error: (err) => {
        console.error('Error adding text source', err);
        this.isSubmitting = false;
        alert('Failed to add text source');
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
