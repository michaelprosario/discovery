import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators, FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { NotebookApiService } from '../infrastructure/http/notebook-api.service';
import { CreateNotebookRequest } from '../core/models/notebook.models';
import { lastValueFrom } from 'rxjs';

@Component({
  selector: 'app-new-notebook',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule],
  templateUrl: './new-notebook.html',
  styleUrl: './new-notebook.scss',
})
export class NewNotebook {
  private fb = inject(FormBuilder);
  private router = inject(Router);
  private notebookApiService = inject(NotebookApiService);

  notebookForm: FormGroup;
  isSubmitting = false;
  errorMessage = '';
  tagInput = '';

  constructor() {
    this.notebookForm = this.fb.group({
      name: ['', [Validators.required, Validators.minLength(1), Validators.maxLength(255)]],
      description: [''],
      tags: [[]]
    });
  }

  get name() {
    return this.notebookForm.get('name');
  }

  get description() {
    return this.notebookForm.get('description');
  }

  get tags() {
    return this.notebookForm.get('tags')?.value as string[];
  }

  addTag(): void {
    const trimmedTag = this.tagInput.trim();
    if (trimmedTag && !this.tags.includes(trimmedTag)) {
      const currentTags = this.tags;
      this.notebookForm.patchValue({
        tags: [...currentTags, trimmedTag]
      });
      this.tagInput = '';
    }
  }

  removeTag(tag: string): void {
    const currentTags = this.tags;
    this.notebookForm.patchValue({
      tags: currentTags.filter(t => t !== tag)
    });
  }

  async onSave(): Promise<void> {
    // Reset error message
    this.errorMessage = '';

    // Validate form
    if (this.notebookForm.invalid) {
      this.notebookForm.markAllAsTouched();
      this.errorMessage = 'Please fill out all required fields correctly.';
      return;
    }

    this.isSubmitting = true;

    try {
      const formValue = this.notebookForm.value;
      const request: CreateNotebookRequest = {
        name: formValue.name,
        description: formValue.description || null,
        tags: formValue.tags.length > 0 ? formValue.tags : null
      };

      const response = await lastValueFrom(this.notebookApiService.createNotebook(request));
      
      if (response && response.id) {
        // Navigate back to list on success
        this.router.navigate(['/list-notebooks']);
      } else {
        this.errorMessage = 'Failed to create notebook. Please try again.';
        this.isSubmitting = false;
      }
    } catch (error: any) {
      console.error('Error creating notebook:', error);
      this.errorMessage = error?.error?.detail || 'An error occurred while creating the notebook. Please try again.';
      this.isSubmitting = false;
    }
  }

  onCancel(): void {
    this.router.navigate(['/list-notebooks']);
  }
}
