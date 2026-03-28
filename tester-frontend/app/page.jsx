'use client';
import { materialCells, materialRenderers } from '@jsonforms/material-renderers';
import { JsonForms } from '@jsonforms/react';
import CachedIcon from '@mui/icons-material/Cached';
import FormatListBulletedIcon from '@mui/icons-material/FormatListBulleted';
import {
    Backdrop,
    CircularProgress,
    FormControl,
    IconButton,
    LinearProgress,
    MenuItem,
    Paper,
    Select,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
} from '@mui/material';
import _ from 'lodash';
import Link from 'next/link';
import * as React from 'react';
import LogModal from './components/LogModal';
import LoginDialog from './components/LoginDialog';
import TestDialog from './components/TestDialog';
import TestResultRow from './components/TestResultRow';
import { useConnection } from './contexts/ConnectionContext';
import { SocketContext, socket } from './socket';

const STAT = ({ label, value, color }) => (
    <div className="flex flex-col items-center justify-center px-4 py-2 rounded-lg"
        style={{ background: 'rgba(255,255,255,0.04)', border: `1px solid ${color}30`, minWidth: 72 }}>
        <span className="text-xl font-bold font-mono leading-none" style={{ color }}>{value}</span>
        <span className="text-xs mt-1 font-medium" style={{ color: '#64748b' }}>{label}</span>
    </div>
);

export default function Home() {
    const { connected, connecting, isOnline } = useConnection();
    const [progress, setProgress] = React.useState(0);
    const [tester, setTester] = React.useState({});
    const [duts, setDuts] = React.useState([]);
    const [programs, setPrograms] = React.useState([]);
    const [activeDut, setActiveDut] = React.useState({});
    const [activeProgram, setActiveProgram] = React.useState({});
    const [run, setRun] = React.useState([]);
    const [canReport, setCanReport] = React.useState(false);
    const [testCases, setTestCases] = React.useState([]);
    const [showLog, setShowLog] = React.useState(false);
    const [log, setLog] = React.useState([]);
    const [showAttr, setShowAttr] = React.useState(false);
    const [operator, setOperator] = React.useState(undefined); // undefined = not yet received

    React.useEffect(() => calcProgress(tester), [tester]);
    React.useEffect(() => getState(), []);

    React.useEffect(() => {
        const handleTester = (data) => { setTester(data); setOperator(data?.operator ?? null); };
        const handleActiveDut = (data) => setActiveDut(data);
        const handleActiveProgram = (data) => {
            setActiveProgram(data);
            setTestCases(_.get(data, 'test_cases', []));
        };
        const handleTestExecuteState = (data) => {
            setTestCases(prev => prev.map(tc =>
                tc.id === data.test_id ? { ...tc, execute: data.execute } : tc
            ));
        };
        const handleLog = (data) => setLog(curr => [...curr, data]);
        const handleRun = (data) => setRun(data);
        const handleRunItem = (data) => {
            setRun(prev => { const n = [...prev]; n[data.idx] = data.item; return n; });
        };
        const handleLogClear = () => setLog([]);
        const handleState = (data) => {
            const t = _.get(data, 'tester', {});
            setTester(t);
            setOperator(t?.operator ?? null);
            setDuts(_.get(data, 'duts', []));
            setPrograms(_.get(data, 'programs', []));
            setActiveDut(_.get(data, 'dut', {}));
            setActiveProgram(_.get(data, 'program', {}));
            setTestCases(_.get(data, 'program.test_cases', []));
            setLog(_.get(data, 'log', []));
            setRun(_.get(data, 'run', {}));
        };

        socket.on('state', handleState);
        socket.on('tester', handleTester);
        socket.on('log', handleLog);
        socket.on('active_dut', handleActiveDut);
        socket.on('active_program', handleActiveProgram);
        socket.on('run', handleRun);
        socket.on('run_item', handleRunItem);
        socket.on('log_clear', handleLogClear);
        socket.on('test_execute_state', handleTestExecuteState);

        return () => {
            socket.off('state', handleState);
            socket.off('tester', handleTester);
            socket.off('log', handleLog);
            socket.off('active_dut', handleActiveDut);
            socket.off('active_program', handleActiveProgram);
            socket.off('run', handleRun);
            socket.off('run_item', handleRunItem);
            socket.off('log_clear', handleLogClear);
            socket.off('test_execute_state', handleTestExecuteState);
        };
    });

    const handleDutChange = (dut) => {
        socket.emit('set_dut', { dut });
        setTestCases([]);
    };
    const handleProgramChange = (program) => {
        socket.emit('set_program', { program });
        setTestCases([]);
    };
    const handleTestExecuteChange = (data) => socket.emit('test_execute_state', data);

    const runProgram = () => {
        socket.emit(_.get(tester, 'running', false) ? 'stop_run' : 'start_run');
    };

    const calcProgress = (t) => {
        const total = _.get(t, 'total', 0);
        const done  = _.get(t, 'done',  0);
        setProgress(total === 0 ? 0 : (100 * done) / total);
        setCanReport(done === total && total !== 0);
    };

    const getState = () => socket.emit('get_state');
    const reload   = () => socket.emit('reload');
    const setAttributes = (attr) => socket.emit('attr', attr);
    const handleDialogClose = (response, responseData) =>
        socket.emit('dialog_response', response, responseData);

    const running  = _.get(tester, 'running',  false);
    const stopping = _.get(tester, 'stopping', false);

    const hasAttr = Object.keys(
        _.get(activeProgram, 'attr_schema.properties', {})
    ).length > 0;

    return (
        <SocketContext.Provider value={socket}>
            <LoginDialog show={operator === null} />

            {/* Offline overlay */}
            <Backdrop
                open={!isOnline}
                sx={{ color: '#fff', zIndex: 9999, backdropFilter: 'blur(4px)', backgroundColor: 'rgba(13,17,23,0.85)' }}
            >
                <div className="text-center space-y-4">
                    <CircularProgress color="inherit" size={48} />
                    <p className="text-white font-medium">
                        {connecting ? 'Connecting to Test Framework…' : 'Backend Disconnected'}
                    </p>
                </div>
            </Backdrop>

            <LogModal open={showLog} handleClose={() => setShowLog(false)} log={log} />
            <TestDialog onClose={handleDialogClose} data={_.get(tester, 'dialog', {})} />

            {/* Log FAB */}
            <button
                onClick={() => setShowLog(true)}
                className="fixed bottom-6 right-6 z-50 w-12 h-12 rounded-full flex items-center justify-center transition-all duration-200 hover:scale-105"
                style={{ background: 'linear-gradient(135deg,#6366f1,#4338ca)', boxShadow: '0 4px 20px rgba(99,102,241,0.4)' }}
            >
                <FormatListBulletedIcon sx={{ fontSize: 20, color: '#fff' }} />
            </button>

            <div className="flex flex-col h-full">
                {/* ── Control bar ── */}
                <div className="shrink-0 px-6 pt-5 pb-4 space-y-4"
                    style={{ borderBottom: '1px solid #2d3748', backgroundColor: '#0d1117' }}>

                    {/* Row 1: tester info + run button */}
                    <div className="flex items-center justify-between gap-4">
                        <div className="min-w-0">
                            <h1 className="text-lg font-bold leading-tight truncate" style={{ color: '#e2e8f0' }}>
                                {_.get(tester, 'name', 'Test Framework')}
                            </h1>
                            <p className="text-xs truncate" style={{ color: '#64748b' }}>
                                v{_.get(tester, 'version', '—')} · fw {_.get(tester, 'fw_version', '—')}
                            </p>
                        </div>

                        <div className="flex items-center gap-2 shrink-0">
                            <IconButton
                                onClick={reload}
                                disabled={running || stopping}
                                size="small"
                                sx={{ color: '#64748b', '&:hover': { color: '#6366f1', backgroundColor: 'rgba(99,102,241,0.1)' } }}
                            >
                                <CachedIcon fontSize="small" />
                            </IconButton>

                            {/* Run / Stop */}
                            <button
                                onClick={runProgram}
                                disabled={stopping}
                                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200 disabled:opacity-40"
                                style={running
                                    ? { backgroundColor: 'rgba(239,68,68,0.12)', color: '#f87171', border: '1px solid rgba(239,68,68,0.35)' }
                                    : { background: 'linear-gradient(135deg,#6366f1,#4338ca)', color: '#fff', border: '1px solid transparent' }
                                }
                            >
                                {running
                                    ? <><span className="w-2 h-2 rounded-sm" style={{ backgroundColor: '#f87171' }} /> Stop</>
                                    : <><span>▶</span> Run</>
                                }
                            </button>

                            {canReport && (
                                <a
                                    href="/get_report"
                                    className="flex items-center gap-1 px-3 py-2 rounded-lg text-sm font-semibold transition-all duration-200"
                                    style={{ backgroundColor: 'rgba(16,185,129,0.12)', color: '#34d399', border: '1px solid rgba(16,185,129,0.3)' }}
                                >
                                    ↓ Report
                                </a>
                            )}
                        </div>
                    </div>

                    {/* Row 2: DUT + Program selects */}
                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="block text-xs font-medium mb-1" style={{ color: '#64748b' }}>
                                Device Under Test
                            </label>
                            <FormControl fullWidth size="small">
                                <Select
                                    disabled={running}
                                    value={_.get(activeDut, 'name', '')}
                                    onChange={(e) => handleDutChange(e.target.value)}
                                    displayEmpty
                                >
                                    <MenuItem value="" disabled>
                                        <span style={{ color: '#64748b' }}>Select device…</span>
                                    </MenuItem>
                                    {duts.map((d, i) => (
                                        <MenuItem key={i} value={d}>{d}</MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                        </div>
                        <div>
                            <label className="block text-xs font-medium mb-1" style={{ color: '#64748b' }}>
                                Test Program
                            </label>
                            <FormControl fullWidth size="small">
                                <Select
                                    disabled={running}
                                    value={_.get(activeProgram, 'name', '')}
                                    onChange={(e) => handleProgramChange(e.target.value)}
                                    displayEmpty
                                >
                                    <MenuItem value="" disabled>
                                        <span style={{ color: '#64748b' }}>Select program…</span>
                                    </MenuItem>
                                    {programs.map((p, i) => (
                                        <MenuItem key={i} value={p}>{p}</MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                        </div>
                    </div>

                    {/* Row 3: Stats */}
                    <div className="flex items-center gap-3 flex-wrap">
                        <STAT label="Done"    value={`${_.get(tester,'done',0)}/${_.get(tester,'total',0)}`} color="#818cf8" />
                        <STAT label="Pass"    value={_.get(tester,'pass',0)}    color="#10b981" />
                        <STAT label="Fail"    value={_.get(tester,'fail',0)}    color="#ef4444" />
                        <STAT label="Error"   value={_.get(tester,'error',0)}   color="#f59e0b" />
                        <STAT label="Skipped" value={_.get(tester,'skip',0)} color="#64748b" />
                        {_.get(tester,'aborted',0) > 0 &&
                            <STAT label="Aborted" value={_.get(tester,'aborted',0)} color="#8b5cf6" />
                        }
                        <div className="flex-1 min-w-32">
                            <LinearProgress variant="determinate" value={progress} sx={{ height: 4, borderRadius: 2 }} />
                            <div className="flex justify-between mt-1">
                                <span className="text-xs" style={{ color: '#64748b' }}>
                                    {_.get(tester,'text','Idle')}
                                </span>
                                <span className="text-xs font-mono" style={{ color: '#64748b' }}>
                                    {_.get(tester,'elapsed','00:00:00')}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Program attributes (collapsible) */}
                    {hasAttr && (
                        <div>
                            <button
                                onClick={() => setShowAttr(v => !v)}
                                className="flex items-center gap-2 text-xs font-medium transition-colors"
                                style={{ color: '#6366f1' }}
                            >
                                <span style={{ transform: showAttr ? 'rotate(90deg)' : 'rotate(0)', display: 'inline-block', transition: 'transform 0.2s' }}>▶</span>
                                Program Attributes
                            </button>
                            {showAttr && (
                                <div className="mt-3 p-4 rounded-lg" style={{ backgroundColor: '#161b2e', border: '1px solid #2d3748' }}>
                                    <JsonForms
                                        readonly={running}
                                        schema={_.get(activeProgram, 'attr_schema', { type: 'object', properties: {} })}
                                        data={_.get(activeProgram, 'attr', {})}
                                        renderers={materialRenderers}
                                        cells={materialCells}
                                        onChange={({ data }) => setAttributes(data)}
                                    />
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* ── Results table ── */}
                <div className="flex-1 overflow-auto">
                    <TableContainer component={Paper} sx={{ borderRadius: 0, height: '100%' }}>
                        <Table stickyHeader size="small" aria-label="test results">
                            <TableHead>
                                <TableRow>
                                    <TableCell align="center" sx={{ width: 64 }}>Run</TableCell>
                                    <TableCell sx={{ width: 72 }}>Time</TableCell>
                                    <TableCell>Suite</TableCell>
                                    <TableCell>Test Name</TableCell>
                                    <TableCell align="center" sx={{ width: 80 }}>Min</TableCell>
                                    <TableCell align="center" sx={{ width: 80 }}>Value</TableCell>
                                    <TableCell align="center" sx={{ width: 80 }}>Max</TableCell>
                                    <TableCell align="center" sx={{ width: 80 }}>Unit</TableCell>
                                    <TableCell align="center" sx={{ width: 96 }}>Result</TableCell>
                                    <TableCell>Comment</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {run.map((row, i) => (
                                    <TestResultRow
                                        key={i}
                                        row={row}
                                        active={i === _.get(tester, 'active_test', -1)}
                                        testCases={testCases}
                                        onExecuteChange={handleTestExecuteChange}
                                        disabled={running}
                                    />
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                </div>
            </div>
        </SocketContext.Provider>
    );
}
