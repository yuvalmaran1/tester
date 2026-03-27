import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Table, TableBody } from '@mui/material';
import TestResultRow from '../app/components/TestResultRow';

// TestResultRow renders a <TableRow> which must be inside a <Table><TableBody>
// to be valid HTML (avoids React DOM warnings in test output).
const wrap = (ui) =>
    render(
        <Table>
            <TableBody>{ui}</TableBody>
        </Table>
    );

// ── Badge label per result type ───────────────────────────────────────────────

const RESULT_LABELS = [
    ['PASS',     'PASS'],
    ['FAIL',     'FAIL'],
    ['ERROR',    'ERROR'],
    ['INFOONLY', 'INFO'],
    ['SKIPPED',  'SKIP'],
    ['ABORTED',  'ABORT'],
];

describe('badge label', () => {
    test.each(RESULT_LABELS)('result %s renders label %s', (result, label) => {
        wrap(<TestResultRow row={{ Result: result }} />);
        expect(screen.getByText(label)).toBeInTheDocument();
    });

    test('no badge rendered when result is empty', () => {
        const { container } = wrap(<TestResultRow row={{}} />);
        expect(container.querySelector('.badge')).toBeNull();
    });
});

// ── Row data cells ────────────────────────────────────────────────────────────

test('renders suite name', () => {
    wrap(<TestResultRow row={{ Suite: 'Power Rails', Result: 'PASS' }} />);
    expect(screen.getByText('Power Rails')).toBeInTheDocument();
});

test('renders test name', () => {
    wrap(<TestResultRow row={{ Name: '3.3V Rail', Result: 'PASS' }} />);
    expect(screen.getByText('3.3V Rail')).toBeInTheDocument();
});

test('renders measured value', () => {
    wrap(<TestResultRow row={{ Value: '3.31', Result: 'PASS' }} />);
    expect(screen.getByText('3.31')).toBeInTheDocument();
});

test('renders comment', () => {
    wrap(<TestResultRow row={{ Comment: 'out of range', Result: 'FAIL' }} />);
    expect(screen.getByText('out of range')).toBeInTheDocument();
});

// ── Execute checkbox ──────────────────────────────────────────────────────────

const makeTestCase = (overrides = {}) => ({
    id: 'Suite1_Test1',
    suite: 'Suite1',
    name: 'Test1',
    type: 'testcase',
    execute: true,
    ...overrides,
});

test('checkbox is checked when testCase.execute is true', () => {
    wrap(
        <TestResultRow
            row={{ Suite: 'Suite1', Name: 'Test1', Result: 'PASS' }}
            testCases={[makeTestCase({ execute: true })]}
        />
    );
    expect(screen.getByRole('checkbox')).toBeChecked();
});

test('checkbox is unchecked when testCase.execute is false', () => {
    wrap(
        <TestResultRow
            row={{ Suite: 'Suite1', Name: 'Test1' }}
            testCases={[makeTestCase({ execute: false })]}
        />
    );
    expect(screen.getByRole('checkbox')).not.toBeChecked();
});

test('checkbox is disabled when disabled prop is true', () => {
    wrap(
        <TestResultRow
            row={{ Suite: 'Suite1', Name: 'Test1' }}
            testCases={[makeTestCase()]}
            disabled={true}
        />
    );
    expect(screen.getByRole('checkbox')).toBeDisabled();
});

test('checkbox is disabled when suite setup is unchecked (suiteUnchecked)', () => {
    const setup   = makeTestCase({ name: 'Setup',  type: 'setup',    execute: false });
    const testCase = makeTestCase({ name: 'Test1', type: 'testcase', execute: true  });
    wrap(
        <TestResultRow
            row={{ Suite: 'Suite1', Name: 'Test1' }}
            testCases={[setup, testCase]}
        />
    );
    expect(screen.getByRole('checkbox')).toBeDisabled();
});

test('checkbox is enabled when suite setup is checked', () => {
    const setup    = makeTestCase({ name: 'Setup', type: 'setup',    execute: true });
    const testCase = makeTestCase({ name: 'Test1', type: 'testcase', execute: true });
    wrap(
        <TestResultRow
            row={{ Suite: 'Suite1', Name: 'Test1' }}
            testCases={[setup, testCase]}
        />
    );
    expect(screen.getByRole('checkbox')).not.toBeDisabled();
});

test('onExecuteChange is called with test_id when checkbox is toggled', async () => {
    const user = userEvent.setup();
    const onChange = jest.fn();
    wrap(
        <TestResultRow
            row={{ Suite: 'Suite1', Name: 'Test1' }}
            testCases={[makeTestCase()]}
            onExecuteChange={onChange}
        />
    );
    await user.click(screen.getByRole('checkbox'));
    expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ test_id: 'Suite1_Test1' })
    );
});

test('no checkbox rendered when no matching testCase', () => {
    wrap(<TestResultRow row={{ Suite: 'Suite1', Name: 'Test1' }} testCases={[]} />);
    expect(screen.queryByRole('checkbox')).toBeNull();
});
