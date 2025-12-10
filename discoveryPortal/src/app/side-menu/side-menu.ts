import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { UserMenuComponent } from '../shared/user-menu/user-menu.component';
import { AuthService } from '../core/services/auth.service';
import { MobileMenuService } from '../core/services/mobile-menu.service';

@Component({
  selector: 'app-side-menu',
  templateUrl: './side-menu.html',
  styleUrl: './side-menu.scss',
  standalone: false
})
export class SideMenu {
  private authService = inject(AuthService);
  protected mobileMenuService = inject(MobileMenuService);
  user$ = this.authService.user$;
  
  closeMobileMenu() {
    this.mobileMenuService.close();
  }
}
