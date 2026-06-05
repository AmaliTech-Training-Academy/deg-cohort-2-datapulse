import { Component, inject, input, OnInit, output, signal } from '@angular/core';
import { Store } from '@ngrx/store';
import { SuggestedRule, DetectedColumn } from '../../../../../../shared/models/dashboard.models';
import { StepErrorComponent } from '../../../../../../shared/ui/step-error/step-error';
import { RuleItemComponent } from './rule-item/rule-item';
import { AddRuleModalComponent } from './add-rule-modal/add-rule-modal';
import * as ProjectCreationActions from '../../../../store/project-creation/project-creation.actions';
import {
  selectRulesLoading,
  selectRulesError,
} from '../../../../store/project-creation/project-creation.selectors';

@Component({
  selector: 'app-step-rules',
  standalone: true,
  imports: [RuleItemComponent, AddRuleModalComponent, StepErrorComponent],
  templateUrl: './step-rules.html',
  styleUrl: './step-rules.css',
})
export class StepRulesComponent implements OnInit {
  readonly columns = input<DetectedColumn[]>([]);
  readonly rules = input<SuggestedRule[]>([]);
  // Outputs kept for backwards compat — never emitted; store drives navigation.
  readonly back = output<void>();
  readonly runChecks = output<SuggestedRule[]>();

  private readonly store = inject(Store);

  protected readonly rulesLoading = this.store.selectSignal(selectRulesLoading);
  protected readonly rulesError = this.store.selectSignal(selectRulesError);

  protected localRules = signal<SuggestedRule[]>([]);
  protected isModalOpen = signal(false);
  protected editingRule = signal<SuggestedRule | null>(null);

  ngOnInit(): void {
    this.localRules.set(this.rules().map((r) => ({ ...r })));
  }

  protected toggleRule(id: string): void {
    this.localRules.update((rules) =>
      rules.map((r) => (r.id === id ? { ...r, enabled: !r.enabled } : r)),
    );
  }

  protected enabledCount(): number {
    return this.localRules().filter((r) => r.enabled).length;
  }

  protected onRunChecks(): void {
    this.store.dispatch(ProjectCreationActions.saveRules({ rules: this.localRules() }));
  }

  protected onBack(): void {
    this.back.emit();
  }

  protected onAddRule(): void {
    this.editingRule.set(null);
    this.isModalOpen.set(true);
  }

  protected onEditRule(id: string): void {
    const rule = this.localRules().find((r) => r.id === id) ?? null;
    this.editingRule.set(rule);
    this.isModalOpen.set(true);
  }

  protected onDeleteRule(id: string): void {
    this.localRules.update((rules) => rules.filter((r) => r.id !== id));
  }

  protected onRuleSaved(rule: SuggestedRule): void {
    const isEdit = this.localRules().some((r) => r.id === rule.id);
    if (isEdit) {
      this.localRules.update((rules) => rules.map((r) => (r.id === rule.id ? rule : r)));
    } else {
      this.localRules.update((rules) => [...rules, rule]);
    }
    this.isModalOpen.set(false);
    this.editingRule.set(null);
  }

  protected onModalCancelled(): void {
    this.isModalOpen.set(false);
    this.editingRule.set(null);
  }

  protected columnTypeLabel(type: string): string {
    return type;
  }
}
