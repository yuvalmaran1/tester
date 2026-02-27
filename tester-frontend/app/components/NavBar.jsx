'use client';
import { Box, Grid, Typography } from '@mui/material';
// import Image from 'next/image'; // Removed for static file serving
import Link from 'next/link';
import { useConnection } from '../contexts/ConnectionContext';

export default function Navbar() {
    const { connected, connecting, isOnline } = useConnection();

    return (
        <nav className="bg-white/90 backdrop-blur-md shadow-xl border-b border-gray-200/50 sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-6 py-4">
                <Grid container spacing={3} alignItems="center" justifyContent="space-between">
                    <Grid item xs={12} md={4}>
                        <Box className="flex items-center space-x-4">
                            <div className="w-12 h-12 flex items-center justify-center">
                                <img
                                    src="/tester.png"
                                    alt="Tester Logo"
                                    width={40}
                                    height={40}
                                    className="object-contain"
                                />
                            </div>
                            <Typography
                                variant="h5"
                                className="font-bold text-primary-600"
                                sx={{
                                    fontWeight: 700,
                                    fontSize: '1.5rem',
                                    letterSpacing: '-0.025em'
                                }}
                            >
                                HiL Test Framework
                            </Typography>
                        </Box>
                    </Grid>

                    <Grid item xs={12} md={4}>
                        <Box className="flex justify-center space-x-8">
                            <Link
                                href="/"
                                className={`font-semibold transition-all duration-200 relative group px-4 py-2 rounded-lg ${isOnline
                                    ? 'text-gray-700 hover:text-primary-600 hover:bg-primary-50'
                                    : 'text-gray-400 cursor-not-allowed'
                                    }`}
                            >
                                Dashboard
                                {isOnline && (
                                    <span className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-0 h-0.5 bg-gradient-to-r from-primary-500 to-accent-500 transition-all duration-200 group-hover:w-full"></span>
                                )}
                            </Link>
                            <Link
                                href="/results"
                                className={`font-semibold transition-all duration-200 relative group px-4 py-2 rounded-lg ${isOnline
                                    ? 'text-gray-700 hover:text-primary-600 hover:bg-primary-50'
                                    : 'text-gray-400 cursor-not-allowed'
                                    }`}
                            >
                                Runs
                                {isOnline && (
                                    <span className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-0 h-0.5 bg-gradient-to-r from-primary-500 to-accent-500 transition-all duration-200 group-hover:w-full"></span>
                                )}
                            </Link>
                            <Link
                                href="/test-query"
                                className={`font-semibold transition-all duration-200 relative group px-4 py-2 rounded-lg ${isOnline
                                    ? 'text-gray-700 hover:text-primary-600 hover:bg-primary-50'
                                    : 'text-gray-400 cursor-not-allowed'
                                    }`}
                            >
                                Tests
                                {isOnline && (
                                    <span className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-0 h-0.5 bg-gradient-to-r from-primary-500 to-accent-500 transition-all duration-200 group-hover:w-full"></span>
                                )}
                            </Link>
                        </Box>
                    </Grid>

                    <Grid item xs={12} md={4}>
                        <Box className="flex justify-end">
                            {connecting ? (
                                <div className="flex items-center space-x-3 bg-gradient-to-r from-warning-500 to-warning-600 text-white px-4 py-2 rounded-full shadow-lg">
                                    <div className="w-3 h-3 bg-white rounded-full animate-spin"></div>
                                    <span className="font-semibold text-sm">Connecting...</span>
                                </div>
                            ) : connected ? (
                                <div className="flex items-center space-x-3 bg-gradient-to-r from-success-500 to-success-600 text-white px-4 py-2 rounded-full shadow-lg">
                                    <div className="w-3 h-3 bg-white rounded-full animate-pulse"></div>
                                    <span className="font-semibold text-sm">System Online</span>
                                </div>
                            ) : (
                                <div className="flex items-center space-x-3 bg-gradient-to-r from-danger-500 to-danger-600 text-white px-4 py-2 rounded-full shadow-lg">
                                    <div className="w-3 h-3 bg-white rounded-full"></div>
                                    <span className="font-semibold text-sm">System Offline</span>
                                </div>
                            )}
                        </Box>
                    </Grid>
                </Grid>
            </div>
        </nav>
    );
}
