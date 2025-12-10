import { Injectable, signal } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class MobileMenuService {
  private _isOpen = signal(false);
  
  readonly isOpen = this._isOpen.asReadonly();
  
  toggle() {
    this._isOpen.update(value => !value);
  }
  
  open() {
    this._isOpen.set(true);
  }
  
  close() {
    this._isOpen.set(false);
  }
}
