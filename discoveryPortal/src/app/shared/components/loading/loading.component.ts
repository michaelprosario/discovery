import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

/**
 * Loading component with animated spinner
 * Can be used to display loading state throughout the application
 */
@Component({
  selector: 'app-loading',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './loading.component.html',
  styleUrls: ['./loading.component.scss']
})
export class LoadingComponent {
  /**
   * Optional message to display below the spinner
   */
  @Input() message: string = 'Loading...';

  /**
   * Size of the spinner: 'small', 'medium', or 'large'
   */
  @Input() size: 'small' | 'medium' | 'large' = 'medium';

  /**
   * Whether to show the overlay background
   */
  @Input() overlay: boolean = false;
}
