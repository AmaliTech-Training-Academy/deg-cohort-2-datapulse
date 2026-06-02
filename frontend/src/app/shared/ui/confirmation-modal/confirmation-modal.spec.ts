import { render, screen, fireEvent } from '@testing-library/angular';
import { ConfirmationModalComponent } from './confirmation-modal';

describe('ConfirmationModalComponent', () => {
  async function setup(inputs: Partial<{
    isOpen: boolean;
    title: string;
    message: string;
    confirmLabel: string;
    cancelLabel: string;
    variant: 'danger' | 'warning' | 'info';
    loading: boolean;
  }> = {}) {
    const { fixture } = await render(ConfirmationModalComponent, {
      componentInputs: {
        isOpen: true,
        title: 'Are you sure?',
        message: 'This action cannot be undone.',
        confirmLabel: 'Confirm',
        cancelLabel: 'Cancel',
        variant: 'danger',
        loading: false,
        ...inputs,
      },
    });
    return { component: fixture.componentInstance };
  }

  it('does not render when isOpen is false', async () => {
    await setup({ isOpen: false });
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('renders title and message when isOpen is true', async () => {
    await setup({ title: 'Delete item?', message: 'This cannot be undone.' });
    expect(screen.getByText('Delete item?')).toBeTruthy();
    expect(screen.getByText('This cannot be undone.')).toBeTruthy();
  });

  it('renders confirm and cancel buttons', async () => {
    await setup({ confirmLabel: 'Yes, delete', cancelLabel: 'Keep it' });
    expect(screen.getByRole('button', { name: /yes, delete/i })).toBeTruthy();
    expect(screen.getByRole('button', { name: /keep it/i })).toBeTruthy();
  });

  it('emits confirmed when confirm button is clicked', async () => {
    const { component } = await setup();
    const confirmedSpy = jest.spyOn(component.confirmed, 'emit');
    fireEvent.click(screen.getByRole('button', { name: /confirm/i }));
    expect(confirmedSpy).toHaveBeenCalled();
  });

  it('emits cancelled when cancel button is clicked', async () => {
    const { component } = await setup();
    const cancelledSpy = jest.spyOn(component.cancelled, 'emit');
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }));
    expect(cancelledSpy).toHaveBeenCalled();
  });

  it('emits cancelled when overlay backdrop is clicked', async () => {
    const { component } = await setup();
    const cancelledSpy = jest.spyOn(component.cancelled, 'emit');
    const overlay = document.querySelector('.modal-overlay') as HTMLElement;
    fireEvent.click(overlay);
    expect(cancelledSpy).toHaveBeenCalled();
  });

  it('disables confirm button when loading', async () => {
    await setup({ loading: true });
    expect(screen.getByRole('button', { name: /confirm/i })).toBeDisabled();
  });

  it('renders the dialog with accessible role', async () => {
    await setup();
    expect(screen.getByRole('dialog')).toBeTruthy();
  });
});
