'use client';
import { materialCells, materialRenderers } from '@jsonforms/material-renderers';
import { JsonForms } from '@jsonforms/react';
import CachedIcon from '@mui/icons-material/Cached';
import FormatListBulletedIcon from '@mui/icons-material/FormatListBulleted';
import {
    Button,
    FormControl,
    IconButton,
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow
} from '@mui/material';
import Backdrop from '@mui/material/Backdrop';
import CircularProgress from '@mui/material/CircularProgress';
import Fab from '@mui/material/Fab';
import LinearProgress from '@mui/material/LinearProgress';
import Link from '@mui/material/Link';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import _ from "lodash";
// import Image from 'next/image'; // Removed for static file serving
import * as React from 'react';
import LogModal from './components/LogModal';
import TestDialog from './components/TestDialog';
import TestResultRow from './components/TestResultRow';
import { useConnection } from './contexts/ConnectionContext';
import { SocketContext, socket } from './socket';


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

    React.useEffect(() => calcProgress(tester), [tester]);
    React.useEffect(() => getState(), []);
    React.useEffect(() => {

        const handleTester = (data) => {
            console.log("tester", data);
            setTester(data);
        };

        const handleActiveDut = (data) => {
            console.log("active DUT", data);
            setActiveDut(data);
        };

        const handleActiveProgram = (data) => {
            console.log("active Program", data);
            setActiveProgram(data);
            setTestCases(_.get(data, 'test_cases', []));
        };

        const handleTestExecuteState = (data) => {
            console.log("test execute state", data);
            // Update the local test cases state to reflect the change
            setTestCases(prevTestCases =>
                prevTestCases.map(tc =>
                    tc.id === data.test_id
                        ? { ...tc, execute: data.execute }
                        : tc
                )
            );
        };

        const handleLog = (data) => {
            setLog((curr) => [...curr, data]);
        };

        const handleRun = (data) => {
            console.log('run', data);
            setRun(data);
        };

        const handleRunItem = (data) => {
            console.log('run item', data);
            let newRun = [...run];
            newRun[data.idx] = data.item;
            setRun(newRun);
        };

        const handleLogClear = () => {
            setLog([]);
        };

        const handleState = (data) => {
            console.log("state", data);
            setTester(_.get(data, 'tester', {}));
            setDuts(_.get(data, 'duts', []));
            setPrograms(_.get(data, 'programs', []));
            setActiveDut(_.get(data, 'dut', {}));
            setActiveProgram(_.get(data, 'program', {}));
            setTestCases(_.get(data, 'program.test_cases', []));
            setLog(_.get(data, 'log', []));
            setRun(_.get(data, 'run', {}));
        };

        socket.on("state", handleState);
        socket.on("tester", handleTester);
        socket.on("log", handleLog);
        socket.on("active_dut", handleActiveDut);
        socket.on("active_program", handleActiveProgram);
        socket.on("run", handleRun);
        socket.on("run_item", handleRunItem);
        socket.on("log_clear", handleLogClear);
        socket.on("test_execute_state", handleTestExecuteState);

        return () => {
            socket.off("state", handleState);
            socket.off("tester", handleTester);
            socket.off("log", handleLog);
            socket.off("active_dut", handleActiveDut);
            socket.off("active_program", handleActiveProgram);
            socket.off("run", handleRun);
            socket.off("run_item", handleRunItem);
            socket.off("log_clear", handleLogClear);
            socket.off("test_execute_state", handleTestExecuteState);
        };
    });

    const handleDutChange = (dut) => {
        console.log(dut);
        socket.emit("set_dut", { "dut": dut });
        // Reset test cases when DUT changes
        setTestCases([]);
    };

    const handleProgramChange = (program) => {
        console.log(program);
        socket.emit("set_program", { "program": program });
        // Reset test cases when program changes
        setTestCases([]);
    };

    const handleTestExecuteChange = (data) => {
        console.log('test execute change', data);
        // Send the change to the backend via websocket
        socket.emit("test_execute_state", data);
    };

    const runProgram = () => {
        if (!_.get(tester, 'running', false)) {
            console.log('start_run');
            socket.emit("start_run");
        }
        else {
            console.log('stop_run');
            socket.emit("stop_run");
        }
    };

    const calcProgress = (t) => {
        if (_.get(t, 'total', 0) == 0) {
            setProgress(0);
        } else {
            setProgress((100 * t.done) / t.total);
        }

        if ((t.done === t.total) && (t.total != 0)) {
            setCanReport(true);
        }
        else {
            setCanReport(false);
        }
    };

    const getState = () => {
        socket.emit("get_state");
    };

    const reload = () => {
        socket.emit("reload");
    };

    const setAttributes = (attr) => {
        socket.emit("attr", attr);
    };

    const handleDialogClose = (response, responseData) => {
        console.log('handleClose invoked', response, responseData);
        socket.emit("dialog_response", response, responseData);
    };

    return (
        <SocketContext.Provider value={socket}>
            <div className="min-h-screen relative">
                <main className="animate-fade-in container mx-auto px-4 py-8 relative z-10">
                    <Fab
                        sx={{
                            position: 'fixed',
                            bottom: 24,
                            right: 24,
                            background: 'linear-gradient(135deg, #3b82f6 0%, #1e3a8a 100%)',
                            '&:hover': {
                                background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
                                transform: 'translateY(-2px) scale(1.05)'
                            }
                        }}
                        aria-label="log"
                        onClick={(e) => { setShowLog(true); }}
                    >
                        <FormatListBulletedIcon />
                    </Fab>
                    <LogModal open={showLog} handleClose={() => setShowLog(false)} log={log} />
                    <TestDialog onClose={handleDialogClose} data={_.get(tester, 'dialog', {})} />

                    <Backdrop
                        sx={{
                            color: "#FFFFFF",
                            zIndex: (theme) => theme.zIndex.drawer + 1,
                            position: "fixed",
                            background: 'rgba(30, 58, 138, 0.8)',
                            backdropFilter: 'blur(4px)'
                        }}
                        open={!isOnline}
                    >
                        <div className="text-center">
                            <CircularProgress color="inherit" size={60} />
                            <div className="mt-4 text-white text-lg font-medium">
                                {connecting ? 'Connecting to Test Framework...' : 'Backend Disconnected'}
                            </div>
                            {!connecting && (
                                <div className="mt-2 text-white text-sm opacity-75">
                                    Please check your connection and try again
                                </div>
                            )}
                        </div>
                    </Backdrop>

                    {/* Header Section */}
                    <div className="card mb-8 relative overflow-hidden">
                        <div className="absolute inset-0 bg-gradient-to-r from-primary-500/10 via-accent-500/10 to-secondary-500/10"></div>
                        <div className="relative z-10">
                            <div className="flex items-center justify-between mb-6">
                                <div>
                                    <h1 className="text-5xl font-bold text-primary-600 mb-2">
                                        {_.get(tester, 'name', 'Test Framework')}
                                    </h1>
                                    <p className="text-gray-700 text-xl font-medium">
                                        {_.get(tester, 'description', 'HiL Testing Framework')}
                                    </p>
                                </div>
                                <div className="text-center space-y-3">
                                    <div className="bg-gradient-to-r from-primary-500 to-primary-600 text-white px-4 py-2 rounded-full">
                                        <div className="text-sm opacity-90">Tester Version</div>
                                        <div className="text-lg font-bold">
                                            {_.get(tester, 'version', 'xx.xx.xx')}
                                        </div>
                                    </div>
                                    <div className="bg-gradient-to-r from-accent-500 to-accent-600 text-white px-4 py-2 rounded-full">
                                        <div className="text-sm opacity-90">Framework Version</div>
                                        <div className="text-lg font-bold">
                                            {_.get(tester, 'fw_version', 'xx.xx.xx')}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Configuration Section */}
                    <div className="card mb-8 relative">
                        <div className="flex items-center justify-between mb-6">
                            <div className="flex items-center gap-3">
                                <div className="w-1 h-8 bg-gradient-to-b from-primary-500 to-accent-500 rounded-full"></div>
                                <h2 className="text-3xl font-bold bg-gradient-to-r from-primary-600 to-accent-500 bg-clip-text text-transparent">
                                    Test Configuration
                                </h2>
                            </div>
                            <IconButton
                                disabled={_.get(tester, 'running', false) || _.get(tester, 'stopping', false)}
                                onClick={() => { reload(); }}
                                sx={{
                                    padding: '8px',
                                    color: '#475569',
                                    '&:hover': {
                                        backgroundColor: '#f1f5f9',
                                        color: '#334155'
                                    },
                                    '&:disabled': {
                                        color: '#9ca3af'
                                    }
                                }}
                                aria-label="refresh"
                            >
                                <CachedIcon />
                            </IconButton>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 mb-6">
                            {/* Device Under Test */}
                            <div className="md:col-span-4">
                                <div className="space-y-2">
                                    <label className="block text-sm font-medium text-gray-700">
                                        Device Under Test
                                    </label>
                                    <FormControl sx={{ width: '100%' }}>
                                        <Select
                                            disabled={_.get(tester, 'running', false)}
                                            value={_.get(activeDut, 'name', '')}
                                            onChange={(e) => { handleDutChange(e.target.value); }}
                                            displayEmpty
                                            sx={{
                                                '& .MuiOutlinedInput-root': {
                                                    borderRadius: '12px',
                                                    backgroundColor: '#f8fafc',
                                                    border: '1px solid #e2e8f0',
                                                    '&:hover': {
                                                        borderColor: '#cbd5e1'
                                                    },
                                                    '&.Mui-focused': {
                                                        borderColor: '#475569',
                                                        boxShadow: '0 0 0 3px rgba(71, 85, 105, 0.1)'
                                                    }
                                                },
                                                '& .MuiSelect-select': {
                                                    padding: '12px 16px',
                                                    fontSize: '14px',
                                                    color: '#374151'
                                                }
                                            }}
                                        >
                                            <MenuItem value="" disabled>
                                                <span className="text-gray-400">Select device</span>
                                            </MenuItem>
                                            {duts.map((dut, index) => (
                                                <MenuItem key={index} value={dut}>
                                                    {dut}
                                                </MenuItem>
                                            ))}
                                        </Select>
                                    </FormControl>
                                    <p className="text-xs text-gray-500">Select the device to test</p>
                                </div>
                            </div>

                            {/* Test Program */}
                            <div className="md:col-span-4">
                                <div className="space-y-2">
                                    <label className="block text-sm font-medium text-gray-700">
                                        Test Program
                                    </label>
                                    <FormControl sx={{ width: '100%' }}>
                                        <Select
                                            disabled={_.get(tester, 'running', false)}
                                            value={_.get(activeProgram, 'name', '')}
                                            onChange={(e) => { handleProgramChange(e.target.value); }}
                                            displayEmpty
                                            sx={{
                                                '& .MuiOutlinedInput-root': {
                                                    borderRadius: '12px',
                                                    backgroundColor: '#f8fafc',
                                                    border: '1px solid #e2e8f0',
                                                    '&:hover': {
                                                        borderColor: '#cbd5e1'
                                                    },
                                                    '&.Mui-focused': {
                                                        borderColor: '#475569',
                                                        boxShadow: '0 0 0 3px rgba(71, 85, 105, 0.1)'
                                                    }
                                                },
                                                '& .MuiSelect-select': {
                                                    padding: '12px 16px',
                                                    fontSize: '14px',
                                                    color: '#374151'
                                                }
                                            }}
                                        >
                                            <MenuItem value="" disabled>
                                                <span className="text-gray-400">Select program</span>
                                            </MenuItem>
                                            {programs.map((program, index) => (
                                                <MenuItem key={index} value={program}>
                                                    {program}
                                                </MenuItem>
                                            ))}
                                        </Select>
                                    </FormControl>
                                    <p className="text-xs text-gray-500">Select the test program to run</p>
                                </div>
                            </div>

                            {/* Actions Buttons */}
                            <div className="md:col-span-4">
                                <div className="space-y-2">
                                    <label className="block text-sm font-medium text-gray-700">
                                        Actions
                                    </label>
                                    <div className="flex gap-2">
                                        <Button
                                            disabled={_.get(tester, 'stopping', false)}
                                            onClick={() => { runProgram(); }}
                                            variant={_.get(tester, 'running', false) ? "outlined" : "contained"}
                                            sx={{
                                                width: '100%',
                                                height: '48px',
                                                borderRadius: '12px',
                                                fontWeight: 600,
                                                fontSize: '0.875rem',
                                                ...(_.get(tester, 'running', false) ? {
                                                    borderColor: '#ef4444',
                                                    color: '#ef4444',
                                                    backgroundColor: '#f8fafc',
                                                    '&:hover': {
                                                        borderColor: '#dc2626',
                                                        backgroundColor: '#fef2f2'
                                                    }
                                                } : {
                                                    background: 'linear-gradient(135deg, #3b82f6 0%, #1e3a8a 100%)',
                                                    '&:hover': {
                                                        background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)'
                                                    },
                                                    '&:disabled': {
                                                        background: '#e2e8f0',
                                                        color: '#9ca3af'
                                                    }
                                                })
                                            }}
                                        >
                                            {_.get(tester, 'running', false) ? "Stop" : "Start"}
                                        </Button>
                                    </div>
                                    <p className="text-xs text-gray-500 text-left">
                                        {_.get(tester, 'running', false) ? "Stop test execution" : "Start test execution"}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Program Attributes - Only show if not empty */}
                        {_.get(activeProgram, 'attr_schema', { "type": "object", "properties": {} }).properties &&
                            Object.keys(_.get(activeProgram, 'attr_schema', { "type": "object", "properties": {} }).properties).length > 0 && (
                                <div className="mt-8">
                                    <div className="space-y-2 mb-4">
                                        <h3 className="text-lg font-semibold text-gray-800">Program Attributes</h3>
                                        <p className="text-sm text-gray-500">Configure test parameters and settings</p>
                                    </div>
                                    <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
                                        <JsonForms
                                            readonly={_.get(tester, 'running', false)}
                                            schema={_.get(activeProgram, 'attr_schema', { "type": "object", "properties": {} })}
                                            data={_.get(activeProgram, 'attr', {})}
                                            renderers={materialRenderers}
                                            cells={materialCells}
                                            onChange={({ data, errors }) => setAttributes(data)}
                                        />
                                    </div>
                                </div>
                            )}
                    </div>

                    {/* Device and Program Information */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
                        {/* Device Information */}
                        <div className="card relative overflow-hidden">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-primary-500/20 to-accent-500/20 rounded-full -translate-y-16 translate-x-16"></div>
                            <div className="relative z-10">
                                <div className="flex items-center mb-4">
                                    <div className="w-12 h-12 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center mr-4 shadow-lg">
                                        <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                                        </svg>
                                    </div>
                                    <h2 className="text-2xl font-bold bg-gradient-to-r from-primary-600 to-accent-500 bg-clip-text text-transparent">Device Under Test</h2>
                                </div>

                                <div className="flex gap-8">
                                    {/* Left side - Text information */}
                                    <div className="flex-1 space-y-4">
                                        <div>
                                            <div className="text-sm text-gray-500 mb-1">Device Name</div>
                                            <div className="text-lg font-semibold text-gray-800">
                                                {_.get(activeDut, 'name', 'No device selected')}
                                            </div>
                                        </div>

                                        <div>
                                            <div className="text-sm text-gray-500 mb-1">Description</div>
                                            <div className="text-gray-700">
                                                {_.get(activeDut, 'description', 'No description available')}
                                            </div>
                                        </div>

                                        <div>
                                            <div className="text-sm text-gray-500 mb-1">Product ID</div>
                                            <div className="text-gray-700 font-mono bg-gray-100 px-3 py-1 rounded-lg inline-block">
                                                {_.get(activeDut, 'product_id', 'N/A')}
                                            </div>
                                        </div>
                                    </div>

                                    {/* Right side - Device Image */}
                                    {_.get(activeDut, 'name') && (
                                        <div className="w-2/5 flex items-center justify-center">
                                            <img
                                                src={`/dut_image?${_.get(activeDut, 'name', 'DUT')}`}
                                                alt={`${_.get(activeDut, 'name', 'DUT')} device`}
                                                width={400}
                                                height={300}
                                                className="max-w-full max-h-full object-contain"
                                                onError={(e) => {
                                                    e.target.style.display = 'none';
                                                    e.target.nextSibling.style.display = 'flex';
                                                }}
                                            />
                                            <div className="hidden flex-col items-center justify-center text-gray-400">
                                                <svg className="w-12 h-12 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                                </svg>
                                                <span className="text-sm">No image available</span>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Program Information */}
                        <div className="card relative overflow-hidden">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-accent-500/20 to-secondary-500/20 rounded-full -translate-y-16 translate-x-16"></div>
                            <div className="relative z-10">
                                <div className="flex items-center mb-4">
                                    <div className="w-12 h-12 bg-gradient-to-br from-accent-500 to-accent-600 rounded-xl flex items-center justify-center mr-4 shadow-lg">
                                        <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                                        </svg>
                                    </div>
                                    <h2 className="text-2xl font-bold bg-gradient-to-r from-accent-600 to-secondary-500 bg-clip-text text-transparent">Test Program</h2>
                                </div>

                                <div className="space-y-4">
                                    <div>
                                        <div className="text-sm text-gray-500 mb-1">Program Name</div>
                                        <div className="text-lg font-semibold text-gray-800">
                                            {_.get(activeProgram, 'name', 'No program selected')}
                                        </div>
                                    </div>

                                    <div>
                                        <div className="text-sm text-gray-500 mb-1">Description</div>
                                        <div className="text-gray-700">
                                            {_.get(activeProgram, 'description', 'No description available')}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Test Execution Control - Sticky */}
                    <div className="card mb-8" style={{
                        position: 'sticky',
                        top: '1rem',
                        zIndex: 40,
                        backgroundColor: '#f8fafc',
                        border: '1px solid #e2e8f0',
                        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03)',
                        backdropFilter: 'blur(8px)'
                    }}>
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-1 h-6 bg-gradient-to-b from-accent-500 to-secondary-500 rounded-full"></div>
                            <h2 className="text-2xl font-bold bg-gradient-to-r from-accent-600 to-secondary-500 bg-clip-text text-transparent">
                                Test Execution
                            </h2>
                        </div>

                        {/* Row 1: Status Cards */}
                        <div className="grid grid-cols-3 md:grid-cols-6 gap-3 mb-4">
                            <div className="bg-gradient-to-br from-primary-500 to-primary-600 text-white p-3 rounded-lg text-center shadow-md">
                                <div className="text-2xl font-bold mb-1">
                                    {_.get(tester, 'done', 0)}/{_.get(tester, 'total', 0)}
                                </div>
                                <div className="text-xs opacity-90 font-medium">Completed</div>
                            </div>

                            <div className="bg-gradient-to-br from-success-500 to-success-600 text-white p-3 rounded-lg text-center shadow-md">
                                <div className="text-2xl font-bold mb-1">
                                    {_.get(tester, 'pass', 0)}
                                </div>
                                <div className="text-xs opacity-90 font-medium">Passed</div>
                            </div>

                            <div className="bg-gradient-to-br from-danger-500 to-danger-600 text-white p-3 rounded-lg text-center shadow-md">
                                <div className="text-2xl font-bold mb-1">
                                    {_.get(tester, 'fail', 0)}
                                </div>
                                <div className="text-xs opacity-90 font-medium">Failed</div>
                            </div>

                            <div className="bg-gradient-to-br from-warning-500 to-warning-600 text-white p-3 rounded-lg text-center shadow-md">
                                <div className="text-2xl font-bold mb-1">
                                    {_.get(tester, 'error', 0)}
                                </div>
                                <div className="text-xs opacity-90 font-medium">Errors</div>
                            </div>

                            <div className="bg-gradient-to-br from-gray-500 to-gray-600 text-white p-3 rounded-lg text-center shadow-md">
                                <div className="text-2xl font-bold mb-1">
                                    {_.get(tester, 'skipped', 0)}
                                </div>
                                <div className="text-xs opacity-90 font-medium">Skipped</div>
                            </div>

                            <div className="bg-gradient-to-br from-purple-500 to-purple-600 text-white p-3 rounded-lg text-center shadow-md">
                                <div className="text-2xl font-bold mb-1">
                                    {_.get(tester, 'aborted', 0)}
                                </div>
                                <div className="text-xs opacity-90 font-medium">Aborted</div>
                            </div>
                        </div>

                        {/* Row 2: Progress, Status, and Controls */}
                        <div className="flex flex-col lg:flex-row gap-4 items-center">
                            {/* Progress Bar */}
                            <div className="flex-1 min-w-0">
                                <div className="flex justify-between items-center mb-1">
                                    <span className="text-sm font-medium text-gray-700">Progress</span>
                                    <span className="text-sm text-gray-500">{Math.round(progress)}%</span>
                                </div>
                                <LinearProgress
                                    variant="determinate"
                                    value={progress}
                                    sx={{
                                        height: 8,
                                        borderRadius: 4,
                                        backgroundColor: '#e2e8f0',
                                        '& .MuiLinearProgress-bar': {
                                            borderRadius: 4,
                                            background: 'linear-gradient(90deg, #3b82f6 0%, #1e3a8a 100%)'
                                        }
                                    }}
                                />
                            </div>

                            {/* Status and Controls */}
                            <div className="flex flex-col sm:flex-row gap-3 items-center">
                                {/* Status */}
                                <div className="flex items-center gap-2">
                                    {_.get(tester, 'total', 0) > 0 && (() => {
                                        const total = _.get(tester, 'total', 0);
                                        const done = _.get(tester, 'done', 0);
                                        const running = _.get(tester, 'running', false);
                                        const pass = _.get(tester, 'pass', 0);
                                        const fail = _.get(tester, 'fail', 0);
                                        const error = _.get(tester, 'error', 0);

                                        let stateColor = '#6b7280';
                                        let stateIcon = 'fas fa-question-circle';
                                        let stateText = 'Unknown';

                                        if (running) {
                                            stateColor = '#3b82f6';
                                            stateIcon = 'fas fa-spinner fa-spin';
                                            stateText = 'Running';
                                        } else if (done === total && total > 0) {
                                            if (fail > 0 || error > 0) {
                                                stateColor = '#ef4444';
                                                stateIcon = 'fas fa-times-circle';
                                                stateText = 'Failed';
                                            } else if (pass > 0) {
                                                stateColor = '#10b981';
                                                stateIcon = 'fas fa-check-circle';
                                                stateText = 'Passed';
                                            } else {
                                                stateColor = '#6b7280';
                                                stateIcon = 'fas fa-info-circle';
                                                stateText = 'Completed';
                                            }
                                        } else if (done > 0) {
                                            stateColor = '#f59e0b';
                                            stateIcon = 'fas fa-clock';
                                            stateText = 'In Progress';
                                        }

                                        return (
                                            <div className="flex items-center gap-2 px-3 py-1 rounded-lg border" style={{ borderColor: stateColor, color: stateColor }}>
                                                <i className={`${stateIcon} text-sm`}></i>
                                                <span className="text-sm font-medium">{stateText}</span>
                                            </div>
                                        );
                                    })()}
                                </div>

                                {/* Control Buttons */}
                                <div className="flex gap-2">
                                    <Button
                                        disabled={_.get(tester, 'stopping', false)}
                                        onClick={() => { runProgram(); }}
                                        variant={_.get(tester, 'running', false) ? "outlined" : "contained"}
                                        sx={{
                                            minWidth: 100,
                                            height: 36,
                                            borderRadius: '8px',
                                            fontWeight: 600,
                                            fontSize: '0.875rem',
                                            ...(_.get(tester, 'running', false) ? {
                                                borderColor: '#ef4444',
                                                color: '#ef4444',
                                                '&:hover': {
                                                    borderColor: '#dc2626',
                                                    backgroundColor: '#fef2f2'
                                                }
                                            } : {
                                                background: 'linear-gradient(135deg, #3b82f6 0%, #1e3a8a 100%)',
                                                '&:hover': {
                                                    background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)'
                                                }
                                            })
                                        }}
                                    >
                                        {_.get(tester, 'running', false) ? "Stop" : "Start"}
                                    </Button>

                                    <Button
                                        component={Link}
                                        href="/get_report"
                                        variant="outlined"
                                        disabled={!canReport}
                                        sx={{
                                            minWidth: 100,
                                            height: 36,
                                            borderRadius: '8px',
                                            fontWeight: 600,
                                            fontSize: '0.875rem',
                                            borderColor: '#10b981',
                                            color: '#10b981',
                                            '&:hover': {
                                                borderColor: '#059669',
                                                backgroundColor: '#ecfdf5'
                                            },
                                            '&:disabled': {
                                                borderColor: '#d1d5db',
                                                color: '#9ca3af'
                                            }
                                        }}
                                    >
                                        Report
                                    </Button>
                                </div>
                            </div>
                        </div>

                        {/* Current Test Info */}
                        <div className="mt-3 pt-3 border-t border-gray-200">
                            <div className="flex justify-between items-center text-sm">
                                <div className="text-gray-700 font-medium">
                                    {_.get(tester, 'text', 'Idle')}
                                </div>
                                <div className="text-gray-500">
                                    Elapsed: {_.get(tester, 'elapsed', '00:00:00')}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Test Results Table */}
                    <div className="card">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="w-1 h-8 bg-gradient-to-b from-primary-500 to-accent-500 rounded-full"></div>
                            <h2 className="text-2xl font-semibold text-primary-700">Test Results</h2>
                        </div>
                        <TableContainer component={Paper} sx={{ overflowX: 'auto', borderRadius: '12px' }}>
                            <Table aria-label="test results table" stickyHeader>
                                <TableHead>
                                    <TableRow>
                                        <TableCell align="center" sx={{ fontWeight: 600, color: '#374151', width: '80px' }}>
                                            Execute
                                        </TableCell>
                                        <TableCell align="left" sx={{ fontWeight: 600, color: '#374151' }}>Time</TableCell>
                                        <TableCell align="left" sx={{ fontWeight: 600, color: '#374151' }}>Suite</TableCell>
                                        <TableCell align="left" sx={{ fontWeight: 600, color: '#374151' }}>Test Name</TableCell>
                                        <TableCell align="center" sx={{ fontWeight: 600, color: '#374151' }}>Min</TableCell>
                                        <TableCell align="center" sx={{ fontWeight: 600, color: '#374151' }}>Value</TableCell>
                                        <TableCell align="center" sx={{ fontWeight: 600, color: '#374151' }}>Max</TableCell>
                                        <TableCell align="center" sx={{ fontWeight: 600, color: '#374151' }}>Unit</TableCell>
                                        <TableCell align="center" sx={{ fontWeight: 600, color: '#374151' }}>Result</TableCell>
                                        <TableCell align="left" sx={{ fontWeight: 600, color: '#374151' }}>Comment</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {run.map((row, index) => (
                                        <TestResultRow
                                            key={index}
                                            row={row}
                                            active={index == _.get(tester, 'active_test', -1)}
                                            testCases={testCases}
                                            onExecuteChange={handleTestExecuteChange}
                                            disabled={_.get(tester, 'running', false)}
                                        />
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    </div>
                </main>
            </div>
        </SocketContext.Provider>
    );
}
