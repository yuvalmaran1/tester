'use client';
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useConnection } from '../contexts/ConnectionContext';
import { socket } from '../socket';

const NAV = [
    {
        href: '/',
        label: 'Dashboard',
        icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
        ),
    },
    {
        href: '/results',
        label: 'Runs',
        icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
        ),
    },
    {
        href: '/test-query',
        label: 'Tests',
        icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
        ),
    },
];

export default function Sidebar() {
    const pathname = usePathname();
    const { connected, connecting } = useConnection();
    const [testerName, setTesterName] = useState('');
    const [operator, setOperator] = useState(null);

    useEffect(() => {
        const onTester = (data) => {
            if (data?.name) setTesterName(data.name);
            setOperator(data?.operator ?? null);
        };
        const onState = (data) => {
            if (data?.tester?.name) setTesterName(data.tester.name);
            setOperator(data?.tester?.operator ?? null);
        };
        socket.on('tester', onTester);
        socket.on('state',  onState);
        return () => {
            socket.off('tester', onTester);
            socket.off('state',  onState);
        };
    }, []);

    const handleLogout = () => socket.emit('logout');

    return (
        <aside
            className="flex flex-col shrink-0 h-screen"
            style={{
                width: '220px',
                backgroundColor: '#0d1117',
                borderRight: '1px solid #2d3748',
            }}
        >
            {/* Brand */}
            <div style={{ borderBottom: '1px solid #2d3748', padding: '1rem 1.25rem' }}>
                <div className="flex items-center gap-3">
                    <img src="/icon.svg" alt="logo" style={{ width: '34px', height: '34px', flexShrink: 0 }} />
                    <div style={{ minWidth: 0 }}>
                        <div style={{
                            color: '#e2e8f0', fontWeight: 700, fontSize: '0.875rem',
                            lineHeight: 1.25, overflow: 'hidden',
                            textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                        }}>
                            {testerName || 'HiL Framework'}
                        </div>
                        <div style={{
                            color: '#6366f1', fontSize: '0.6875rem', fontWeight: 600,
                            textTransform: 'uppercase', letterSpacing: '0.07em',
                            marginTop: '2px',
                        }}>
                            Test Framework
                        </div>
                    </div>
                </div>
            </div>

            {/* Nav links */}
            <nav className="flex-1 px-3 py-4 space-y-1">
                {NAV.map(({ href, label, icon }) => {
                    const active = pathname === href;
                    return (
                        <Link
                            key={href}
                            href={href}
                            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-150"
                            style={{
                                color:           active ? '#e2e8f0' : '#8b9eb0',
                                backgroundColor: active ? 'rgba(99,102,241,0.15)' : 'transparent',
                                borderLeft:      active ? '2px solid #6366f1' : '2px solid transparent',
                            }}
                        >
                            <span style={{ color: active ? '#818cf8' : '#64748b' }}>{icon}</span>
                            {label}
                        </Link>
                    );
                })}
            </nav>

            {/* Operator info */}
            {operator && (
                <div className="px-4 py-3" style={{ borderTop: '1px solid #2d3748' }}>
                    <div style={{ color: '#8b9eb0', fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 4 }}>
                        Operator
                    </div>
                    <div className="flex items-center justify-between">
                        <div>
                            <div style={{ color: '#e2e8f0', fontSize: '0.8rem', fontWeight: 600 }}>
                                {operator.display_name || operator.username}
                            </div>
                            {operator.role === 'admin' && (
                                <Link href="/admin" style={{ color: '#6366f1', fontSize: '0.65rem', fontWeight: 600 }}>
                                    Admin Panel
                                </Link>
                            )}
                        </div>
                        <button
                            onClick={handleLogout}
                            title="Logout"
                            style={{
                                background: 'none', border: 'none', cursor: 'pointer',
                                color: '#64748b', padding: 4, borderRadius: 4,
                            }}
                        >
                            <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                    d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                            </svg>
                        </button>
                    </div>
                </div>
            )}

            {/* Connection status */}
            <div className="px-4 py-4" style={{ borderTop: '1px solid #2d3748' }}>
                <div className="flex items-center gap-2.5">
                    <span
                        className="w-2 h-2 rounded-full shrink-0"
                        style={{
                            backgroundColor: connecting
                                ? '#f59e0b'
                                : connected
                                    ? '#10b981'
                                    : '#ef4444',
                            boxShadow: connecting
                                ? '0 0 6px #f59e0b'
                                : connected
                                    ? '0 0 6px #10b981'
                                    : '0 0 6px #ef4444',
                        }}
                    />
                    <span className="text-xs font-medium" style={{ color: '#8b9eb0' }}>
                        {connecting ? 'Connecting…' : connected ? 'System Online' : 'Disconnected'}
                    </span>
                </div>
            </div>
        </aside>
    );
}
