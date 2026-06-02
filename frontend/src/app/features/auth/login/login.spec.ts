import { render, screen, fireEvent } from '@testing-library/angular';
import { LoginComponent } from './login';
import { provideMockStore, MockStore } from '@ngrx/store/testing';
import { provideRouter } from '@angular/router';
import { TestBed } from '@angular/core/testing';
import * as AuthActions from '../store/auth.actions';

const defaultAuthState = { user: null, loading: false, error: null, forgotPasswordSent: false };

describe('LoginComponent', () => {
  async function setup(authState: Partial<typeof defaultAuthState> = {}) {
    await render(LoginComponent, {
      providers: [
        provideMockStore({ initialState: { auth: { ...defaultAuthState, ...authState } } }),
        provideRouter([]),
      ],
    });
    return { store: TestBed.inject(MockStore) };
  }

  it('renders Sign in submit button', async () => {
    await setup();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeTruthy();
  });

  it('has email and password fields', async () => {
    await setup();
    expect(screen.getByLabelText(/email/i)).toBeTruthy();
    expect(screen.getByLabelText(/password/i, { selector: 'input' })).toBeTruthy();
  });

  it('shows error alert when store has error', async () => {
    await setup({ error: 'Invalid credentials' });
    const alert = screen.getByRole('alert');
    expect(alert).toBeTruthy();
    expect(alert.textContent).toContain('Invalid credentials');
  });

  it('disables the submit button when loading', async () => {
    await setup({ loading: true });
    expect(screen.getByRole('button', { name: /sign in/i })).toBeDisabled();
  });

  it('dispatches login action with credentials on valid submit', async () => {
    const { store } = await setup();
    const dispatchSpy = jest.spyOn(store, 'dispatch');

    fireEvent.input(screen.getByLabelText(/email/i), { target: { value: 'user@example.com' } });
    fireEvent.input(screen.getByLabelText(/password/i, { selector: 'input' }), {
      target: { value: 'secret123' },
    });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    expect(dispatchSpy).toHaveBeenCalledWith(
      AuthActions.login({ email: 'user@example.com', password: 'secret123' }),
    );
  });

  it('does not dispatch when form is empty', async () => {
    const { store } = await setup();
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
    expect(dispatchSpy).not.toHaveBeenCalled();
  });

  it('does not dispatch when email is invalid', async () => {
    const { store } = await setup();
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    fireEvent.input(screen.getByLabelText(/email/i), { target: { value: 'not-an-email' } });
    fireEvent.input(screen.getByLabelText(/password/i, { selector: 'input' }), {
      target: { value: 'secret123' },
    });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
    expect(dispatchSpy).not.toHaveBeenCalled();
  });

  it('has a forgot password link', async () => {
    await setup();
    expect(screen.getByRole('link', { name: /forgot password/i })).toBeTruthy();
  });

  it('has a create an account link', async () => {
    await setup();
    expect(screen.getByRole('link', { name: /create an account/i })).toBeTruthy();
  });
});
