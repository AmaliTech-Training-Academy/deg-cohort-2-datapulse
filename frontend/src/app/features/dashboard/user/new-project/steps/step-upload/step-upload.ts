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
  protected parsedColumns = signal<DetectedColumn[]>([]);
  protected parsedRules = signal<SuggestedRule[]>([]);
  protected parseError = signal<string | null>(null);

  private pendingFile: File | null = null;

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
    if (file) this.processFile(file);
  }

  protected onFileSelect(event: Event): void {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (file) this.processFile(file);
  }

  protected onContinue(): void {
    this.continue.emit({
      name: this.projectName,
      description: this.description,
      fileName: this.fileName() ?? '',
      columns: this.parsedColumns(),
      rules: this.parsedRules(),
    });
  }

  protected get canContinue(): boolean {
    return this.projectName.trim().length > 0 && this.parsedColumns().length > 0;
  }

  private processFile(file: File): void {
    this.pendingFile = file;
    this.fileName.set(file.name);
    this.parsedColumns.set([]);
    this.parsedRules.set([]);
    this.parseError.set(null);

    const lower = file.name.toLowerCase();
    if (!lower.endsWith('.csv') && !lower.endsWith('.json')) {
      this.parseError.set('Only .csv and .json files are supported.');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      try {
        if (lower.endsWith('.csv')) {
          this.parseCSV(text);
        } else {
          this.parseJSON(text);
        }
      } catch {
        this.parseError.set('Could not parse this file. Check that it is valid CSV or JSON.');
      }
    };
    reader.onerror = () => this.parseError.set('Failed to read the file.');
    reader.readAsText(file);
  }

  private parseCSV(text: string): void {
    const lines = text.split(/\r?\n/).filter((l) => l.trim().length > 0);
    if (lines.length < 1) {
      this.parseError.set('CSV is empty.');
      return;
    }

    const headers = this.splitCSVLine(lines[0]);
    if (headers.length === 0) {
      this.parseError.set('No columns found in CSV header.');
      return;
    }

    const sampleValues = lines.length > 1 ? this.splitCSVLine(lines[1]) : [];

    const columns: DetectedColumn[] = headers.map((name, i) => ({
      name: name || `column_${i + 1}`,
      type: this.inferType(sampleValues[i] ?? ''),
    }));

    this.parsedColumns.set(columns);
    this.parsedRules.set(this.suggestRules(columns));
  }

  private parseJSON(text: string): void {
    const parsed: unknown = JSON.parse(text);
    const obj: Record<string, unknown> = Array.isArray(parsed)
      ? (parsed[0] as Record<string, unknown>)
      : (parsed as Record<string, unknown>);

    if (typeof obj !== 'object' || obj === null) {
      this.parseError.set('JSON must be an object or array of objects.');
      return;
    }

    const columns: DetectedColumn[] = Object.entries(obj)
      .filter(([, v]) => typeof v !== 'object' || v === null)
      .map(([key, value]) => ({
        name: key,
        type: this.inferTypeFromValue(value),
      }));

    if (columns.length === 0) {
      this.parseError.set('No scalar top-level keys found in this JSON.');
      return;
    }

    this.parsedColumns.set(columns);
    this.parsedRules.set(this.suggestRules(columns));
  }

  private splitCSVLine(line: string): string[] {
    const result: string[] = [];
    let inQuote = false;
    let current = '';
    for (const char of line) {
      if (char === '"') {
        inQuote = !inQuote;
      } else if (char === ',' && !inQuote) {
        result.push(current.trim());
        current = '';
      } else {
        current += char;
      }
    }
    result.push(current.trim());
    return result;
  }

  private inferType(value: string): DetectedColumn['type'] {
    if (/^(true|false)$/i.test(value)) return 'Boolean';
    if (/^\d{4}-\d{2}-\d{2}T/.test(value)) return 'Datetime';
    if (/^\d{4}-\d{2}-\d{2}$/.test(value)) return 'Date';
    if (/^-?\d+$/.test(value)) return 'Integer';
    if (/^-?\d+\.\d+$/.test(value)) return 'Float';
    return 'String';
  }

  private inferTypeFromValue(value: unknown): DetectedColumn['type'] {
    if (value === null || value === undefined) return 'String';
    if (typeof value === 'boolean') return 'Boolean';
    if (typeof value === 'number') return Number.isInteger(value) ? 'Integer' : 'Float';
    if (typeof value === 'string') {
      if (/^\d{4}-\d{2}-\d{2}T/.test(value)) return 'Datetime';
      if (/^\d{4}-\d{2}-\d{2}$/.test(value)) return 'Date';
    }
    return 'String';
  }

  private suggestRules(columns: DetectedColumn[]): SuggestedRule[] {
    const rules: SuggestedRule[] = [];
    let counter = 0;

    if (columns.length > 0) {
      counter++;
      rules.push({
        id: `auto-${counter}`,
        name: `Unique ${columns[0].name}`,
        type: 'uniqueness',
        description: 'Detected as a potential primary key — no duplicate values allowed',
        column: columns[0].name,
        enabled: true,
      });
    }

    columns.forEach((col) => {
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
