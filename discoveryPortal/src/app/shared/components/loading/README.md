# Loading Component

A reusable loading spinner component for displaying loading states throughout the application.

## Features

- 🎨 Animated multi-ring spinner
- 📏 Three size options: small, medium, large
- 🎭 Optional overlay mode for full-screen loading
- 💬 Customizable loading message
- 🎯 Standalone component (no module import required)

## Usage

### Basic Usage

```typescript
import { LoadingComponent } from '@app/shared';

@Component({
  selector: 'app-my-component',
  standalone: true,
  imports: [LoadingComponent],
  template: `
    <app-loading></app-loading>
  `
})
export class MyComponent {}
```

### With Custom Message

```html
<app-loading message="Fetching data..."></app-loading>
```

### Different Sizes

```html
<!-- Small spinner -->
<app-loading size="small" message="Loading..."></app-loading>

<!-- Medium spinner (default) -->
<app-loading size="medium" message="Loading..."></app-loading>

<!-- Large spinner -->
<app-loading size="large" message="Loading..."></app-loading>
```

### Full-Screen Overlay

```html
<app-loading 
  [overlay]="true" 
  message="Please wait while we process your request...">
</app-loading>
```

### Conditional Display

```typescript
@Component({
  selector: 'app-my-component',
  standalone: true,
  imports: [LoadingComponent, CommonModule],
  template: `
    <app-loading 
      *ngIf="isLoading" 
      [overlay]="true"
      message="Loading data...">
    </app-loading>
    
    <div *ngIf="!isLoading">
      <!-- Your content here -->
    </div>
  `
})
export class MyComponent {
  isLoading = false;

  loadData() {
    this.isLoading = true;
    this.dataService.getData().subscribe({
      next: (data) => {
        // Handle data
        this.isLoading = false;
      },
      error: () => {
        this.isLoading = false;
      }
    });
  }
}
```

## API

### Inputs

| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `message` | `string` | `'Loading...'` | Message to display below the spinner |
| `size` | `'small' \| 'medium' \| 'large'` | `'medium'` | Size of the spinner |
| `overlay` | `boolean` | `false` | Whether to show as a full-screen overlay |

## Examples

### In a Data Table

```html
<div class="table-container">
  <app-loading *ngIf="loadingData" size="small" message="Fetching records..."></app-loading>
  <table *ngIf="!loadingData">
    <!-- Table content -->
  </table>
</div>
```

### In a Form Submission

```typescript
@Component({
  template: `
    <form (ngSubmit)="onSubmit()">
      <!-- Form fields -->
      <button type="submit" [disabled]="submitting">Submit</button>
    </form>
    
    <app-loading 
      *ngIf="submitting" 
      [overlay]="true"
      message="Submitting form...">
    </app-loading>
  `
})
export class MyFormComponent {
  submitting = false;

  onSubmit() {
    this.submitting = true;
    // Submit logic
  }
}
```

### Multiple Loading States

```typescript
@Component({
  template: `
    <div class="dashboard">
      <div class="section">
        <app-loading *ngIf="loadingUsers" size="small"></app-loading>
        <user-list *ngIf="!loadingUsers" [users]="users"></user-list>
      </div>
      
      <div class="section">
        <app-loading *ngIf="loadingReports" size="small"></app-loading>
        <report-list *ngIf="!loadingReports" [reports]="reports"></report-list>
      </div>
    </div>
  `
})
export class DashboardComponent {
  loadingUsers = false;
  loadingReports = false;
  // ...
}
```

## Styling

The component uses SCSS with BEM-like naming conventions. The colors can be customized by modifying the `loading.component.scss` file.

Default spinner colors:
- Ring 1: `#007bff`
- Ring 2: `#0056b3`
- Ring 3: `#004085`
- Ring 4: `#003366`

## Animation

The spinner uses CSS animations with a cubic-bezier timing function for smooth rotation. Each ring has a staggered animation delay for a cascading effect.
