import { render, screen } from '@testing-library/angular';
import { DashboardComponent } from './dashboard';

describe('DashboardComponent', () => {
  it('renders dashboard heading', async () => {
    await render(DashboardComponent);
    expect(screen.getByRole('heading', { name: /dashboard/i })).toBeTruthy();
  });
});
