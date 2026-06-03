import { Component, input, OnInit, output, signal } from '@angular/core';
import { SuggestedRule, DetectedColumn } from '../../../../../../shared/models/dashboard.models';

@Component({
  selector: 'app-step-rules',
  standalone: true,
  templateUrl: './step-rules.html',
  styleUrl: './step-rules.css',
})
export class StepRulesComponent implements OnInit {
  readonly columns = input<DetectedColumn[]>([]);
  readonly rules = input<SuggestedRule[]>([]);
  readonly back = output<void>();
  readonly runChecks = output<SuggestedRule[]>();

  protected localRules = signal<SuggestedRule[]>([]);

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

  protected ruleTypeIcon(type: string): string {
    switch (type) {
      case 'uniqueness': return 'M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z';
      case 'null_check': return 'M7 20l4-16m2 16l4-16M6 9h14M4 15h14';
      case 'type_check': return 'M4 6h16M4 12h16M4 18h7';
      case 'range_check': return 'M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6-10l6-3m0 16l5.447-2.724A1 1 0 0021 16.382V5.618a1 1 0 00-1.447-.894L15 7m0 13V7';
      default: return 'M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4';
    }
  }

  protected columnTypeLabel(type: string): string {
    return type;
  }
}
