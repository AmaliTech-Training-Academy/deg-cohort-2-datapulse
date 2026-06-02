import { render, screen, fireEvent } from '@testing-library/angular';
import { CheckboxComponent } from './checkbox';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { Component } from '@angular/core';

describe('CheckboxComponent', () => {
  it('renders with label text', async () => {
    await render(`<app-checkbox label="Accept terms" />`, { imports: [CheckboxComponent] });
    expect(screen.getByLabelText(/accept terms/i)).toBeTruthy();
  });

  it('is unchecked by default', async () => {
    await render(`<app-checkbox label="Subscribe" />`, { imports: [CheckboxComponent] });
    expect(screen.getByRole('checkbox')).not.toBeChecked();
  });

  it('reflects checked state when writeValue is called via reactive form', async () => {
    @Component({
      template: `<app-checkbox label="Agree" [formControl]="ctrl" />`,
      standalone: true,
      imports: [CheckboxComponent, ReactiveFormsModule],
    })
    class HostComponent {
      ctrl = new FormControl(true);
    }

    await render(HostComponent);
    expect(screen.getByRole('checkbox')).toBeChecked();
  });

  it('updates form control value when clicked', async () => {
    @Component({
      template: `<app-checkbox label="Newsletter" [formControl]="ctrl" />`,
      standalone: true,
      imports: [CheckboxComponent, ReactiveFormsModule],
    })
    class HostComponent {
      ctrl = new FormControl(false);
    }

    const { fixture } = await render(HostComponent);
    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).not.toBeChecked();

    fireEvent.click(checkbox);
    expect(fixture.componentInstance.ctrl.value).toBe(true);

    fireEvent.click(checkbox);
    expect(fixture.componentInstance.ctrl.value).toBe(false);
  });

  it('is disabled when setDisabledState is called via form control', async () => {
    @Component({
      template: `<app-checkbox label="Disabled" [formControl]="ctrl" />`,
      standalone: true,
      imports: [CheckboxComponent, ReactiveFormsModule],
    })
    class HostComponent {
      ctrl = new FormControl({ value: false, disabled: true });
    }

    await render(HostComponent);
    expect(screen.getByRole('checkbox')).toBeDisabled();
  });
});
