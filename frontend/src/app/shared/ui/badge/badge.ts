import { Component, computed, input } from '@angular/core';

export type BadgeVariant = 'success' | 'warning' | 'danger' | 'info' | 'neutral';

@Component({
  selector: 'app-badge',
  standalone: true,
  templateUrl: './badge.html',
  styleUrl: './badge.css',
})
export class BadgeComponent {
  readonly label = input<string>('');
  readonly variant = input<BadgeVariant>('neutral');
  readonly dot = input<boolean>(true);

  protected readonly classes = computed(() => `badge badge--${this.variant()}`);
}
