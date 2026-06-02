import { Component, computed, input } from '@angular/core';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

@Component({
  selector: 'app-button',
  standalone: true,
  templateUrl: './button.html',
  styleUrl: './button.css',
})
export class ButtonComponent {
  readonly variant = input<ButtonVariant>('primary');
  readonly size = input<ButtonSize>('md');
  readonly loading = input<boolean>(false);
  readonly disabled = input<boolean>(false);
  readonly fullWidth = input<boolean>(false);
  readonly type = input<'button' | 'submit' | 'reset'>('button');

  protected readonly classes = computed(
    () =>
      `btn btn--${this.variant()} btn--${this.size()}` +
      (this.fullWidth() ? ' btn--full' : '') +
      (this.loading() ? ' btn--loading' : ''),
  );
}
