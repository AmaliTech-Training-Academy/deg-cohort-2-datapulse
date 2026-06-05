import { Component, computed, inject, OnDestroy, OnInit, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { Store } from '@ngrx/store';
import { SuggestedRule, DetectedColumn } from '../../../../shared/models/dashboard.models';
import { StepUploadComponent, UploadData } from './steps/step-upload/step-upload';
import { StepRulesComponent } from './steps/step-rules/step-rules';
import { StepRunningComponent } from './steps/step-running/step-running';
import * as ProjectCreationActions from '../../store/project-creation/project-creation.actions';
import {
  selectCurrentStep,
  selectUploadedColumns,
  selectConfirmedRules,
} from '../../store/project-creation/project-creation.selectors';

@Component({
  selector: 'app-new-project',
  standalone: true,
  imports: [RouterLink, StepUploadComponent, StepRulesComponent, StepRunningComponent],
  templateUrl: './new-project.html',
  styleUrl: './new-project.css',
})
export class NewProjectComponent implements OnInit, OnDestroy {
  private readonly store = inject(Store);
  private readonly router = inject(Router);

  protected readonly currentStep = this.store.selectSignal(selectCurrentStep);

  private readonly uploadedColumnNames = this.store.selectSignal(selectUploadedColumns);
  private readonly confirmedRulesFromStore = this.store.selectSignal(selectConfirmedRules);

  protected readonly columns = computed((): DetectedColumn[] =>
    this.uploadedColumnNames().map((name) => ({ name, type: 'String' as const })),
  );

  protected readonly rules = computed((): SuggestedRule[] => {
    const confirmed = this.confirmedRulesFromStore();
    return confirmed.length > 0 ? confirmed : this.generateSuggestedRules(this.columns());
  });

  // Kept for template compat — step-running manages its own animation internally.
  protected readonly progress = signal(0);
  protected readonly projectId = signal<string | null>(null);

  ngOnInit(): void {
    this.store.dispatch(ProjectCreationActions.resetProjectCreation());
  }

  ngOnDestroy(): void {
    this.store.dispatch(ProjectCreationActions.resetProjectCreation());
  }

  // Dead handler: step-upload now dispatches uploadDataset directly.
  // The (continue) binding in the template is kept to avoid removing the output.
  protected onUploadContinue(_data: UploadData): void {
    // noop — store drives navigation via uploadDatasetSuccess
  }

  // Dead handler: step-rules now dispatches saveRules directly.
  protected onRunChecks(_rules: SuggestedRule[]): void {
    // noop — store drives navigation via saveRulesSuccess
  }

  protected onBack(): void {
    const step = this.currentStep();
    if (step === 2) this.store.dispatch(ProjectCreationActions.goBackToUpload());
    else if (step === 3) this.store.dispatch(ProjectCreationActions.goBackToRules());
  }

  protected onCreateProject(): void {
    this.store.dispatch(ProjectCreationActions.resetProjectCreation());
    void this.router.navigate(['/dashboard/projects']);
  }

  private generateSuggestedRules(cols: DetectedColumn[]): SuggestedRule[] {
    const rules: SuggestedRule[] = [];
    let counter = 0;

    if (cols.length > 0) {
      counter++;
      rules.push({
        id: `auto-${counter}`,
        name: `Unique ${cols[0].name}`,
        type: 'uniqueness',
        description: 'Detected as a potential primary key — no duplicate values allowed',
        column: cols[0].name,
        enabled: true,
      });
    }

    cols.forEach((col) => {
      counter++;
      rules.push({
        id: `auto-${counter}`,
        name: `No null ${col.name}`,
        type: 'null_check',
        description: `Flag any missing values in ${col.name}`,
        column: col.name,
        enabled: true,
      });
    });

    return rules;
  }
}
