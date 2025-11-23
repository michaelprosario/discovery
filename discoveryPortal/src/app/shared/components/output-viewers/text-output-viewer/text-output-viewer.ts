import { Component, Input, OnChanges, SimpleChanges, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { marked } from 'marked';

@Component({
  selector: 'app-text-output-viewer',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './text-output-viewer.html',
  styleUrl: './text-output-viewer.scss',
})
export class TextOutputViewer implements OnChanges {
  @Input() content: string = '';
  @Input() outputType: string = 'blog_post';
  
  renderedContent: SafeHtml = '';

  constructor(
    private sanitizer: DomSanitizer,
    private cdr: ChangeDetectorRef
  ) {}

  async ngOnChanges(changes: SimpleChanges) {
    if (changes['content'] && this.content) {
      const html = await marked.parse(this.content);
      this.renderedContent = this.sanitizer.sanitize(1, html) || '';
      this.cdr.detectChanges();
    }
  }
}
