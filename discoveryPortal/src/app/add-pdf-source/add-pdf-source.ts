import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { SourceApiService } from '../infrastructure/http/source-api.service';
import { ImportFileSourceRequest } from '../core/models';

@Component({
  selector: 'app-add-pdf-source',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './add-pdf-source.html',
  styleUrl: './add-pdf-source.scss'
})
export class AddPdfSource implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private sourceService = inject(SourceApiService);

  notebookId: string | null = null;
  name: string = '';
  selectedFile: File | null = null;
  selectedFileName: string = '';
  isSubmitting = false;
  isDragOver = false;

  ngOnInit() {
    this.notebookId = this.route.snapshot.paramMap.get('id');
    if (!this.notebookId) {
      console.error('No notebook ID provided');
      this.router.navigate(['/list-notebooks']);
    }
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.handleFile(input.files[0]);
    }
  }

  onDragOver(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver = true;
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver = false;
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver = false;

    if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
      this.handleFile(event.dataTransfer.files[0]);
    }
  }

  handleFile(file: File) {
    // Check if file is PDF
    if (file.type !== 'application/pdf') {
      alert('Please select a PDF file');
      return;
    }

    this.selectedFile = file;
    this.selectedFileName = file.name;
    
    // Auto-populate name if empty
    if (!this.name) {
      this.name = file.name.replace('.pdf', '');
    }
  }

  triggerFileInput() {
    const fileInput = document.getElementById('pdfFile') as HTMLInputElement;
    fileInput?.click();
  }

  async onSubmit() {
    if (!this.notebookId || !this.name || !this.selectedFile) {
      return;
    }

    this.isSubmitting = true;

    try {
      // Convert file to base64
      const base64Content = await this.fileToBase64(this.selectedFile);
      
      const request: ImportFileSourceRequest = {
        notebook_id: this.notebookId,
        name: this.name,
        file_content: base64Content,
        file_type: 'pdf'
      };

      this.sourceService.importFileSource(request).subscribe({
        next: () => {
          this.isSubmitting = false;
          this.router.navigate(['/edit-notebook', this.notebookId]);
        },
        error: (err) => {
          console.error('Error adding PDF source', err);
          this.isSubmitting = false;
          alert('Failed to add PDF source');
        }
      });
    } catch (error) {
      console.error('Error reading file', error);
      this.isSubmitting = false;
      alert('Failed to read PDF file');
    }
  }

  private fileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        if (typeof reader.result === 'string') {
          // Remove the data URL prefix (e.g., "data:application/pdf;base64,")
          const base64 = reader.result.split(',')[1];
          resolve(base64);
        } else {
          reject(new Error('Failed to read file as base64'));
        }
      };
      reader.onerror = error => reject(error);
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
