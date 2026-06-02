import { Component, Optional, Self, input, signal } from '@angular/core';
import { ControlValueAccessor, NgControl } from '@angular/forms';

@Component({
  selector: 'app-input',
  standalone: true,
  templateUrl: './input.html',
  styleUrl: './input.css',
})
export class InputComponent implements ControlValueAccessor {
  readonly label = input<string>('');
  readonly type = input<'text' | 'email' | 'password' | 'number' | 'tel'>('text');
  readonly placeholder = input<string>('');
  readonly autocomplete = input<string>('off');

  protected readonly showPassword = signal(false);
  protected value = '';
  protected isDisabled = false;
  protected readonly inputId = `field-${Math.random().toString(36).slice(2, 7)}`;

  private onChange: (val: string) => void = () => {};
  private onTouched: () => void = () => {};

  constructor(@Optional() @Self() protected readonly ngControl: NgControl) {
    if (this.ngControl != null) {
      this.ngControl.valueAccessor = this;
    }
  }

  protected get currentType(): string {
    return this.type() === 'password' && this.showPassword() ? 'text' : this.type();
  }

  get showError(): boolean {
    return !!(this.ngControl?.control?.touched && this.ngControl?.control?.invalid);
  }

  get errorMessage(): string {
    const errors = this.ngControl?.control?.errors;
    if (!errors) return '';
    if (errors['required']) return 'This field is required.';
    if (errors['email']) return 'Enter a valid email address.';
    if (errors['minlength'])
      return `Minimum ${errors['minlength'].requiredLength} characters required.`;
    return 'Invalid value.';
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

  protected handleInput(event: Event): void {
    const val = (event.target as HTMLInputElement).value;
    this.value = val;
    this.onChange(val);
  }

  protected handleBlur(): void {
    this.onTouched();
  }

  protected togglePassword(): void {
    this.showPassword.update((v) => !v);
  }
}
