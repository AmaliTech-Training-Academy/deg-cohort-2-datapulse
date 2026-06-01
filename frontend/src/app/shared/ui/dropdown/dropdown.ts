import { Component, Optional, Self, input } from '@angular/core';
import { ControlValueAccessor, NgControl } from '@angular/forms';

export interface DropdownOption {
  value: string;
  label: string;
}

@Component({
  selector: 'app-dropdown',
  standalone: true,
  templateUrl: './dropdown.html',
  styleUrl: './dropdown.css',
})
export class DropdownComponent implements ControlValueAccessor {
  readonly label = input<string>('');
  readonly placeholder = input<string>('Select an option');
  readonly options = input<DropdownOption[]>([]);

  protected value = '';
  protected isDisabled = false;
  protected readonly selectId = `select-${Math.random().toString(36).slice(2, 7)}`;

  private onChange: (val: string) => void = () => {};
  private onTouched: () => void = () => {};

  constructor(@Optional() @Self() protected readonly ngControl: NgControl) {
    if (this.ngControl != null) {
      this.ngControl.valueAccessor = this;
    }
  }

  get showError(): boolean {
    return !!(this.ngControl?.control?.touched && this.ngControl?.control?.invalid);
  }

  get errorMessage(): string {
    const errors = this.ngControl?.control?.errors;
    if (!errors) return '';
    if (errors['required']) return 'Please select an option.';
    return 'Invalid selection.';
  }

  writeValue(val: string): void {
    this.value = val ?? '';
  }

  registerOnChange(fn: (val: string) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.isDisabled = isDisabled;
  }

  protected handleChange(event: Event): void {
    const val = (event.target as HTMLSelectElement).value;
    this.value = val;
    this.onChange(val);
    this.onTouched();
  }
}
