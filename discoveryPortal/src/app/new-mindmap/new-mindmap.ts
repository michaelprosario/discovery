import { Component, inject, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { MindMapApiService } from '../infrastructure/http/mindmap-api.service';
import { OutputApiService } from '../infrastructure/http/output-api.service';
import { GenerateMindMapRequest, MindMapResponse, CreateOutputRequest, UpdateOutputRequest } from '../core/models';
import { LoadingComponent } from '../shared/components/loading/loading.component';

@Component({
  selector: 'app-new-mindmap',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, LoadingComponent],
  templateUrl: './new-mindmap.html',
  styleUrl: './new-mindmap.scss'
})
export class NewMindMap implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private mindmapService = inject(MindMapApiService);
  private outputService = inject(OutputApiService);
  private cdr = inject(ChangeDetectorRef);

  notebookId: string | null = null;
  prompt: string = '';
  maxSources: number = 10;
  
  isGenerating = false;
  generatedMindMap: MindMapResponse | null = null;
  isSavingOutput = false;

  ngOnInit() {
    this.notebookId = this.route.snapshot.paramMap.get('id');
    if (!this.notebookId) {
      console.error('No notebook ID provided');
      this.router.navigate(['/list-notebooks']);
    }
  }

  onGenerate() {
    if (!this.notebookId || !this.prompt.trim()) {
      return;
    }

    this.isGenerating = true;
    this.generatedMindMap = null;

    const request: GenerateMindMapRequest = {
      prompt: this.prompt,
      max_sources: this.maxSources,
      temperature: 0.4,
      max_tokens: 2000
    };

    this.mindmapService.generateMindMap(this.notebookId, request).subscribe({
      next: (response) => {
        this.generatedMindMap = response;
        this.isGenerating = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error generating mindmap', err);
        this.isGenerating = false;
        this.cdr.detectChanges();
        alert('Failed to generate mindmap. Please ensure the notebook has ingested sources and try again.');
      }
    });
  }

  onSaveAsOutput() {
    if (!this.notebookId || !this.generatedMindMap) {
      return;
    }

    this.isSavingOutput = true;

    const outputRequest: CreateOutputRequest = {
      title: `Mind Map: ${this.prompt.substring(0, 50)}`,
      output_type: 'mind_map',
      prompt: this.generatedMindMap.prompt
    };

    this.outputService.createOutput(this.notebookId, outputRequest).subscribe({
      next: (output) => {
        // Update the output with the mindmap content
        const updateRequest: UpdateOutputRequest = {
          content: this.generatedMindMap!.markdown_outline
        };

        this.outputService.updateOutput(output.id, updateRequest).subscribe({
          next: (updatedOutput) => {
            this.isSavingOutput = false;
            this.cdr.detectChanges();
            // Navigate to view the output
            this.router.navigate(['/edit-notebook', this.notebookId, 'outputs', updatedOutput.id]);
          },
          error: (err) => {
            console.error('Error updating output content', err);
            this.isSavingOutput = false;
            this.cdr.detectChanges();
            alert('Failed to save mindmap content');
          }
        });
      },
      error: (err) => {
        console.error('Error creating output', err);
        this.isSavingOutput = false;
        this.cdr.detectChanges();
        alert('Failed to create mindmap output');
      }
    });
  }

  onDownloadMarkdown() {
    if (!this.generatedMindMap) {
      return;
    }

    const blob = new Blob([this.generatedMindMap.markdown_outline], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `mindmap-${Date.now()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  onCancel() {
    if (this.notebookId) {
      this.router.navigate(['/edit-notebook', this.notebookId]);
    } else {
      this.router.navigate(['/list-notebooks']);
    }
  }

  onBackToNotebook() {
    if (this.notebookId) {
      this.router.navigate(['/edit-notebook', this.notebookId]);
    } else {
      this.router.navigate(['/list-notebooks']);
    }
  }
}
