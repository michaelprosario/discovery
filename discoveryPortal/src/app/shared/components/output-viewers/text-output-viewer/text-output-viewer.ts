import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-text-output-viewer',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './text-output-viewer.html',
  styleUrl: './text-output-viewer.scss',
})
export class TextOutputViewer {
  @Input() content: string = '';
  @Input() outputType: string = 'blog_post';
}
