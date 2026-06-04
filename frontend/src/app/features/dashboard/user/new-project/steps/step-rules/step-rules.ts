import { Component, input, OnInit, output, signal } from '@angular/core';
import { SuggestedRule, DetectedColumn } from '../../../../../../shared/models/dashboard.models';
import { RuleItemComponent } from './rule-item/rule-item';
import { AddRuleModalComponent } from './add-rule-modal/add-rule-modal';

@Component({
  selector: 'app-step-rules',
  standalone: true,
  imports: [RuleItemComponent, AddRuleModalComponent],
  templateUrl: './step-rules.html',
  styleUrl: './step-rules.css',
})
export class StepRulesComponent implements OnInit {
  readonly columns = input<DetectedColumn[]>([]);
  readonly rules = input<SuggestedRule[]>([]);
  readonly back = output<void>();
  readonly runChecks = output<SuggestedRule[]>();

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
    this.runChecks.emit(this.localRules());
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
