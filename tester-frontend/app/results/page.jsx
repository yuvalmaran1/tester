"use client";
import {
    Backdrop,
    Button,
    CircularProgress,
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow
} from "@mui/material";
import axios from 'axios';
import * as React from "react";
import TestRunRow from '../components/TestRunRow';
import { useConnection } from '../contexts/ConnectionContext';

export default function ResultsPage() {
    const { connected, connecting, isOnline } = useConnection();
    const [runs, setRuns] = React.useState([]);
    const [loading, setLoading] = React.useState(true);

    const getState = React.useCallback(() => {
        if (!isOnline) {
            setLoading(false);
            return;
        }

        setLoading(true);
        axios
            .get("/get_runs")
            .then((response) => {
                // Sort runs by start_date in descending order (newest first)
                const sortedRuns = response.data.sort((a, b) => {
                    const dateA = new Date(a.start_date);
                    const dateB = new Date(b.start_date);
                    return dateB - dateA; // Descending order (newest first)
                });
                setRuns(sortedRuns);
                setLoading(false);
            })
            .catch((error) => {
                console.error('Error fetching runs:', error);
                setLoading(false);
            });
    }, [isOnline]);

    React.useEffect(() => {
        if (isOnline) {
            getState();
        }
    }, [isOnline, getState]);

    return (
        <main className="animate-fade-in">
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
            {/* Header */}
            <div className="card mb-8">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-4xl font-bold text-primary-800 mb-2">
                            Runs
                        </h1>
                        <p className="text-gray-600 text-lg">
                            View and analyze historical test runs and their results
                        </p>
                    </div>
                    <div className="text-right">
                        <div className="text-sm text-gray-500 mb-1">Total Runs</div>
                        <div className="text-3xl font-bold text-primary-600">
                            {runs.length}
                        </div>
                    </div>
                </div>
            </div>

            {/* Results Table */}
            <div className="card">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-semibold text-primary-700">Test Runs</h2>
                    <Button
                        onClick={getState}
                        variant="outlined"
                        disabled={!isOnline}
                        sx={{
                            borderRadius: '12px',
                            borderColor: isOnline ? '#3b82f6' : '#d1d5db',
                            color: isOnline ? '#3b82f6' : '#9ca3af',
                            '&:hover': isOnline ? {
                                borderColor: '#2563eb',
                                backgroundColor: '#eff6ff'
                            } : {},
                            '&:disabled': {
                                borderColor: '#d1d5db',
                                color: '#9ca3af'
                            }
                        }}
                    >
                        Refresh
                    </Button>
                </div>

                {loading ? (
                    <div className="flex justify-center items-center py-12">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
                    </div>
                ) : runs.length === 0 ? (
                    <div className="text-center py-12">
                        <div className="text-gray-400 mb-4">
                            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                        </div>
                        <h3 className="text-lg font-medium text-gray-600 mb-2">No test runs found</h3>
                        <p className="text-gray-500">Run some tests to see results here</p>
                    </div>
                ) : (
                    <TableContainer
                        component={Paper}
                        sx={{
                            overflowX: "auto",
                            borderRadius: '12px',
                            border: '1px solid #e2e8f0'
                        }}
                    >
                        <Table
                            aria-label="test runs table"
                            stickyHeader
                            sx={{ backgroundColor: "white" }}
                        >
                            <TableHead>
                                <TableRow sx={{ backgroundColor: '#f8fafc' }}>
                                    <TableCell sx={{ width: "5%", fontWeight: 600, color: '#374151' }} align="center">
                                        Details
                                    </TableCell>
                                    <TableCell sx={{ width: "10%", fontWeight: 600, color: '#374151' }} align="center">
                                        Run ID
                                    </TableCell>
                                    <TableCell sx={{ width: "15%", fontWeight: 600, color: '#374151' }} align="left">
                                        Device
                                    </TableCell>
                                    <TableCell sx={{ width: "20%", fontWeight: 600, color: '#374151' }} align="left">
                                        Program
                                    </TableCell>
                                    <TableCell sx={{ width: "20%", fontWeight: 600, color: '#374151' }} align="center">
                                        Start Time
                                    </TableCell>
                                    <TableCell sx={{ width: "20%", fontWeight: 600, color: '#374151' }} align="center">
                                        Duration
                                    </TableCell>
                                    <TableCell sx={{ width: "10%", fontWeight: 600, color: '#374151' }} align="center">
                                        Result
                                    </TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {runs.map((row, index) => (
                                    <TestRunRow key={index} row={row} />
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                )}
            </div>
        </main>
    );
}
