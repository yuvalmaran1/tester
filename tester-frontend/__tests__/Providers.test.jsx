import '@testing-library/jest-dom';
import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useTheme } from '@mui/material/styles';
import Providers, { useColorMode } from '../app/components/Providers';

const mockHandlers = {};

jest.mock('../app/socket', () => ({
    socket: {
        emit: jest.fn(),
        on: jest.fn((event, handler) => { mockHandlers[event] = handler; }),
        off: jest.fn(),
    },
}));

const ThemeProbe = () => {
    const theme = useTheme();
    const { mode, toggleColorMode } = useColorMode();
    return (
        <button onClick={toggleColorMode}>
            {mode}:{theme.palette.mode}
        </button>
    );
};

beforeEach(() => {
    Object.keys(mockHandlers).forEach((event) => delete mockHandlers[event]);
    document.documentElement.removeAttribute('data-theme');
});

test('defaults to light and applies the station theme', () => {
    render(<Providers><ThemeProbe /></Providers>);
    expect(screen.getByRole('button')).toHaveTextContent('light:light');

    act(() => mockHandlers.state({ tester: { ui_theme: 'dark' } }));

    expect(screen.getByRole('button')).toHaveTextContent('dark:dark');
    expect(document.documentElement).toHaveAttribute('data-theme', 'dark');
});

test('button selection is not overwritten by later station updates', async () => {
    const user = userEvent.setup();
    render(<Providers><ThemeProbe /></Providers>);

    await user.click(screen.getByRole('button'));
    act(() => mockHandlers.tester({ ui_theme: 'light' }));

    expect(screen.getByRole('button')).toHaveTextContent('dark:dark');
});