import { render } from '@testing-library/angular';
import { provideMockStore } from '@ngrx/store/testing';
import { provideRouter } from '@angular/router';
import { DashboardComponent } from './dashboard';

describe('DashboardComponent', () => {
  it('renders the dashboard layout', async () => {
    const { container } = await render(DashboardComponent, {
      providers: [
        provideMockStore({ initialState: { auth: { user: null, loading: false, error: null, forgotPasswordSent: false } } }),
        provideRouter([]),
      ],
    });
    expect(container.querySelector('.layout')).toBeTruthy();
  });
});
