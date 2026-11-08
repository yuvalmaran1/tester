'use client';
import CssBaseline from '@mui/material/CssBaseline';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import { createContext, useContext, useEffect, useRef, useState } from 'react';
import { socket } from '../socket';

const sharedPalette = {
    primary: { main: '#4f46e5' },
    success: { main: '#059669' },
    warning: { main: '#d97706' },
    error: { main: '#dc2626' },
};

const createAppTheme = (mode) => createTheme({
    palette: {
        mode,
        ...sharedPalette,
        secondary: { main: mode === 'dark' ? '#a5b4fc' : '#475569' },
        background: mode === 'dark'
            ? { default: '#0d1117', paper: '#161b2e' }
            : { default: '#f8fafc', paper: '#ffffff' },
        text: {
            primary: mode === 'dark' ? '#f1f5f9' : '#172033',
            secondary: mode === 'dark' ? '#cbd5e1' : '#526077',
        },
        divider: mode === 'dark' ? '#3d4a5f' : '#d8e0ea',
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
                paper: {
                    backgroundColor: mode === 'dark' ? '#1e2640' : '#ffffff',
                    border: `1px solid ${mode === 'dark' ? '#3d4a5f' : '#d8e0ea'}`,
                },
            },
        },
        MuiMenu: {
            styleOverrides: {
                paper: {
                    backgroundColor: mode === 'dark' ? '#1e2640' : '#ffffff',
                    border: `1px solid ${mode === 'dark' ? '#3d4a5f' : '#d8e0ea'}`,
                },
            },
        },
    },
});

const themes = {
    light: createAppTheme('light'),
    dark: createAppTheme('dark'),
};

const ColorModeContext = createContext();

export const useColorMode = () => {
    const context = useContext(ColorModeContext);
    if (!context) throw new Error('useColorMode must be used within Providers');
    return context;
};

export default function Providers({ children }) {
    const [mode, setMode] = useState('light');
    const userSelected = useRef(false);
    const stationThemeApplied = useRef(false);

    useEffect(() => {
        const applyStationTheme = (payload) => {
            const stationMode = payload?.tester?.ui_theme ?? payload?.ui_theme;
            if (!stationThemeApplied.current && !userSelected.current && themes[stationMode]) {
                stationThemeApplied.current = true;
                setMode(stationMode);
            }
        };

        socket.on('state', applyStationTheme);
        socket.on('tester', applyStationTheme);
        socket.emit('get_state');
        return () => {
            socket.off('state', applyStationTheme);
            socket.off('tester', applyStationTheme);
        };
    }, []);

    useEffect(() => {
        document.documentElement.dataset.theme = mode;
        document.documentElement.style.colorScheme = mode;
    }, [mode]);

    const toggleColorMode = () => {
        userSelected.current = true;
        setMode((currentMode) => currentMode === 'light' ? 'dark' : 'light');
    };

    return (
        <ColorModeContext.Provider value={{ mode, toggleColorMode }}>
            <ThemeProvider theme={themes[mode]}>
                <CssBaseline />
                {children}
            </ThemeProvider>
        </ColorModeContext.Provider>
    );
}
