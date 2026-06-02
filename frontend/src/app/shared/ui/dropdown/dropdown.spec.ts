import { render, screen, fireEvent } from '@testing-library/angular';
import { DropdownComponent } from './dropdown';
import { FormControl, ReactiveFormsModule, Validators } from '@angular/forms';
import { Component } from '@angular/core';

const options = [
  { value: 'option1', label: 'Option 1' },
  { value: 'option2', label: 'Option 2' },
  { value: 'option3', label: 'Option 3' },
];

describe('DropdownComponent', () => {
  it('renders the label', async () => {
    await render(`<app-dropdown label="Category" [options]="opts" />`, {
      imports: [DropdownComponent],
      componentProperties: { opts: options },
    });
    expect(screen.getByLabelText(/category/i)).toBeTruthy();
  });

  it('renders the placeholder option', async () => {
    await render(`<app-dropdown label="Pick one" placeholder="Choose..." [options]="opts" />`, {
      imports: [DropdownComponent],
      componentProperties: { opts: options },
    });
    expect(screen.getByRole('option', { name: /choose.../i })).toBeTruthy();
  });

  it('renders all provided options', async () => {
    await render(`<app-dropdown label="Pick" [options]="opts" />`, {
      imports: [DropdownComponent],
      componentProperties: { opts: options },
    });
    expect(screen.getByRole('option', { name: /option 1/i })).toBeTruthy();
    expect(screen.getByRole('option', { name: /option 2/i })).toBeTruthy();
    expect(screen.getByRole('option', { name: /option 3/i })).toBeTruthy();
  });

  it('updates form control value when an option is selected', async () => {
    @Component({
      template: `<app-dropdown label="Category" [options]="opts" [formControl]="ctrl" />`,
      standalone: true,
      imports: [DropdownComponent, ReactiveFormsModule],
    })
    class HostComponent {
      ctrl = new FormControl('');
      opts = options;
    }

    const { fixture } = await render(HostComponent);
    const select = screen.getByLabelText(/category/i);
    fireEvent.change(select, { target: { value: 'option2' } });
    expect(fixture.componentInstance.ctrl.value).toBe('option2');
  });

  it('shows required error message after control is touched', async () => {
    @Component({
      template: `<app-dropdown label="Category" [options]="opts" [formControl]="ctrl" />`,
      standalone: true,
      imports: [DropdownComponent, ReactiveFormsModule],
    })
    class HostComponent {
      ctrl = new FormControl('', Validators.required);
      opts = options;
    }

    const { fixture } = await render(HostComponent);
    fixture.componentInstance.ctrl.markAsTouched();
    fixture.detectChanges();

    expect(screen.getByRole('alert').textContent).toContain('Please select an option');
  });

  it('is disabled when the form control is disabled', async () => {
    @Component({
      template: `<app-dropdown label="Locked" [options]="opts" [formControl]="ctrl" />`,
      standalone: true,
      imports: [DropdownComponent, ReactiveFormsModule],
    })
    class HostComponent {
      ctrl = new FormControl({ value: '', disabled: true });
      opts = options;
    }

    await render(HostComponent);
    expect(screen.getByLabelText(/locked/i)).toBeDisabled();
  });
});
