// @testing-library/jest-dom is imported at the top of each test file because
// it extends Jest's `expect`, which is not available during setupFiles.

// MUI's button ripple animation fires async state updates after a click, which
// triggers React's act() warning.  These are a known jsdom/MUI interaction and
// do not indicate real bugs — suppress them to keep CI output clean.
const _consoleError = console.error;
console.error = (...args) => {
    if (typeof args[0] === 'string' && args[0].includes('act(')) return;
    _consoleError(...args);
};

// MUI needs matchMedia (not in jsdom)
Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation((query) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
    })),
});

// MUI's Popover / ResponsiveContainer need ResizeObserver (not in jsdom)
global.ResizeObserver = jest.fn().mockImplementation(() => ({
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn(),
}));
