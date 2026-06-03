import { Component, computed, input } from '@angular/core';

@Component({
  selector: 'app-score-ring',
  standalone: true,
  templateUrl: './score-ring.html',
  styleUrl: './score-ring.css',
})
export class ScoreRingComponent {
  readonly score = input<number>(0);
  readonly size = input<number>(120);
  readonly strokeWidth = input<number>(10);

  protected readonly ring = computed(() => {
    const s = this.score();
    const sz = this.size();
    const sw = this.strokeWidth();
    const r = (sz - sw) / 2;
    const circ = 2 * Math.PI * r;
    const clamped = Math.max(0, Math.min(100, s));
    const offset = circ * (1 - clamped / 100);
    const color =
      s >= 85 ? 'var(--color-success)' : s >= 70 ? 'var(--color-warning)' : 'var(--color-danger)';
    return { r, circ, offset, color, cx: sz / 2, cy: sz / 2 };
  });
}
