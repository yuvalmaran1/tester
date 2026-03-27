const nextJest = require('next/jest');

const createJestConfig = nextJest({ dir: './' });

/** @type {import('jest').Config} */
const customConfig = {
    testEnvironment: 'jest-environment-jsdom',
    // setupFiles runs before Jest globals (describe/test/expect) are available
    // so it is safe for polyfills (matchMedia, ResizeObserver) but NOT for
    // @testing-library/jest-dom — import that at the top of each test file.
    setupFiles: ['<rootDir>/jest.setup.js'],
    moduleNameMapper: {
        // Avoid ResizeObserver / SVG issues by swapping recharts for a thin stub
        '^recharts$': '<rootDir>/__mocks__/recharts.js',
    },
};

module.exports = createJestConfig(customConfig);
