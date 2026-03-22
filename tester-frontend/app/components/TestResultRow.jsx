import { Checkbox, TableCell, TableRow, Tooltip } from '@mui/material';
import _ from 'lodash';
import * as React from 'react';
import ResultPlot from './ResultPlot';

const RESULT_META = {
    PASS:     { color: '#10b981', bg: 'rgba(16,185,129,0.12)',  border: 'rgba(16,185,129,0.4)',  label: 'PASS'    },
    FAIL:     { color: '#ef4444', bg: 'rgba(239,68,68,0.12)',   border: 'rgba(239,68,68,0.4)',   label: 'FAIL'    },
    ERROR:    { color: '#f59e0b', bg: 'rgba(245,158,11,0.12)',  border: 'rgba(245,158,11,0.4)',  label: 'ERROR'   },
    INFOONLY: { color: '#60a5fa', bg: 'rgba(96,165,250,0.12)',  border: 'rgba(96,165,250,0.4)',  label: 'INFO'    },
    SKIPPED:  { color: '#64748b', bg: 'rgba(100,116,139,0.1)',  border: 'rgba(100,116,139,0.3)', label: 'SKIP'    },
    ABORTED:  { color: '#a78bfa', bg: 'rgba(167,139,250,0.12)', border: 'rgba(167,139,250,0.4)', label: 'ABORT'   },
};
const DEFAULT_META = { color: '#8b9eb0', bg: 'rgba(139,158,176,0.08)', border: 'rgba(139,158,176,0.2)', label: '—' };

export default function TestResultRow({ row, active, testCases = [], onExecuteChange, disabled = false }) {
    const [showPlot, setShowPlot] = React.useState(false);
    const [plotData, setPlotData] = React.useState({});
    const myRef = React.useRef(null);

    React.useEffect(() => {
        const pd = _.get(row, 'PlotData', {});
        setPlotData(pd);
        setShowPlot(Object.keys(pd).length > 0);
    }, [row]);

    React.useEffect(() => {
        if (active && myRef.current) {
            myRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, [active]);

    const result   = _.get(row, 'Result', '');
    const meta     = RESULT_META[result] || DEFAULT_META;

    // Find matching test case
    const testCase = React.useMemo(() => {
        const suite = _.get(row, 'Suite', '');
        const name  = _.get(row, 'Name',  '');
        let tc = testCases.find(t => t.suite === suite && t.name === name);
        if (!tc) {
            const type = name.toLowerCase().includes('setup') ? 'setup'
                       : name.toLowerCase().includes('cleanup') ? 'cleanup'
                       : 'testcase';
            tc = testCases.find(t => t.suite === suite && t.type === type);
        }
        return tc;
    }, [row, testCases]);

    const suiteUnchecked = React.useMemo(() => {
        if (!testCase || testCase.type === 'setup' || testCase.type === 'cleanup') return false;
        const suite   = testCase.suite;
        const setup   = testCases.find(t => t.suite === suite && t.type === 'setup');
        const cleanup = testCases.find(t => t.suite === suite && t.type === 'cleanup');
        return (setup && !setup.execute) || (cleanup && !cleanup.execute);
    }, [testCase, testCases]);

    const handleExecuteChange = (checked) => {
        if (testCase && onExecuteChange) {
            onExecuteChange({ test_id: testCase.id, execute: checked, type: testCase.type, suite: testCase.suite, name: testCase.name });
        }
    };

    const rowBg = active ? 'rgba(99,102,241,0.08)' : 'transparent';

    return (
        <React.Fragment>
            <TableRow
                ref={myRef}
                className="animate-slide-in"
                sx={{
                    backgroundColor: rowBg,
                    borderLeft: active ? '2px solid #6366f1' : `2px solid ${result ? meta.border : 'transparent'}`,
                    '&:hover': { backgroundColor: active ? 'rgba(99,102,241,0.12)' : 'rgba(255,255,255,0.03)' },
                    transition: 'background-color 0.15s ease',
                    '& td': { borderBottom: '1px solid rgba(45,55,72,0.5)' },
                }}
            >
                {/* Execute checkbox */}
                <TableCell align="center" sx={{ width: 64, opacity: (disabled || suiteUnchecked) ? 0.4 : 1 }}>
                    {testCase ? (
                        <Tooltip title={
                            disabled       ? 'Cannot change while running' :
                            suiteUnchecked ? 'Suite disabled' :
                            testCase.execute ? 'Skip this test' : 'Enable this test'
                        }>
                            <Checkbox
                                size="small"
                                checked={testCase.execute && !suiteUnchecked}
                                onChange={(e) => handleExecuteChange(e.target.checked)}
                                disabled={disabled || suiteUnchecked}
                            />
                        </Tooltip>
                    ) : (
                        <span style={{ color: '#334155' }}>—</span>
                    )}
                </TableCell>

                {/* Time */}
                <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.75rem', color: '#64748b', width: 72 }}>
                    {_.get(row, 'Time', '—')}
                </TableCell>

                {/* Suite */}
                <TableCell sx={{ fontSize: '0.8rem', color: '#94a3b8', fontWeight: 500 }}>
                    {_.get(row, 'Suite', '')}
                </TableCell>

                {/* Test name */}
                <TableCell sx={{ fontSize: '0.85rem', fontWeight: 600, color: active ? '#c7d2fe' : '#e2e8f0' }}>
                    {_.get(row, 'Name', '—')}
                    {active && (
                        <span className="ml-2 inline-block w-1.5 h-1.5 rounded-full animate-pulse-slow"
                            style={{ backgroundColor: '#6366f1', verticalAlign: 'middle' }} />
                    )}
                </TableCell>

                {/* Min / Value / Max */}
                <TableCell align="center" sx={{ fontFamily: 'monospace', fontSize: '0.75rem', color: '#64748b', width: 80 }}>
                    {_.get(row, 'Min', '')}
                </TableCell>
                <TableCell align="center" sx={{ fontFamily: 'monospace', fontSize: '0.85rem', fontWeight: 700, color: meta.color || '#e2e8f0', width: 80 }}>
                    {_.get(row, 'Value', '')}
                </TableCell>
                <TableCell align="center" sx={{ fontFamily: 'monospace', fontSize: '0.75rem', color: '#64748b', width: 80 }}>
                    {_.get(row, 'Max', '')}
                </TableCell>

                {/* Unit */}
                <TableCell align="center" sx={{ fontSize: '0.75rem', color: '#64748b', width: 80 }}>
                    {_.get(row, 'Unit', '')}
                </TableCell>

                {/* Result badge */}
                <TableCell align="center" sx={{ width: 96 }}>
                    {result && (
                        <span className="badge" style={{
                            backgroundColor: meta.bg,
                            color:           meta.color,
                            border:          `1px solid ${meta.border}`,
                        }}>
                            {meta.label}
                        </span>
                    )}
                </TableCell>

                {/* Comment */}
                <TableCell sx={{ fontSize: '0.75rem', color: '#64748b' }}>
                    {_.get(row, 'Comment', '')}
                </TableCell>
            </TableRow>

            <ResultPlot plotData={plotData} show={showPlot} />
        </React.Fragment>
    );
}
