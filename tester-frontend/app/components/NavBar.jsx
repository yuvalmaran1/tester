'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useConnection } from '../contexts/ConnectionContext';

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

    return (
        <aside
            className="flex flex-col shrink-0 h-screen"
            style={{
                width: '220px',
                backgroundColor: '#0d1117',
                borderRight: '1px solid #2d3748',
            }}
        >
            {/* Logo */}
            <div className="flex items-center gap-3 px-5 py-5" style={{ borderBottom: '1px solid #2d3748' }}>
                <div
                    className="flex items-center justify-center w-8 h-8 rounded-lg shrink-0"
                    style={{ background: 'linear-gradient(135deg, #6366f1, #4338ca)' }}
                >
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                    </svg>
                </div>
                <span className="font-semibold text-sm tracking-tight" style={{ color: '#e2e8f0' }}>
                    HiL Framework
                </span>
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
