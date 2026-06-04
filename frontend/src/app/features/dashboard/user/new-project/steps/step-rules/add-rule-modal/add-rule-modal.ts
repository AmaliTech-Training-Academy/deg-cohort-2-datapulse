import { Component, effect, inject, input, output } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { SuggestedRule, DetectedColumn } from '../../../../../../../shared/models/dashboard.models';

@Component({
  selector: 'app-add-rule-modal',
  standalone: true,
  imports: [ReactiveFormsModule],
  templateUrl: './add-rule-modal.html',
  styleUrl: './add-rule-modal.css',
})
export class AddRuleModalComponent {
  readonly isOpen = input<boolean>(false);
  readonly columns = input<DetectedColumn[]>([]);
  readonly existingRules = input<SuggestedRule[]>([]);
  readonly editingRule = input<SuggestedRule | null>(null);

  readonly saved = output<SuggestedRule>();
  readonly cancelled = output<void>();

  private readonly fb = inject(FormBuilder);

  protected form = this.fb.group({
    ruleType: ['', Validators.required],
    column: ['', Validators.required],
    params: [''],
  });

  protected duplicateError = false;

  protected readonly ruleTypes = [
    { value: 'null_check', label: 'Null check' },
    { value: 'type_check', label: 'Type check' },
    { value: 'range_check', label: 'Range check' },
    { value: 'uniqueness', label: 'Uniqueness' },
  ];

  protected readonly paramsPlaceholders: Record<string, string> = {
    type_check: 'e.g. email, integer, date',
    range_check: 'e.g. min=0, max=120',
  };

  constructor() {
    effect(() => {
      const editing = this.editingRule();
      if (editing) {
        this.form.patchValue({
          ruleType: editing.type,
          column: editing.column,
          params: editing.params ?? '',
        });
      } else {
        this.form.reset({ ruleType: '', column: '', params: '' });
      }
      this.duplicateError = false;
    });
  }

  protected get showParams(): boolean {
    const t = this.form.get('ruleType')?.value;
    return t === 'type_check' || t === 'range_check';
  }

  protected get paramsPlaceholder(): string {
    return this.paramsPlaceholders[this.form.get('ruleType')?.value ?? ''] ?? '';
  }

  protected onOverlayClick(event: MouseEvent): void {
    if ((event.target as HTMLElement).classList.contains('modal-overlay')) {
      this.cancelled.emit();
    }
  }

  protected onSave(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const { ruleType, column, params } = this.form.value as {
      ruleType: string;
      column: string;
      params: string;
    };

    const editing = this.editingRule();

    const isDuplicate = this.existingRules().some((r) => {
      const sameCombo = r.type === ruleType && r.column === column;
      return editing ? sameCombo && r.id !== editing.id : sameCombo;
    });

    if (isDuplicate) {
      this.duplicateError = true;
      return;
    }

    const rule: SuggestedRule = {
      id: editing?.id ?? `custom-${Date.now()}`,
      name: this.buildName(ruleType, column),
      type: ruleType,
      description: this.buildDescription(ruleType, column, params),
      column,
      enabled: editing?.enabled ?? true,
      ...(params.trim() ? { params: params.trim() } : {}),
    };

    this.saved.emit(rule);
    this.form.reset({ ruleType: '', column: '', params: '' });
    this.duplicateError = false;
  }

  protected onCancel(): void {
    this.cancelled.emit();
  }

  private buildName(type: string, column: string): string {
    switch (type) {
      case 'null_check':
        return `No null ${column}`;
      case 'type_check':
        return `Type: ${column}`;
      case 'range_check':
        return `${column} range`;
      case 'uniqueness':
        return `Unique ${column}`;
      default:
        return `${type} — ${column}`;
    }
  }

  private buildDescription(type: string, column: string, params: string): string {
    switch (type) {
      case 'null_check':
        return `Flag any missing values in ${column}`;
      case 'type_check':
        return params ? `Values must match type: ${params}` : `Every value must match the expected type`;
      case 'range_check':
        return params ? `Values must fall within bounds: ${params}` : `Numeric values must fall within defined bounds`;
      case 'uniqueness':
        return `No duplicate values allowed in ${column}`;
      default:
        return `${type} check on ${column}`;
    }
  }
}
