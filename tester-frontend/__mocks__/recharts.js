/**
 * Minimal recharts stub for Jest / jsdom.
 *
 * The real recharts uses SVG and ResizeObserver which are not available in
 * jsdom.  This stub replaces every exported component with a lightweight
 * React element so that components using recharts can be rendered in unit
 * tests without SVG / observer errors.
 */
const React = require('react');

const Container = ({ children, 'data-testid': tid }) =>
    React.createElement('div', { 'data-testid': tid || 'recharts-container' }, children);

const Noop = () => null;

module.exports = {
    ResponsiveContainer: ({ children }) =>
        React.createElement('div', { 'data-testid': 'responsive-container' }, children),
    LineChart: ({ children }) =>
        React.createElement('div', { 'data-testid': 'line-chart' }, children),
    Line: Noop,
    XAxis: Noop,
    YAxis: Noop,
    CartesianGrid: Noop,
    Tooltip: Noop,
    Legend: Noop,
    BarChart: ({ children }) => React.createElement('div', { 'data-testid': 'bar-chart' }, children),
    Bar: Noop,
    Cell: Noop,
    ReferenceLine: Noop,
};
