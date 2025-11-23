import { Component, inject, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { NotebookApiService } from '../infrastructure/http/notebook-api.service';
import { GenerateBlogPostRequest, OutputResponse } from '../core/models';
import { LoadingComponent } from '../shared/components/loading/loading.component';

@Component({
  selector: 'app-new-blog-post',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, LoadingComponent],
  templateUrl: './new-blog-post.html',
  styleUrl: './new-blog-post.scss'
})
export class NewBlogPost implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private notebookService = inject(NotebookApiService);
  private cdr = inject(ChangeDetectorRef);

  notebookId: string | null = null;
  title: string = '';
  customPrompt: string = '';
  tone: string = 'informative';
  wordCount: number = 550;
  structure: string = 'default';
  
  isGenerating = false;
  generatedBlogPost: OutputResponse | null = null;

  toneOptions = [
    { value: 'informative', label: 'Informative' },
    { value: 'casual', label: 'Casual' },
    { value: 'formal', label: 'Formal' },
    { value: 'conversational', label: 'Conversational' },
    { value: 'academic', label: 'Academic' }
  ];

  wordCountOptions = [
    { value: 550, label: '550 words' },
    { value: 700, label: '700 words' },
    { value: 1000, label: '1000 words' }
  ];

  structureOptions = [
    { value: 'default', label: 'Default' },
    { value: 'how-to', label: 'How To' },
    { value: 'list-article', label: 'List Article' },
    { value: 'comparison', label: 'Comparison' },
    { value: 'case-study', label: 'Case Study' },
    { value: 'opinion', label: 'Opinion' }
  ];

  ngOnInit() {
    this.notebookId = this.route.snapshot.paramMap.get('id');
    if (!this.notebookId) {
      console.error('No notebook ID provided');
      this.router.navigate(['/list-notebooks']);
    }
  }

  onGenerate() {
    if (!this.notebookId || !this.title) {
      return;
    }

    this.isGenerating = true;
    this.generatedBlogPost = null;

    // Build the prompt based on structure and custom prompt
    let fullPrompt = this.customPrompt;
    if (this.structure !== 'default') {
      const structurePrompts: Record<string, string> = {
        'how-to': 'Create a step-by-step how-to guide. ',
        'list-article': 'Create a listicle format article. ',
        'comparison': 'Create a comparison article analyzing different aspects. ',
        'case-study': 'Create a case study with problem, solution, and results. ',
        'opinion': 'Create an opinion piece with clear arguments and evidence. '
      };
      fullPrompt = structurePrompts[this.structure] + (fullPrompt || '');
    }

    const request: GenerateBlogPostRequest = {
      title: this.title,
      prompt: fullPrompt || null,
      target_word_count: this.wordCount,
      tone: this.tone,
      include_references: true
    };

    this.notebookService.generateBlogPost(this.notebookId, request).subscribe({
      next: (response) => {
        this.generatedBlogPost = response;
        this.isGenerating = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error generating blog post', err);
        this.isGenerating = false;
        this.cdr.detectChanges();
        alert('Failed to generate blog post. Please ensure the notebook has sources and try again.');
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

  onBackToNotebook() {
    if (this.notebookId) {
      this.router.navigate(['/edit-notebook', this.notebookId]);
    } else {
      this.router.navigate(['/list-notebooks']);
    }
  }
}
