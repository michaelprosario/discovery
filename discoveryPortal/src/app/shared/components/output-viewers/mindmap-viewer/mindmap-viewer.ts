import { Component, Input, OnInit, AfterViewInit, ElementRef, ViewChild, ChangeDetectorRef, inject } from '@angular/core';
import { CommonModule } from '@angular/common';

// Declare global markmap types
declare const markmap: {
  Transformer: any;
  Markmap: any;
};

@Component({
  selector: 'app-mindmap-viewer',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './mindmap-viewer.html',
  styleUrl: './mindmap-viewer.scss',
})
export class MindMapViewer implements OnInit, AfterViewInit {
  @Input() content: string = '';
  @ViewChild('markmapContainer', { static: false }) markmapContainer?: ElementRef<SVGElement>;
  
  private cdr = inject(ChangeDetectorRef);
  markmapInstance: any = null;

  ngOnInit() {
    console.log('MindMapViewer initialized with content length:', this.content?.length);
  }

  ngAfterViewInit() {
    if (this.content && this.markmapContainer) {
      console.log('MindMapViewer AfterViewInit: scheduling render');
      setTimeout(() => this.renderMindMap(), 300);
    }
  }

  renderMindMap() {
    if (!this.content || !this.markmapContainer) {
      console.log('Cannot render mindmap: missing content or container');
      return;
    }

    try {
      console.log('Rendering mindmap...');
      
      if (typeof markmap === 'undefined') {
        console.error('markmap is not loaded');
        setTimeout(() => this.renderMindMap(), 500);
        return;
      }

      const { Transformer, Markmap } = markmap;
      
      if (!Transformer || !Markmap) {
        console.error('Transformer or Markmap not available');
        return;
      }

      const transformer = new Transformer();
      const { root } = transformer.transform(this.content);
      
      this.markmapInstance = Markmap.create(
        this.markmapContainer.nativeElement,
        {
          color: (node: any) => {
            const colors = ['#5B8FF9', '#5AD8A6', '#5D7092', '#F6BD16', '#E86452', '#6DC8EC', '#945FB9', '#FF9845'];
            return colors[node.depth % colors.length];
          },
          duration: 500,
          maxWidth: 300,
        },
        root
      );
      
      console.log('Mindmap rendered successfully');
    } catch (error) {
      console.error('Error rendering mindmap:', error);
    }
  }

  expandAll() {
    if (this.markmapInstance) {
      const expandNode = (node: any) => {
        if (node.children && node.children.length > 0) {
          if (!node.payload) node.payload = {};
          node.payload.fold = 0;
          node.children.forEach(expandNode);
        }
      };

      if (this.markmapInstance.state && this.markmapInstance.state.data) {
        expandNode(this.markmapInstance.state.data);
        this.markmapInstance.renderData();
      }
    }
  }

  collapseAll() {
    if (this.markmapInstance) {
      const collapseNode = (node: any) => {
        if (node.children && node.children.length > 0) {
          if (!node.payload) node.payload = {};
          node.payload.fold = 1;
          node.children.forEach(collapseNode);
        }
      };

      if (this.markmapInstance.state && this.markmapInstance.state.data) {
        collapseNode(this.markmapInstance.state.data);
        this.markmapInstance.renderData();
      }
    }
  }
}
