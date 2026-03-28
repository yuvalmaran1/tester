'use client';
import * as React from 'react';
import Image from 'next/image';
import { socket } from '../socket';

export default function LoginDialog({ show }) {
    const [username, setUsername] = React.useState('');
    const [password, setPassword] = React.useState('');
    const [error, setError] = React.useState('');
    const [loading, setLoading] = React.useState(false);

    React.useEffect(() => {
        const onResult = (data) => {
            setLoading(false);
            if (data?.success) {
                setError('');
                setUsername('');
                setPassword('');
            } else {
                setError(data?.error || 'Login failed');
            }
        };
        socket.on('login_result', onResult);
        return () => socket.off('login_result', onResult);
    }, []);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!username || !password) return;
        setLoading(true);
        setError('');
        socket.emit('login', { username, password });
    };

    if (!show) return null;

    return (
        <div style={{
            position: 'fixed', inset: 0, zIndex: 9999,
            background: 'rgba(0,0,0,0.85)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
            <div style={{
                background: '#161b22', border: '1px solid #2d3748',
                borderRadius: '12px', padding: '2rem', width: '340px',
                boxShadow: '0 20px 60px rgba(0,0,0,0.6)',
            }}>
                {/* Logo + title */}
                <div className="flex items-center gap-3 mb-6">
                    <Image src="/icon.svg" alt="logo" width={36} height={36} />
                    <div>
                        <div style={{ color: '#e2e8f0', fontWeight: 700, fontSize: '1rem' }}>HiL Framework</div>
                        <div style={{ color: '#6366f1', fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.07em' }}>
                            Operator Login
                        </div>
                    </div>
                </div>

                <form onSubmit={handleSubmit}>
                    <div className="mb-4">
                        <label style={{ color: '#8b9eb0', fontSize: '0.8rem', display: 'block', marginBottom: 6 }}>
                            Username
                        </label>
                        <input
                            type="text"
                            value={username}
                            onChange={e => setUsername(e.target.value)}
                            autoFocus
                            style={{
                                width: '100%', padding: '0.5rem 0.75rem',
                                background: '#0d1117', border: '1px solid #2d3748',
                                borderRadius: 6, color: '#e2e8f0', fontSize: '0.9rem',
                                outline: 'none', boxSizing: 'border-box',
                            }}
                        />
                    </div>
                    <div className="mb-5">
                        <label style={{ color: '#8b9eb0', fontSize: '0.8rem', display: 'block', marginBottom: 6 }}>
                            Password
                        </label>
                        <input
                            type="password"
                            value={password}
                            onChange={e => setPassword(e.target.value)}
                            style={{
                                width: '100%', padding: '0.5rem 0.75rem',
                                background: '#0d1117', border: '1px solid #2d3748',
                                borderRadius: 6, color: '#e2e8f0', fontSize: '0.9rem',
                                outline: 'none', boxSizing: 'border-box',
                            }}
                        />
                    </div>

                    {error && (
                        <div style={{
                            color: '#f87171', fontSize: '0.8rem', marginBottom: '0.75rem',
                            padding: '0.5rem 0.75rem', background: 'rgba(239,68,68,0.1)',
                            borderRadius: 6, border: '1px solid rgba(239,68,68,0.3)',
                        }}>
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        style={{
                            width: '100%', padding: '0.6rem',
                            background: loading ? '#4a4a6a' : '#6366f1',
                            color: '#fff', border: 'none', borderRadius: 6,
                            fontSize: '0.9rem', fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer',
                            transition: 'background 0.15s',
                        }}
                    >
                        {loading ? 'Signing in…' : 'Sign In'}
                    </button>
                </form>
            </div>
        </div>
    );
}
