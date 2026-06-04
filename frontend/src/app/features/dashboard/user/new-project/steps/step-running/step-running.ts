import { Component, computed, effect, inject, input, OnDestroy, OnInit, output, signal } from '@angular/core';
import { Store } from '@ngrx/store';
import { SuggestedRule } from '../../../../../../shared/models/dashboard.models';
import { ScoreRingComponent } from '../../../../../../shared/ui/score-ring/score-ring';
import { StepErrorComponent } from '../../../../../../shared/ui/step-error/step-error';
import * as ProjectCreationActions from '../../../../store/project-creation/project-creation.actions';
import {
  selectRunCheckLoading,
  selectRunCheckError,
  selectRunCheckScore,
} from '../../../../store/project-creation/project-creation.selectors';

@Component({
  selector: 'app-step-running',
  standalone: true,
  imports: [ScoreRingComponent, StepErrorComponent],
  templateUrl: './step-running.html',
  styleUrl: './step-running.css',
})
export class StepRunningComponent implements OnInit, OnDestroy {
  readonly progress = input<number>(0);
  readonly rules = input<SuggestedRule[]>([]);
  readonly projectId = input<string | null>(null);
  readonly createProject = output<void>();
  readonly back = output<void>();

  private readonly store = inject(Store);
  private intervalId?: ReturnType<typeof setInterval>;

  private readonly runCheckLoading = this.store.selectSignal(selectRunCheckLoading);
  protected readonly runCheckError = this.store.selectSignal(selectRunCheckError);
  private readonly runCheckScore = this.store.selectSignal(selectRunCheckScore);

  protected readonly localProgress = signal(0);
  protected readonly progressPct = computed(
    () => `${Math.min(100, Math.round(this.localProgress()))}%`,
  );

  // Complete when the API has returned a score — not when progress hits 100%.
  protected readonly isComplete = computed(
    () => this.runCheckScore() !== null && !this.runCheckLoading(),
  );

  protected readonly passedChecks = computed(
    () => this.rules().filter((r) => r.enabled).length,
  );

  // Getter so Angular template tracks the signal read without a binding change.
  protected get firstScore(): number {
    return this.runCheckScore() ?? 0;
  }

  constructor() {
    // Jump to 100% as soon as the API succeeds so the bar fills before the
    // completion card appears.
    effect(() => {
      if (this.runCheckScore() !== null && !this.runCheckLoading()) {
        clearInterval(this.intervalId);
        this.localProgress.set(100);
      }
    });
  }

  ngOnInit(): void {
    this.store.dispatch(ProjectCreationActions.runChecks());
    this.startProgress();
  }

  ngOnDestroy(): void {
    clearInterval(this.intervalId);
  }

  private startProgress(): void {
    this.localProgress.set(0);
    this.intervalId = setInterval(() => {
      const current = this.localProgress();
      if (current >= 90) {
        clearInterval(this.intervalId);
      } else {
        this.localProgress.set(Math.min(90, current + Math.random() * 8 + 3));
      }
    }, 200);
  }
}
