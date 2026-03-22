"use client";
import { Backdrop, CircularProgress, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from "@mui/material";
import axios from 'axios';
import * as React from "react";
import TestRunRow from '../components/TestRunRow';
import { useConnection } from '../contexts/ConnectionContext';

export default function ResultsPage() {
    const { isOnline, connecting } = useConnection();
    const [runs, setRuns] = React.useState([]);
    const [loading, setLoading] = React.useState(true);

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

    return (
        <main className="animate-fade-in p-6">
            <Backdrop open={!isOnline} sx={{ color: '#fff', zIndex: 9999, backdropFilter: 'blur(4px)', backgroundColor: 'rgba(13,17,23,0.85)' }}>
                <div className="text-center space-y-3">
                    <CircularProgress color="inherit" size={40} />
                    <p className="text-sm font-medium">{connecting ? 'Connecting…' : 'Backend Disconnected'}</p>
                </div>
            </Backdrop>

            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-bold" style={{ color: '#e2e8f0' }}>Runs</h1>
                    <p className="text-sm mt-0.5" style={{ color: '#64748b' }}>Historical test runs</p>
                </div>
                <div className="flex items-center gap-3">
                    <span className="text-sm font-mono" style={{ color: '#64748b' }}>
                        {runs.length} run{runs.length !== 1 ? 's' : ''}
                    </span>
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
                                <TableCell align="center">Start Time</TableCell>
                                <TableCell align="center">Duration</TableCell>
                                <TableCell align="center" sx={{ width: 96 }}>Result</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {runs.map((row, i) => <TestRunRow key={i} row={row} />)}
                        </TableBody>
                    </Table>
                </TableContainer>
            )}
        </main>
    );
}
