import { Component, input } from '@angular/core';

// Inline error banner used by the project-creation wizard steps to surface
// API failures without restructuring existing step templates.
@Component({
  selector: 'app-step-error',
  standalone: true,
  template: `
    @if (message()) {
      <div class="step-error" role="alert">
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
        {{ message() }}
      </div>
    }
  `,
  styles: [
    `
      .step-error {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 8px 12px;
        border-radius: var(--radius-md, 6px);
        background: color-mix(in srgb, var(--color-danger) 12%, transparent);
        color: var(--color-danger);
        font-size: 13px;
        margin-top: 8px;
      }
    `,
  ],
})
export class StepErrorComponent {
  readonly message = input<string | null>(null);
}
