import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TestDialog from '../app/components/TestDialog';

const base = { show: true, title: '', text: '', responses: [], progress: 0 };

const renderDialog = (dataOverrides = {}) =>
    render(
        <TestDialog
            data={{ ...base, ...dataOverrides }}
            onClose={jest.fn()}
        />
    );

// ── Content rendering ─────────────────────────────────────────────────────────

test('renders the dialog title', () => {
    renderDialog({ title: 'Scan barcode' });
    expect(screen.getByText('Scan barcode')).toBeInTheDocument();
});

test('renders the dialog description text', () => {
    renderDialog({ text: 'Place the board on the fixture and press OK.' });
    expect(
        screen.getByText('Place the board on the fixture and press OK.')
    ).toBeInTheDocument();
});

test('renders all response buttons', () => {
    renderDialog({ responses: ['OK', 'Cancel', 'Retry'] });
    expect(screen.getByRole('button', { name: 'OK' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
});

// ── Button variant rules ──────────────────────────────────────────────────────
// Positive responses (OK / Yes) → MUI "contained"; everything else → "outlined"

test('"OK" button uses contained variant', () => {
    renderDialog({ responses: ['OK'] });
    expect(screen.getByRole('button', { name: 'OK' })).toHaveClass('MuiButton-contained');
});

test('"Yes" button uses contained variant', () => {
    renderDialog({ responses: ['Yes'] });
    expect(screen.getByRole('button', { name: 'Yes' })).toHaveClass('MuiButton-contained');
});

test('"Cancel" button uses outlined variant', () => {
    renderDialog({ responses: ['Cancel'] });
    expect(screen.getByRole('button', { name: 'Cancel' })).toHaveClass('MuiButton-outlined');
});

test('"No" button uses outlined variant', () => {
    renderDialog({ responses: ['No'] });
    expect(screen.getByRole('button', { name: 'No' })).toHaveClass('MuiButton-outlined');
});

// ── Progress bar ──────────────────────────────────────────────────────────────

test('progress label shows rounded percentage', () => {
    renderDialog({ progress: 66.7 });
    expect(screen.getByText('Progress: 67%')).toBeInTheDocument();
});

test('progress bar defaults to 0%', () => {
    renderDialog({});
    expect(screen.getByText('Progress: 0%')).toBeInTheDocument();
});

// ── onClose callback ──────────────────────────────────────────────────────────

test('onClose is called with {rsp} and data when a button is clicked', async () => {
    const user = userEvent.setup();
    const onClose = jest.fn();
    render(
        <TestDialog
            data={{ ...base, responses: ['OK'] }}
            onClose={onClose}
        />
    );
    await user.click(screen.getByRole('button', { name: 'OK' }));
    expect(onClose).toHaveBeenCalledWith({ rsp: 'OK' }, expect.anything());
});
