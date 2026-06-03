import { Component, computed, input } from '@angular/core';

@Component({
  selector: 'app-progress-bar',
  standalone: true,
  templateUrl: './progress-bar.html',
  styleUrl: './progress-bar.css',
})
export class ProgressBarComponent {
  readonly label = input<string>('');
  readonly value = input<number>(0);
  readonly color = input<string | null>(null);

  protected readonly displayPercent = computed(() => `${Math.round(this.value())}%`);

  protected readonly fillColor = computed(() => {
    if (this.color()) return this.color()!;
    const v = this.value();
    if (v >= 85) return 'var(--color-success)';
    if (v >= 70) return 'var(--color-warning)';
    return 'var(--color-danger)';
  });
}
