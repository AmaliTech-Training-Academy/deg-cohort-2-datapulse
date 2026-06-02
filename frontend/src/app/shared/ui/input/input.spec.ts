import { render, screen, fireEvent } from '@testing-library/angular';
import { InputComponent } from './input';
import { FormControl, ReactiveFormsModule, Validators } from '@angular/forms';
import { Component } from '@angular/core';

describe('InputComponent', () => {
  it('renders the label text', async () => {
    await render(`<app-input label="Username" />`, { imports: [InputComponent] });
    expect(screen.getByLabelText(/username/i)).toBeTruthy();
  });

  it('renders a text input by default', async () => {
    await render(`<app-input label="Name" />`, { imports: [InputComponent] });
    expect(screen.getByLabelText(/name/i).getAttribute('type')).toBe('text');
  });

  it('renders an email input when type is email', async () => {
    await render(`<app-input label="Email" type="email" />`, { imports: [InputComponent] });
    expect(screen.getByLabelText(/email/i).getAttribute('type')).toBe('email');
  });

  it('renders a password toggle button for password inputs', async () => {
    await render(`<app-input label="Password" type="password" />`, { imports: [InputComponent] });
    expect(screen.getByRole('button', { name: /show password/i })).toBeTruthy();
  });

  it('toggles password visibility when the toggle button is clicked', async () => {
    await render(`<app-input label="Secret" type="password" />`, { imports: [InputComponent] });
    const input = screen.getByLabelText(/secret/i, { selector: 'input' });
    expect(input.getAttribute('type')).toBe('password');

    fireEvent.click(screen.getByRole('button', { name: /show password/i }));
    expect(input.getAttribute('type')).toBe('text');

    fireEvent.click(screen.getByRole('button', { name: /hide password/i }));
    expect(input.getAttribute('type')).toBe('password');
  });

  it('sets a placeholder', async () => {
    await render(`<app-input label="Name" placeholder="Enter your name" />`, {
      imports: [InputComponent],
    });
    expect(screen.getByLabelText(/name/i).getAttribute('placeholder')).toBe('Enter your name');
  });

  it('updates the form control value when the user types', async () => {
    @Component({
      template: `<app-input label="Field" [formControl]="ctrl" />`,
      standalone: true,
      imports: [InputComponent, ReactiveFormsModule],
    })
    class HostComponent {
      ctrl = new FormControl('');
    }

    const { fixture } = await render(HostComponent);
    const input = screen.getByLabelText(/field/i);
    fireEvent.input(input, { target: { value: 'hello world' } });
    expect(fixture.componentInstance.ctrl.value).toBe('hello world');
  });

  it('shows required error message after the control is touched', async () => {
    @Component({
      template: `<app-input label="Field" [formControl]="ctrl" />`,
      standalone: true,
      imports: [InputComponent, ReactiveFormsModule],
    })
    class HostComponent {
      ctrl = new FormControl('', Validators.required);
    }

    const { fixture } = await render(HostComponent);
    fixture.componentInstance.ctrl.markAsTouched();
    fixture.detectChanges();

    expect(screen.getByRole('alert').textContent).toContain('This field is required');
  });

  it('shows email error message after the control is touched with invalid email', async () => {
    @Component({
      template: `<app-input label="Email" type="email" [formControl]="ctrl" />`,
      standalone: true,
      imports: [InputComponent, ReactiveFormsModule],
    })
    class HostComponent {
      ctrl = new FormControl('not-an-email', [Validators.required, Validators.email]);
    }

    const { fixture } = await render(HostComponent);
    fixture.componentInstance.ctrl.markAsTouched();
    fixture.detectChanges();

    expect(screen.getByRole('alert').textContent).toContain('Enter a valid email address');
  });

  it('shows minlength error message after the control is touched', async () => {
    @Component({
      template: `<app-input label="Pass" type="password" [formControl]="ctrl" />`,
      standalone: true,
      imports: [InputComponent, ReactiveFormsModule],
    })
    class HostComponent {
      ctrl = new FormControl('short', [Validators.required, Validators.minLength(8)]);
    }

    const { fixture } = await render(HostComponent);
    fixture.componentInstance.ctrl.markAsTouched();
    fixture.detectChanges();

    expect(screen.getByRole('alert').textContent).toContain('Minimum 8 characters required');
  });
});
