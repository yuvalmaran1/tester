"use client";
import {
    Backdrop,
    Box,
    Chip,
    CircularProgress,
    FormControl,
    InputLabel,
    MenuItem,
    OutlinedInput,
    Paper,
    Select,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    TextField,
} from "@mui/material";
import axios from 'axios';
import * as React from "react";
import ResultPlot from '../components/ResultPlot';
import TestHistogram from '../components/TestHistogram';
import { useConnection } from '../contexts/ConnectionContext';

const RESULT_META = {
    PASS:    { color: '#10b981', bg: 'rgba(16,185,129,0.12)',  border: 'rgba(16,185,129,0.3)'  },
    FAIL:    { color: '#ef4444', bg: 'rgba(239,68,68,0.12)',   border: 'rgba(239,68,68,0.3)'   },
    ERROR:   { color: '#f59e0b', bg: 'rgba(245,158,11,0.12)',  border: 'rgba(245,158,11,0.3)'  },
    SKIPPED: { color: '#64748b', bg: 'rgba(100,116,139,0.1)',  border: 'rgba(100,116,139,0.25)'},
    ABORTED: { color: '#a78bfa', bg: 'rgba(167,139,250,0.12)', border: 'rgba(167,139,250,0.3)' },
};
const DEFAULT_META = { color: '#60a5fa', bg: 'rgba(96,165,250,0.1)', border: 'rgba(96,165,250,0.25)' };

const ResultBadge = ({ result }) => {
    const meta = RESULT_META[result] || DEFAULT_META;
    return (
        <span className="badge" style={{ backgroundColor: meta.bg, color: meta.color, border: `1px solid ${meta.border}` }}>
            {result}
        </span>
    );
};

const formatDuration = (startDate, endDate) => {
    if (!startDate || !endDate) return '—';
    try {
        const ms = new Date(endDate) - new Date(startDate);
        if (ms < 0) return '—';
        const h = Math.floor(ms / 3600000);
        const m = Math.floor((ms % 3600000) / 60000);
        const s = Math.floor((ms % 60000) / 1000);
        return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
    } catch { return '—'; }
};

export default function TestQueryPage() {
    const { isOnline } = useConnection();
    const [loading, setLoading] = React.useState(false);
    const [testResults, setTestResults] = React.useState([]);
    const [availableTests, setAvailableTests] = React.useState([]);
    const [availablePrograms, setAvailablePrograms] = React.useState([]);
    const [availableDuts, setAvailableDuts] = React.useState([]);
    const [selectedTests, setSelectedTests] = React.useState([]);
    const [selectedPrograms, setSelectedPrograms] = React.useState([]);
    const [selectedDuts, setSelectedDuts] = React.useState([]);
    const [selectedResults, setSelectedResults] = React.useState([]);
    const [startDate, setStartDate] = React.useState(null);
    const [endDate, setEndDate] = React.useState(null);

    const getAvailableTests = React.useCallback(() => {
        if (!isOnline) return;
        axios.get("/get_available_tests").then(r => setAvailableTests(r.data)).catch(() => {});
    }, [isOnline]);

    const getAvailablePrograms = React.useCallback(() => {
        if (!isOnline) return;
        axios.get("/get_available_programs").then(r => setAvailablePrograms(r.data)).catch(() => {});
    }, [isOnline]);

    const getAvailableDuts = React.useCallback(() => {
        if (!isOnline) return;
        axios.get("/get_available_duts").then(r => setAvailableDuts(r.data)).catch(() => {});
    }, [isOnline]);

    const queryTestResults = React.useCallback(() => {
        if (!isOnline || selectedTests.length === 0) return;
        setLoading(true);
        const params = {
            test_names: selectedTests.join(',')  || undefined,
            programs:   selectedPrograms.join(',') || undefined,
            duts:       selectedDuts.join(',')    || undefined,
            results:    selectedResults.join(',') || undefined,
            start_date: startDate ? startDate.toISOString().split('T')[0] : undefined,
            end_date:   endDate   ? endDate.toISOString().split('T')[0]   : undefined,
        };
        Object.keys(params).forEach(k => params[k] === undefined && delete params[k]);
        axios.get("/query_test_results", { params })
            .then(r => { setTestResults(r.data); setLoading(false); })
            .catch(() => setLoading(false));
    }, [selectedTests, selectedPrograms, selectedDuts, selectedResults, startDate, endDate, isOnline]);

    const clearFilters = () => {
        setSelectedTests([]); setSelectedPrograms([]); setSelectedDuts([]);
        setSelectedResults([]); setStartDate(null); setEndDate(null); setTestResults([]);
    };

    React.useEffect(() => {
        if (isOnline) { getAvailableTests(); getAvailablePrograms(); getAvailableDuts(); }
    }, [isOnline, getAvailableTests, getAvailablePrograms, getAvailableDuts]);

    React.useEffect(() => { setTestResults([]); },
        [selectedTests, selectedPrograms, selectedDuts, selectedResults, startDate, endDate]);

    const MultiSelect = ({ label, value, onChange, options }) => (
        <FormControl fullWidth size="small">
            <InputLabel>{label}</InputLabel>
            <Select
                multiple
                value={value}
                onChange={(e) => onChange(e.target.value)}
                input={<OutlinedInput label={label} />}
                renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {selected.map(v => (
                            <Chip key={v} label={v} size="small"
                                sx={{ backgroundColor: 'rgba(99,102,241,0.15)', color: '#818cf8',
                                      border: '1px solid rgba(99,102,241,0.3)', borderRadius: '4px',
                                      fontSize: '0.7rem', fontWeight: 600 }} />
                        ))}
                    </Box>
                )}
            >
                {options.map(o => <MenuItem key={o} value={o}>{o}</MenuItem>)}
            </Select>
        </FormControl>
    );

    return (
        <main className="animate-fade-in p-6">
            <Backdrop open={loading} sx={{ color: '#fff', zIndex: 9999, backdropFilter: 'blur(4px)', backgroundColor: 'rgba(13,17,23,0.7)' }}>
                <CircularProgress sx={{ color: '#6366f1' }} />
            </Backdrop>

            {/* Header */}
            <div className="mb-6">
                <h1 className="text-2xl font-bold" style={{ color: '#e2e8f0' }}>Tests</h1>
                <p className="text-sm mt-0.5" style={{ color: '#64748b' }}>Compare results across runs</p>
            </div>

            {/* Filters */}
            <div className="card mb-6">
                <h2 className="text-sm font-semibold mb-4" style={{ color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                    Filters
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <MultiSelect label="Test Names"         value={selectedTests}    onChange={setSelectedTests}    options={availableTests}    />
                    <MultiSelect label="Programs"           value={selectedPrograms} onChange={setSelectedPrograms} options={availablePrograms} />
                    <MultiSelect label="Devices Under Test" value={selectedDuts}     onChange={setSelectedDuts}     options={availableDuts}     />
                    <MultiSelect
                        label="Results" value={selectedResults} onChange={setSelectedResults}
                        options={['PASS','FAIL','ERROR','SKIPPED','ABORTED']}
                    />
                    <TextField
                        label="Start Date" type="date" size="small" fullWidth
                        value={startDate ? startDate.toISOString().split('T')[0] : ''}
                        onChange={(e) => setStartDate(e.target.value ? new Date(e.target.value) : null)}
                        InputLabelProps={{ shrink: true }}
                    />
                    <TextField
                        label="End Date" type="date" size="small" fullWidth
                        value={endDate ? endDate.toISOString().split('T')[0] : ''}
                        onChange={(e) => setEndDate(e.target.value ? new Date(e.target.value) : null)}
                        InputLabelProps={{ shrink: true }}
                    />
                </div>
                <div className="flex justify-center gap-3">
                    <button
                        onClick={queryTestResults}
                        disabled={loading || selectedTests.length === 0}
                        className="px-6 py-2 rounded-lg text-sm font-semibold transition-all disabled:opacity-40"
                        style={{ background: 'linear-gradient(135deg,#6366f1,#4338ca)', color: '#fff' }}
                    >
                        {loading ? 'Querying…' : 'Query Results'}
                    </button>
                    <button
                        onClick={clearFilters}
                        disabled={loading}
                        className="px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-40"
                        style={{ backgroundColor: 'rgba(255,255,255,0.05)', color: '#94a3b8', border: '1px solid #2d3748' }}
                    >
                        Clear
                    </button>
                </div>
            </div>

            {/* Histograms */}
            {testResults.length > 0 && selectedTests.length > 0 && (() => {
                const byTest = testResults.reduce((acc, r) => {
                    const n = r.Name;
                    if (!acc[n]) acc[n] = [];
                    acc[n].push(r);
                    return acc;
                }, {});
                return Object.entries(byTest).map(([testName, results]) => {
                    const type = results[0]?.ResultType?.toLowerCase();
                    if (['numeric','bool','string','passfail'].includes(type)) {
                        return <TestHistogram key={testName} testResults={results} testType={type} testName={testName} />;
                    }
                    return null;
                }).filter(Boolean);
            })()}

            {/* Results table */}
            {testResults.length > 0 && (
                <div className="card">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-sm font-semibold" style={{ color: '#e2e8f0' }}>
                            {selectedTests.length > 0 ? selectedTests.join(', ') : 'All Tests'}
                        </h2>
                        <span className="text-xs font-mono" style={{ color: '#64748b' }}>
                            {testResults.length} result{testResults.length !== 1 ? 's' : ''}
                        </span>
                    </div>
                    <TableContainer component={Paper} sx={{ borderRadius: '8px', border: '1px solid #2d3748' }}>
                        <Table stickyHeader size="small">
                            <TableHead>
                                <TableRow>
                                    <TableCell sx={{ width: 60 }}>Run</TableCell>
                                    <TableCell>Program</TableCell>
                                    <TableCell>DUT</TableCell>
                                    <TableCell>Suite</TableCell>
                                    <TableCell>Test Name</TableCell>
                                    <TableCell align="center" sx={{ width: 96 }}>Result</TableCell>
                                    <TableCell align="center" sx={{ width: 120 }}>Value</TableCell>
                                    <TableCell>Unit</TableCell>
                                    <TableCell>Time</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {testResults.map((r, i) => {
                                    const hasPlot = r.PlotData?.points?.length > 0;
                                    return (
                                        <React.Fragment key={i}>
                                            <TableRow sx={{ '&:hover': { backgroundColor: 'rgba(99,102,241,0.05)' }, '& td': { borderBottom: '1px solid rgba(45,55,72,0.5)' } }}>
                                                <TableCell sx={{ fontFamily: 'monospace', fontWeight: 700, color: '#818cf8', fontSize: '0.8rem' }}>
                                                    #{r.run_id || '—'}
                                                </TableCell>
                                                <TableCell sx={{ fontSize: '0.8rem', color: '#94a3b8' }}>{r.Program || '—'}</TableCell>
                                                <TableCell sx={{ fontSize: '0.85rem', fontWeight: 500 }}>{r.DUT || '—'}</TableCell>
                                                <TableCell sx={{ fontSize: '0.8rem', color: '#94a3b8' }}>{r.Suite || '—'}</TableCell>
                                                <TableCell sx={{ fontWeight: 600 }}>{r.Name || '—'}</TableCell>
                                                <TableCell align="center"><ResultBadge result={r.Result} /></TableCell>
                                                <TableCell align="center" sx={{ fontFamily: 'monospace', fontSize: '0.85rem', fontWeight: 700, color: (RESULT_META[r.Result] || DEFAULT_META).color }}>
                                                    {r.Value || '—'}
                                                </TableCell>
                                                <TableCell sx={{ fontSize: '0.75rem', color: '#64748b' }}>{r.Unit || '—'}</TableCell>
                                                <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.75rem', color: '#64748b' }}>
                                                    {r.Time ? new Date(r.Time).toLocaleString() : '—'}
                                                </TableCell>
                                            </TableRow>
                                            {hasPlot && <ResultPlot show plotData={r.PlotData} />}
                                        </React.Fragment>
                                    );
                                })}
                            </TableBody>
                        </Table>
                    </TableContainer>
                </div>
            )}

            {/* Empty states */}
            {selectedTests.length === 0 && (
                <div className="flex flex-col items-center justify-center py-16 space-y-2">
                    <p className="text-sm" style={{ color: '#475569' }}>Select at least one test to query results</p>
                </div>
            )}
            {selectedTests.length > 0 && testResults.length === 0 && !loading && (
                <div className="flex flex-col items-center justify-center py-16 space-y-2">
                    <p className="text-sm" style={{ color: '#475569' }}>No results match the selected filters</p>
                </div>
            )}
        </main>
    );
}
