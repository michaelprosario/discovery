import { ComponentFixture, TestBed } from '@angular/core/testing';
import { LoadingComponent } from './loading.component';

describe('LoadingComponent', () => {
  let component: LoadingComponent;
  let fixture: ComponentFixture<LoadingComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LoadingComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(LoadingComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should display default loading message', () => {
    const compiled = fixture.nativeElement;
    const message = compiled.querySelector('.loading-message');
    expect(message.textContent).toContain('Loading...');
  });

  it('should display custom message', () => {
    component.message = 'Please wait...';
    fixture.detectChanges();
    const compiled = fixture.nativeElement;
    const message = compiled.querySelector('.loading-message');
    expect(message.textContent).toContain('Please wait...');
  });

  it('should apply medium size by default', () => {
    const compiled = fixture.nativeElement;
    const wrapper = compiled.querySelector('.spinner-wrapper');
    expect(wrapper.classList.contains('spinner-medium')).toBeTruthy();
  });

  it('should apply small size when specified', () => {
    component.size = 'small';
    fixture.detectChanges();
    const compiled = fixture.nativeElement;
    const wrapper = compiled.querySelector('.spinner-wrapper');
    expect(wrapper.classList.contains('spinner-small')).toBeTruthy();
  });

  it('should apply large size when specified', () => {
    component.size = 'large';
    fixture.detectChanges();
    const compiled = fixture.nativeElement;
    const wrapper = compiled.querySelector('.spinner-wrapper');
    expect(wrapper.classList.contains('spinner-large')).toBeTruthy();
  });

  it('should not have overlay class by default', () => {
    const compiled = fixture.nativeElement;
    const container = compiled.querySelector('.loading-container');
    expect(container.classList.contains('overlay')).toBeFalsy();
  });

  it('should apply overlay class when overlay is true', () => {
    component.overlay = true;
    fixture.detectChanges();
    const compiled = fixture.nativeElement;
    const container = compiled.querySelector('.loading-container');
    expect(container.classList.contains('overlay')).toBeTruthy();
  });

  it('should hide message when message is empty', () => {
    component.message = '';
    fixture.detectChanges();
    const compiled = fixture.nativeElement;
    const message = compiled.querySelector('.loading-message');
    expect(message).toBeNull();
  });
});
