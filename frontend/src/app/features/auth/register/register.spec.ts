import { render, screen } from '@testing-library/angular';
import { RegisterComponent } from './register';
import { provideStore } from '@ngrx/store';
import { authReducer } from '../store/auth.reducer';
import { provideRouter } from '@angular/router';

describe('RegisterComponent', () => {
  async function setup() {
    return render(RegisterComponent, {
      providers: [provideStore({ auth: authReducer }), provideRouter([])],
    });
  }

  it('renders create account heading', async () => {
    await setup();
    expect(screen.getByRole('heading', { name: /create account/i })).toBeTruthy();
  });

  it('has name, email, and password fields', async () => {
    await setup();
    expect(screen.getByLabelText(/name/i)).toBeTruthy();
    expect(screen.getByLabelText(/email/i)).toBeTruthy();
    expect(screen.getByLabelText(/password/i)).toBeTruthy();
  });
});
