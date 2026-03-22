/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        './pages/**/*.{js,ts,jsx,tsx,mdx}',
        './components/**/*.{js,ts,jsx,tsx,mdx}',
        './app/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    theme: {
        extend: {
            colors: {
                primary: {
                    50:  '#eef2ff',
                    100: '#e0e7ff',
                    200: '#c7d2fe',
                    300: '#a5b4fc',
                    400: '#818cf8',
                    500: '#6366f1',
                    600: '#4f46e5',
                    700: '#4338ca',
                    800: '#3730a3',
                    900: '#312e81',
                    950: '#1e1b4b',
                },
                surface: {
                    base:     '#0d1117',
                    card:     '#161b2e',
                    elevated: '#1e2640',
                    border:   '#2d3748',
                },
                success: {
                    50:  '#f0fdf4',
                    100: '#dcfce7',
                    400: '#4ade80',
                    500: '#10b981',
                    600: '#059669',
                    700: '#047857',
                    900: '#064e3b',
                },
                warning: {
                    50:  '#fffbeb',
                    100: '#fef3c7',
                    400: '#fbbf24',
                    500: '#f59e0b',
                    600: '#d97706',
                    900: '#78350f',
                },
                danger: {
                    50:  '#fef2f2',
                    100: '#fee2e2',
                    400: '#f87171',
                    500: '#ef4444',
                    600: '#dc2626',
                    900: '#7f1d1d',
                },
                violet: {
                    400: '#a78bfa',
                    500: '#8b5cf6',
                    600: '#7c3aed',
                },
                gray: {
                    50:  '#f8fafc',
                    100: '#f1f5f9',
                    200: '#e2e8f0',
                    300: '#cbd5e1',
                    400: '#94a3b8',
                    500: '#64748b',
                    600: '#475569',
                    700: '#334155',
                    800: '#1e293b',
                    900: '#0f172a',
                },
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
                mono: ['JetBrains Mono', 'Fira Code', 'Monaco', 'monospace'],
            },
            boxShadow: {
                'glow':        '0 0 20px rgba(99, 102, 241, 0.25)',
                'glow-sm':     '0 0 10px rgba(99, 102, 241, 0.15)',
                'card':        '0 4px 24px rgba(0, 0, 0, 0.4)',
                'pass':        '0 0 8px rgba(16, 185, 129, 0.3)',
                'fail':        '0 0 8px rgba(239, 68, 68, 0.3)',
            },
            animation: {
                'slide-in': 'slideIn 0.25s ease-out',
                'fade-in':  'fadeIn 0.3s ease-out',
                'pulse-slow': 'pulse 2s ease-in-out infinite',
            },
            keyframes: {
                slideIn: {
                    from: { opacity: '0', transform: 'translateX(-8px)' },
                    to:   { opacity: '1', transform: 'translateX(0)' },
                },
                fadeIn: {
                    from: { opacity: '0' },
                    to:   { opacity: '1' },
                },
            },
        },
    },
    plugins: [],
};
