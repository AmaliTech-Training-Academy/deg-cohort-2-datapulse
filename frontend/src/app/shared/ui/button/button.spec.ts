import { render, screen } from '@testing-library/angular';
import { ButtonComponent } from './button';

describe('ButtonComponent', () => {
  it('renders projected text content', async () => {
    await render(`<app-button>Click me</app-button>`, { imports: [ButtonComponent] });
    expect(screen.getByRole('button', { name: /click me/i })).toBeTruthy();
  });

  it('applies primary and md classes by default', async () => {
    await render(`<app-button>Go</app-button>`, { imports: [ButtonComponent] });
    const btn = screen.getByRole('button', { name: /go/i });
    expect(btn.className).toContain('btn--primary');
    expect(btn.className).toContain('btn--md');
  });

  it('applies danger variant class', async () => {
    await render(`<app-button variant="danger">Delete</app-button>`, {
      imports: [ButtonComponent],
    });
    expect(screen.getByRole('button').className).toContain('btn--danger');
  });

  it('applies secondary variant class', async () => {
    await render(`<app-button variant="secondary">Cancel</app-button>`, {
      imports: [ButtonComponent],
    });
    expect(screen.getByRole('button').className).toContain('btn--secondary');
  });

  it('applies lg size class', async () => {
    await render(`<app-button size="lg">Big</app-button>`, { imports: [ButtonComponent] });
    expect(screen.getByRole('button').className).toContain('btn--lg');
  });

  it('applies sm size class', async () => {
    await render(`<app-button size="sm">Small</app-button>`, { imports: [ButtonComponent] });
    expect(screen.getByRole('button').className).toContain('btn--sm');
  });

  it('applies full-width class when fullWidth is true', async () => {
    await render(`<app-button [fullWidth]="true">Full</app-button>`, {
      imports: [ButtonComponent],
    });
    expect(screen.getByRole('button').className).toContain('btn--full');
  });

  it('applies loading class and disables button when loading', async () => {
    await render(`<app-button [loading]="true">Save</app-button>`, { imports: [ButtonComponent] });
    const btn = screen.getByRole('button');
    expect(btn.className).toContain('btn--loading');
    expect(btn).toBeDisabled();
  });

  it('disables button when disabled is true', async () => {
    await render(`<app-button [disabled]="true">Nope</app-button>`, { imports: [ButtonComponent] });
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('sets the correct native button type', async () => {
    await render(`<app-button type="submit">Submit</app-button>`, { imports: [ButtonComponent] });
    expect(screen.getByRole('button').getAttribute('type')).toBe('submit');
  });

  it('defaults to type button', async () => {
    await render(`<app-button>Default</app-button>`, { imports: [ButtonComponent] });
    expect(screen.getByRole('button').getAttribute('type')).toBe('button');
  });
});
