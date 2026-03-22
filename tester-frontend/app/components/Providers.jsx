'use client';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

const darkTheme = createTheme({
    palette: {
        mode: 'dark',
        background: {
            default: '#0d1117',
            paper:   '#161b2e',
        },
        primary:   { main: '#6366f1' },
        secondary: { main: '#8b9eb0' },
        success:   { main: '#10b981' },
        warning:   { main: '#f59e0b' },
        error:     { main: '#ef4444' },
        text: {
            primary:   '#e2e8f0',
            secondary: '#8b9eb0',
        },
        divider: '#2d3748',
    },
    shape: { borderRadius: 8 },
    typography: {
        fontFamily: "'Inter', system-ui, sans-serif",
    },
    components: {
        MuiPaper: {
            styleOverrides: {
                root: { backgroundImage: 'none' },
            },
        },
        MuiPopover: {
            styleOverrides: {
                paper: { backgroundColor: '#1e2640', border: '1px solid #2d3748' },
            },
        },
        MuiMenu: {
            styleOverrides: {
                paper: { backgroundColor: '#1e2640', border: '1px solid #2d3748' },
            },
        },
    },
});

export default function Providers({ children }) {
    return (
        <ThemeProvider theme={darkTheme}>
            <CssBaseline />
            {children}
        </ThemeProvider>
    );
}
