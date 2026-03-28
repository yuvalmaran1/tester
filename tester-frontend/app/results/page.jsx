"use client";
import { Backdrop, CircularProgress, MenuItem, Paper, Select, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from "@mui/material";
import axios from 'axios';
import _ from 'lodash';
import * as React from "react";
import TestRunRow from '../components/TestRunRow';
import { useConnection } from '../contexts/ConnectionContext';

const RESULTS = ['', 'PASS', 'FAIL', 'ERROR', 'SKIPPED', 'ABORTED'];

const FILTER_INPUT_SX = {
    background: '#0d1117',
    border: '1px solid #2d3748',
    borderRadius: 6,
    color: '#e2e8f0',
    fontSize: '0.75rem',
    padding: '0.3rem 0.5rem',
    outline: 'none',
    width: '100%',
};

export default function ResultsPage() {
    const { isOnline, connecting } = useConnection();
    const [runs, setRuns] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [filters, setFilters] = React.useState({ dut: '', program: '', serial_number: '', operator: '', result: '' });

    const getState = React.useCallback(() => {
        if (!isOnline) { setLoading(false); return; }
        setLoading(true);
        axios.get("/get_runs")
            .then((res) => {
                const sorted = [...res.data].sort((a, b) =>
                    new Date(b.start_date) - new Date(a.start_date)
                );
                setRuns(sorted);
                setLoading(false);
            })
            .catch(() => setLoading(false));
    }, [isOnline]);

    React.useEffect(() => { if (isOnline) getState(); }, [isOnline, getState]);

    const setFilter = (key, val) => setFilters(f => ({ ...f, [key]: val }));

    const filtered = runs.filter(r => {
        const match = (field, key) => {
            const fv = filters[key];
            if (!fv) return true;
            return String(_.get(r, field, '') || '').toLowerCase().includes(fv.toLowerCase());
        };
        if (filters.result && r.result !== filters.result) return false;
        return match('dut', 'dut') && match('program', 'program') &&
               match('serial_number', 'serial_number') && match('operator', 'operator');
    });

    const hasFilters = Object.values(filters).some(v => v !== '');

    return (
        <main className="animate-fade-in p-6">
            <Backdrop open={!isOnline} sx={{ color: '#fff', zIndex: 9999, backdropFilter: 'blur(4px)', backgroundColor: 'rgba(13,17,23,0.85)' }}>
                <div className="text-center space-y-3">
                    <CircularProgress color="inherit" size={40} />
                    <p className="text-sm font-medium">{connecting ? 'Connecting…' : 'Backend Disconnected'}</p>
                </div>
            </Backdrop>

            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div>
                    <h1 className="text-2xl font-bold" style={{ color: '#e2e8f0' }}>Runs</h1>
                    <p className="text-sm mt-0.5" style={{ color: '#64748b' }}>
                        {hasFilters ? `${filtered.length} of ${runs.length}` : runs.length} run{runs.length !== 1 ? 's' : ''}
                        {hasFilters && ' (filtered)'}
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    {hasFilters && (
                        <button
                            onClick={() => setFilters({ dut: '', program: '', serial_number: '', operator: '', result: '' })}
                            className="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors"
                            style={{ backgroundColor: 'rgba(239,68,68,0.1)', color: '#f87171', border: '1px solid rgba(239,68,68,0.25)' }}
                        >
                            Clear filters
                        </button>
                    )}
                    <button
                        onClick={getState}
                        disabled={!isOnline}
                        className="px-3 py-1.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-40"
                        style={{ backgroundColor: 'rgba(99,102,241,0.12)', color: '#818cf8', border: '1px solid rgba(99,102,241,0.25)' }}
                    >
                        Refresh
                    </button>
                </div>
            </div>

            {loading ? (
                <div className="flex justify-center items-center py-24">
                    <CircularProgress size={32} sx={{ color: '#6366f1' }} />
                </div>
            ) : runs.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-24 space-y-3">
                    <svg className="w-12 h-12" style={{ color: '#334155' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1}
                            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <p className="text-sm font-medium" style={{ color: '#475569' }}>No runs yet</p>
                </div>
            ) : (
                <TableContainer component={Paper} sx={{ borderRadius: '10px', border: '1px solid #2d3748' }}>
                    <Table stickyHeader size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell align="center" sx={{ width: 56 }}>—</TableCell>
                                <TableCell align="center" sx={{ width: 72 }}>ID</TableCell>
                                <TableCell>Device</TableCell>
                                <TableCell>Program</TableCell>
                                <TableCell>Serial Number</TableCell>
                                <TableCell>Operator</TableCell>
                                <TableCell align="center">Start Time</TableCell>
                                <TableCell align="center">Duration</TableCell>
                                <TableCell align="center" sx={{ width: 96 }}>Result</TableCell>
                            </TableRow>
                            {/* Filter row */}
                            <TableRow sx={{ '& th': { paddingTop: '4px', paddingBottom: '4px', backgroundColor: '#0d1117' } }}>
                                <TableCell /><TableCell />
                                <TableCell>
                                    <input style={FILTER_INPUT_SX} placeholder="Filter…" value={filters.dut}
                                        onChange={e => setFilter('dut', e.target.value)} />
                                </TableCell>
                                <TableCell>
                                    <input style={FILTER_INPUT_SX} placeholder="Filter…" value={filters.program}
                                        onChange={e => setFilter('program', e.target.value)} />
                                </TableCell>
                                <TableCell>
                                    <input style={FILTER_INPUT_SX} placeholder="Filter…" value={filters.serial_number}
                                        onChange={e => setFilter('serial_number', e.target.value)} />
                                </TableCell>
                                <TableCell>
                                    <input style={FILTER_INPUT_SX} placeholder="Filter…" value={filters.operator}
                                        onChange={e => setFilter('operator', e.target.value)} />
                                </TableCell>
                                <TableCell /><TableCell />
                                <TableCell align="center">
                                    <Select
                                        value={filters.result}
                                        onChange={e => setFilter('result', e.target.value)}
                                        displayEmpty
                                        size="small"
                                        sx={{
                                            fontSize: '0.7rem', color: filters.result ? '#e2e8f0' : '#64748b',
                                            '& .MuiOutlinedInput-notchedOutline': { borderColor: '#2d3748' },
                                            '& .MuiSvgIcon-root': { color: '#64748b' },
                                            minWidth: 80,
                                        }}
                                    >
                                        <MenuItem value=""><em style={{ color: '#64748b', fontSize: '0.7rem' }}>All</em></MenuItem>
                                        {RESULTS.slice(1).map(r => (
                                            <MenuItem key={r} value={r} sx={{ fontSize: '0.75rem' }}>{r}</MenuItem>
                                        ))}
                                    </Select>
                                </TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {filtered.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={9} align="center" sx={{ py: 6, color: '#475569', fontSize: '0.875rem' }}>
                                        No runs match the current filters
                                    </TableCell>
                                </TableRow>
                            ) : (
                                filtered.map((row, i) => <TestRunRow key={i} row={row} />)
                            )}
                        </TableBody>
                    </Table>
                </TableContainer>
            )}
        </main>
    );
}
