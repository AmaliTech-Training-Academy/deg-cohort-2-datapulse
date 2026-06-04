import { Component, input, output } from '@angular/core';
import { SuggestedRule } from '../../../../../../../shared/models/dashboard.models';

@Component({
  selector: 'app-rule-item',
  standalone: true,
  templateUrl: './rule-item.html',
  styleUrl: './rule-item.css',
})
export class RuleItemComponent {
  readonly rule = input.required<SuggestedRule>();

  readonly toggled = output<string>();
  readonly editClicked = output<string>();
  readonly deleteClicked = output<string>();

  protected ruleTypeIcon(type: string): string {
    switch (type) {
      case 'uniqueness':
        return 'M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z';
      case 'null_check':
        return 'M7 20l4-16m2 16l4-16M6 9h14M4 15h14';
      case 'type_check':
        return 'M4 6h16M4 12h16M4 18h7';
      case 'range_check':
        return 'M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6-10l6-3m0 16l5.447-2.724A1 1 0 0021 16.382V5.618a1 1 0 00-1.447-.894L15 7m0 13V7';
      default:
        return 'M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4';
    }
  }
}
