import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LogModal from '../app/components/LogModal';

test('renders log content when open', () => {
    render(<LogModal open={true} handleClose={jest.fn()} log="[INFO] Test started" />);
    expect(screen.getByText(/\[INFO\] Test started/)).toBeInTheDocument();
});

test('renders multi-line log text', () => {
    const log = '[INFO] Line one\n[WARN] Line two';
    render(<LogModal open={true} handleClose={jest.fn()} log={log} />);
    expect(screen.getByText(/Line one/)).toBeInTheDocument();
    expect(screen.getByText(/Line two/)).toBeInTheDocument();
});

test('close button is present', () => {
    render(<LogModal open={true} handleClose={jest.fn()} log="" />);
    expect(screen.getByRole('button')).toBeInTheDocument();
});

test('handleClose is called when the close button is clicked', async () => {
    const user = userEvent.setup();
    const handleClose = jest.fn();
    render(<LogModal open={true} handleClose={handleClose} log="" />);
    await user.click(screen.getByRole('button'));
    expect(handleClose).toHaveBeenCalledTimes(1);
});

test('"Framework Log" header is shown', () => {
    render(<LogModal open={true} handleClose={jest.fn()} log="" />);
    expect(screen.getByText('Framework Log')).toBeInTheDocument();
});
