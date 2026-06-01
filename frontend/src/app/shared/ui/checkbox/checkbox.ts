import { Component, Optional, Self, input } from '@angular/core';
import { ControlValueAccessor, NgControl } from '@angular/forms';

@Component({
  selector: 'app-checkbox',
  standalone: true,
  templateUrl: './checkbox.html',
  styleUrl: './checkbox.css',
})
export class CheckboxComponent implements ControlValueAccessor {
  readonly label = input<string>('');

  protected checked = false;
  protected isDisabled = false;
  protected readonly inputId = `checkbox-${Math.random().toString(36).slice(2, 7)}`;

  private onChange: (val: boolean) => void = () => {};
  private onTouched: () => void = () => {};

  constructor(@Optional() @Self() protected readonly ngControl: NgControl) {
    if (this.ngControl != null) {
      this.ngControl.valueAccessor = this;
    }
  }

  writeValue(val: boolean): void {
    this.checked = !!val;
  }

  registerOnChange(fn: (val: boolean) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.isDisabled = isDisabled;
  }

  protected handleChange(event: Event): void {
    const checked = (event.target as HTMLInputElement).checked;
    this.checked = checked;
    this.onChange(checked);
    this.onTouched();
  }
}
