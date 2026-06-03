import { Component, computed, input, output } from '@angular/core';
import { SuggestedRule } from '../../../../../../shared/models/dashboard.models';
import { ScoreRingComponent } from '../../../../../../shared/ui/score-ring/score-ring';

@Component({
  selector: 'app-step-running',
  standalone: true,
  imports: [ScoreRingComponent],
  templateUrl: './step-running.html',
  styleUrl: './step-running.css',
})
export class StepRunningComponent {
  readonly progress = input<number>(0);
  readonly rules = input<SuggestedRule[]>([]);
  readonly projectId = input<string | null>(null);
  readonly createProject = output<void>();
  readonly back = output<void>();

  protected readonly isComplete = computed(() => this.progress() >= 100);
  protected readonly progressPct = computed(() => `${Math.min(100, Math.round(this.progress()))}%`);

  protected readonly firstScore = 91;
  protected readonly passedChecks = computed(() =>
    this.rules().filter((r) => r.enabled && r.id !== 'r2' && r.id !== 'r4').length,
  );
}
