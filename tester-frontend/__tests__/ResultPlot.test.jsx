import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import { Table, TableBody } from '@mui/material';
import ResultPlot from '../app/components/ResultPlot';

// ResultPlot renders an additional <TableRow>, so it also needs table context.
const wrap = (ui) =>
    render(
        <Table>
            <TableBody>{ui}</TableBody>
        </Table>
    );

const PLOT_DATA = {
    points: [
        { x: 0.0, value: 1.0, min: 0.8, max: 1.2 },
        { x: 1.0, value: 1.1, min: 0.8, max: 1.2 },
    ],
    xlabel: 'Time (s)',
    ylabel: 'Voltage (V)',
};

test('renders nothing when show is false', () => {
    const { container } = wrap(<ResultPlot show={false} plotData={{}} />);
    expect(container.querySelector('[data-testid="responsive-container"]')).toBeNull();
});

test('renders chart container when show is true', () => {
    wrap(<ResultPlot show={true} plotData={PLOT_DATA} />);
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
});

test('renders inner LineChart when show is true', () => {
    wrap(<ResultPlot show={true} plotData={PLOT_DATA} />);
    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
});
