import { Component, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { SuggestedRule, DetectedColumn } from '../../../../shared/models/dashboard.models';
import { StepUploadComponent, UploadData } from './steps/step-upload/step-upload';
import { StepRulesComponent } from './steps/step-rules/step-rules';
import { StepRunningComponent } from './steps/step-running/step-running';

@Component({
  selector: 'app-new-project',
  standalone: true,
  imports: [RouterLink, StepUploadComponent, StepRulesComponent, StepRunningComponent],
  templateUrl: './new-project.html',
  styleUrl: './new-project.css',
})
export class NewProjectComponent {
  protected readonly currentStep = signal<1 | 2 | 3>(1);
  protected readonly projectName = signal('');
  protected readonly fileName = signal('');
  protected readonly columns = signal<DetectedColumn[]>([]);
  protected readonly rules = signal<SuggestedRule[]>([]);
  protected readonly progress = signal(0);
  protected readonly projectId = signal<string | null>(null);

  private intervalId?: ReturnType<typeof setInterval>;

  constructor(private readonly router: Router) {}

  protected onUploadContinue(data: UploadData): void {
    this.projectName.set(data.name);
    this.fileName.set(data.fileName);
    this.columns.set(data.columns);
    this.rules.set(data.rules);
    this.currentStep.set(2);
  }

  protected onRunChecks(enabledRules: SuggestedRule[]): void {
    this.rules.set(enabledRules);
    this.currentStep.set(3);
    this.simulateProgress();
  }

  protected onBack(): void {
    const current = this.currentStep();
    if (current > 1) this.currentStep.set((current - 1) as 1 | 2 | 3);
  }

  protected onCreateProject(): void {
    this.router.navigate(['/dashboard/projects']);
  }

  private simulateProgress(): void {
    this.progress.set(0);
    this.intervalId = setInterval(() => {
      const current = this.progress();
      if (current >= 100) {
        clearInterval(this.intervalId);
        this.projectId.set(`new-${Date.now()}`);
      } else {
        this.progress.set(Math.min(100, current + Math.random() * 8 + 3));
      }
    }, 200);
  }
}
