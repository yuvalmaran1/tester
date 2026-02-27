import {
    Checkbox,
    TableCell,
    TableRow,
    Tooltip
} from '@mui/material';
import _ from "lodash";
import * as React from 'react';
import ResultPlot from './ResultPlot';

export default function TestResultRow(props) {
    const { row, active, testCases = [], onExecuteChange, disabled = false } = props;
    const [showPlot, setShowPlot] = React.useState(false);
    const [resStyle, setResStyle] = React.useState({});
    const [plotData, setPlotData] = React.useState({});
    React.useEffect(() => evalResultColor(row), [row]);
    React.useEffect(() => scrollHandler(active, myRef), [active]);
    const myRef = React.useRef(null);

    const scrollHandler = (a, ref) => {
        if ((a === true) && (ref) && (ref.current)) {
            ref.current.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
        }
    };

    // Find the corresponding test case for this result row
    const findTestCase = () => {
        const suite = _.get(row, 'Suite', '');
        const name = _.get(row, 'Name', '');

        // Try to find exact match first
        let testCase = testCases.find(tc => tc.suite === suite && tc.name === name);

        // If not found, try to match by suite and type
        if (!testCase) {
            // Determine type based on name patterns or other logic
            let type = 'testcase'; // default
            if (name.toLowerCase().includes('setup')) {
                type = 'setup';
            } else if (name.toLowerCase().includes('cleanup')) {
                type = 'cleanup';
            }

            testCase = testCases.find(tc => tc.suite === suite && tc.type === type);
        }

        return testCase;
    };

    const testCase = findTestCase();

    // Check if the suite is unchecked (either setup OR cleanup is unchecked)
    // But don't dim the setup/cleanup tests themselves - they control the suite
    const isSuiteUnchecked = () => {
        if (!testCase || testCase.type === 'setup' || testCase.type === 'cleanup') return false;
        const suite = testCase.suite;
        const setupTestCase = testCases.find(tc => tc.suite === suite && tc.type === 'setup');
        const cleanupTestCase = testCases.find(tc => tc.suite === suite && tc.type === 'cleanup');

        // Suite is unchecked if either setup OR cleanup is unchecked
        const setupUnchecked = setupTestCase && !setupTestCase.execute;
        const cleanupUnchecked = cleanupTestCase && !cleanupTestCase.execute;

        return setupUnchecked || cleanupUnchecked;
    };

    const suiteUnchecked = isSuiteUnchecked();

    const handleExecuteChange = (checked) => {
        if (testCase && onExecuteChange) {
            onExecuteChange({
                test_id: testCase.id,
                execute: checked,
                type: testCase.type,
                suite: testCase.suite,
                name: testCase.name
            });
        }
    };

    const evalResultColor = (r) => {
        let res = _.get(r, 'Result', 'UNKNOWN');
        let plotData = _.get(r, 'PlotData', {});
        let style = {};
        switch (res) {
            case 'PASS':
                style = { color: '#10b981', fontWeight: '600' };
                break;
            case 'FAIL':
                style = { color: '#ef4444', fontWeight: '600' };
                break;
            case 'ERROR':
                style = { color: '#f59e0b', fontWeight: '600' };
                break;
            case 'INFOONLY':
                style = { color: '#3b82f6', fontWeight: '600' };
                break;
            case 'SKIPPED':
                style = { color: '#64748b', fontWeight: '600' };
                break;
            case 'ABORTED':
                style = { color: '#8b5cf6', fontWeight: '600' };
                break;
        }

        setResStyle(style);
        setPlotData(plotData);
        setShowPlot(Object.keys(plotData).length != 0);
    };

    return (
        <React.Fragment>
            <TableRow
                ref={myRef}
                sx={{
                    '& > *': { borderBottom: '1px solid #f1f5f9' },
                    backgroundColor: active ? '#eff6ff' : 'transparent',
                    '&:hover': {
                        backgroundColor: active ? '#dbeafe' : '#f8fafc'
                    },
                    transition: 'background-color 0.2s ease'
                }}
                selected={active}
            >
                <TableCell align="center" sx={{
                    width: '80px',
                    opacity: (disabled || suiteUnchecked) ? 0.6 : 1
                }}>
                    {testCase ? (
                        <Tooltip
                            title={
                                disabled ? "Cannot change while test is running" :
                                    suiteUnchecked ? "Test skipped because suite setup or cleanup is disabled" :
                                        testCase.execute ? "Click to skip this test" : "Click to execute this test"
                            }
                        >
                            <Checkbox
                                checked={testCase.execute && !suiteUnchecked}
                                onChange={(e) => handleExecuteChange(e.target.checked)}
                                disabled={disabled || suiteUnchecked}
                                sx={{
                                    color: '#10b981',
                                    '&.Mui-checked': {
                                        color: '#10b981',
                                    },
                                    '&.Mui-disabled': {
                                        opacity: 0.5,
                                    }
                                }}
                            />
                        </Tooltip>
                    ) : (
                        <span style={{ color: '#64748b', fontSize: '0.75rem' }}>-</span>
                    )}
                </TableCell>
                <TableCell align="left" sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                    {_.get(row, 'Time', '00:00:00')}
                </TableCell>
                <TableCell align="left" sx={{ fontWeight: 500 }}>
                    {_.get(row, 'Suite', 'undefined')}
                </TableCell>
                <TableCell align="left" sx={{ fontWeight: 500 }}>
                    {_.get(row, 'Name', 'unnamed')}
                </TableCell>
                <TableCell sx={{ wordBreak: "break-all", fontFamily: 'monospace' }} align="center">
                    {_.get(row, 'Min', '')}
                </TableCell>
                <TableCell sx={{ wordBreak: "break-all", fontFamily: 'monospace', fontWeight: 600 }} align="center">
                    {_.get(row, 'Value', '')}
                </TableCell>
                <TableCell sx={{ wordBreak: "break-all", fontFamily: 'monospace' }} align="center">
                    {_.get(row, 'Max', '')}
                </TableCell>
                <TableCell align="center" sx={{ fontSize: '0.875rem', color: '#64748b' }}>
                    {_.get(row, 'Unit', '')}
                </TableCell>
                <TableCell align="center">
                    <span
                        className={`px-3 py-1 rounded-full text-xs font-semibold ${_.get(row, 'Result', '') === 'PASS' ? 'bg-success-100 text-success-800' :
                            _.get(row, 'Result', '') === 'FAIL' ? 'bg-danger-100 text-danger-800' :
                                _.get(row, 'Result', '') === 'ERROR' ? 'bg-warning-100 text-warning-800' :
                                    _.get(row, 'Result', '') === 'SKIPPED' ? 'bg-gray-100 text-gray-800' :
                                        'bg-primary-100 text-primary-800'
                            }`}
                    >
                        {_.get(row, 'Result', '')}
                    </span>
                </TableCell>
                <TableCell align="left" sx={{ fontSize: '0.875rem', color: '#64748b' }}>
                    {_.get(row, 'Comment', '')}
                </TableCell>
            </TableRow>
            <ResultPlot plotData={plotData} show={showPlot} />
        </React.Fragment>
    );
}
