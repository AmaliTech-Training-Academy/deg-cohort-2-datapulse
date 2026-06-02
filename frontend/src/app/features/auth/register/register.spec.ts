import { render, screen, fireEvent } from '@testing-library/angular';
import { RegisterComponent } from './register';
import { provideMockStore, MockStore } from '@ngrx/store/testing';
import { provideRouter } from '@angular/router';
import { TestBed } from '@angular/core/testing';
import * as AuthActions from '../store/auth.actions';

const defaultAuthState = { user: null, loading: false, error: null, forgotPasswordSent: false };

describe('RegisterComponent', () => {
  async function setup(authState: Partial<typeof defaultAuthState> = {}) {
    await render(RegisterComponent, {
      providers: [
        provideMockStore({ initialState: { auth: { ...defaultAuthState, ...authState } } }),
        provideRouter([]),
      ],
    });
    return { store: TestBed.inject(MockStore) };
  }

  it('renders Create account submit button', async () => {
    await setup();
    expect(screen.getByRole('button', { name: /create account/i })).toBeTruthy();
  });

  it('has first name, last name, email, and password fields', async () => {
    await setup();
    expect(screen.getByLabelText(/first name/i)).toBeTruthy();
    expect(screen.getByLabelText(/last name/i)).toBeTruthy();
    expect(screen.getByLabelText(/email/i)).toBeTruthy();
    expect(screen.getByLabelText(/password/i, { selector: 'input' })).toBeTruthy();
  });

  it('shows error alert when store has error', async () => {
    await setup({ error: 'Email already registered' });
    const alert = screen.getByRole('alert');
    expect(alert).toBeTruthy();
    expect(alert.textContent).toContain('Email already registered');
  });

  it('disables the submit button when loading', async () => {
    await setup({ loading: true });
    expect(screen.getByRole('button', { name: /create account/i })).toBeDisabled();
  });

  it('dispatches register action combining first and last name', async () => {
    const { store } = await setup();
    const dispatchSpy = jest.spyOn(store, 'dispatch');

    fireEvent.input(screen.getByLabelText(/first name/i), { target: { value: 'Jordan' } });
    fireEvent.input(screen.getByLabelText(/last name/i), { target: { value: 'Lee' } });
    fireEvent.input(screen.getByLabelText(/email/i), { target: { value: 'jordan@example.com' } });
    fireEvent.input(screen.getByLabelText(/password/i, { selector: 'input' }), {
      target: { value: 'secure123' },
    });
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    expect(dispatchSpy).toHaveBeenCalledWith(
      AuthActions.register({
        name: 'Jordan Lee',
        email: 'jordan@example.com',
        password: 'secure123',
      }),
    );
  });

  it('does not dispatch when form is empty', async () => {
    const { store } = await setup();
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));
    expect(dispatchSpy).not.toHaveBeenCalled();
  });

  it('does not dispatch when password is too short', async () => {
    const { store } = await setup();
    const dispatchSpy = jest.spyOn(store, 'dispatch');

    fireEvent.input(screen.getByLabelText(/first name/i), { target: { value: 'Jordan' } });
    fireEvent.input(screen.getByLabelText(/last name/i), { target: { value: 'Lee' } });
    fireEvent.input(screen.getByLabelText(/email/i), { target: { value: 'jordan@example.com' } });
    fireEvent.input(screen.getByLabelText(/password/i, { selector: 'input' }), {
      target: { value: 'short' },
    });
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    expect(dispatchSpy).not.toHaveBeenCalled();
  });

  it('has a sign in link', async () => {
    await setup();
    expect(screen.getByRole('link', { name: /sign in/i })).toBeTruthy();
  });
});
