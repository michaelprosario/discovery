import { Component, signal, inject } from '@angular/core';
import { MobileMenuService } from './core/services/mobile-menu.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.html',
  styleUrl: './app.scss',
  standalone: false
})
export class AppComponent {
  protected readonly title = signal('discoveryPortal');
  private mobileMenuService = inject(MobileMenuService);
  
  toggleMobileMenu() {
    this.mobileMenuService.toggle();
  }
}
