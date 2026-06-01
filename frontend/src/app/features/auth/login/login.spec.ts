import { render, screen } from '@testing-library/angular';
import { LoginComponent } from './login';
import { provideStore } from '@ngrx/store';
import { authReducer } from '../store/auth.reducer';
import { provideRouter } from '@angular/router';

describe('LoginComponent', () => {
  async function setup() {
    return render(LoginComponent, {
      providers: [provideStore({ auth: authReducer }), provideRouter([])],
    });
  }

  it('renders sign in heading', async () => {
    await setup();
    expect(screen.getByRole('heading', { name: /sign in/i })).toBeTruthy();
  });

  it('has email and password fields', async () => {
    await setup();
    expect(screen.getByLabelText(/email/i)).toBeTruthy();
    expect(screen.getByLabelText(/password/i)).toBeTruthy();
  });
});
