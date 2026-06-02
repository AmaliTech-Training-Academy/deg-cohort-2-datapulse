import { Component, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { SuggestedRule, DetectedColumn } from '../../../../../../shared/models/dashboard.models';

export interface UploadData {
  name: string;
  description: string;
  fileName: string;
  columns: DetectedColumn[];
  rules: SuggestedRule[];
}

const MOCK_COLUMNS: DetectedColumn[] = [
  { name: 'customer_id', type: 'Integer' },
  { name: 'email', type: 'String' },
  { name: 'signup_date', type: 'Date' },
  { name: 'age', type: 'Integer' },
  { name: 'region', type: 'String' },
  { name: 'status', type: 'Enum' },
  { name: 'created_at', type: 'Datetime' },
];

const MOCK_RULES: SuggestedRule[] = [
  { id: 'r1', name: 'Unique customer_id', type: 'uniqueness', description: 'Detected as a primary key — no duplicate values allowed', column: 'customer_id', enabled: true },
  { id: 'r2', name: 'No null emails', type: 'null_check', description: 'Required field — flag any missing values', column: 'email', enabled: true },
  { id: 'r3', name: 'Email format', type: 'type_check', description: 'Values must match a valid email pattern', column: 'email', enabled: true },
  { id: 'r4', name: 'Type: signup_date', type: 'type_check', description: 'Every value must parse as an ISO 8601 date', column: 'signup_date', enabled: true },
  { id: 'r5', name: 'Age range 18–120', type: 'range_check', description: 'Numeric values must fall within bounds', column: 'age', enabled: true },
  { id: 'r6', name: 'Status in allowed set', type: 'type_check', description: 'Only active, trial, or churned accepted', column: 'status', enabled: false },
];

@Component({
  selector: 'app-step-upload',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './step-upload.html',
  styleUrl: './step-upload.css',
})
export class StepUploadComponent {
  readonly continue = output<UploadData>();

  protected projectName = '';
  protected description = '';
  protected fileName = signal<string | null>(null);
  protected isDragOver = signal(false);

  protected onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.isDragOver.set(true);
  }

  protected onDragLeave(): void {
    this.isDragOver.set(false);
  }

  protected onDrop(event: DragEvent): void {
    event.preventDefault();
    this.isDragOver.set(false);
    const file = event.dataTransfer?.files[0];
    if (file) this.fileName.set(file.name);
  }

  protected onFileSelect(event: Event): void {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (file) this.fileName.set(file.name);
  }

  protected onContinue(): void {
    this.continue.emit({
      name: this.projectName || 'New Project',
      description: this.description,
      fileName: this.fileName() ?? 'dataset.csv',
      columns: MOCK_COLUMNS,
      rules: [...MOCK_RULES],
    });
  }

  protected get canContinue(): boolean {
    return this.projectName.trim().length > 0;
  }
}
