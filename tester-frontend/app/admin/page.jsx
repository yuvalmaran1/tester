'use client';
import * as React from 'react';
import { socket } from '../socket';

const FIELD = ({ label, children }) => (
    <div style={{ marginBottom: '0.75rem' }}>
        <label style={{ color: '#8b9eb0', fontSize: '0.75rem', display: 'block', marginBottom: 4 }}>{label}</label>
        {children}
    </div>
);

const INPUT = ({ value, onChange, type = 'text', placeholder = '' }) => (
    <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        style={{
            width: '100%', padding: '0.45rem 0.65rem',
            background: '#0d1117', border: '1px solid #2d3748',
            borderRadius: 6, color: '#e2e8f0', fontSize: '0.85rem',
            outline: 'none', boxSizing: 'border-box',
        }}
    />
);

const SELECT = ({ value, onChange, children }) => (
    <select
        value={value}
        onChange={e => onChange(e.target.value)}
        style={{
            width: '100%', padding: '0.45rem 0.65rem',
            background: '#0d1117', border: '1px solid #2d3748',
            borderRadius: 6, color: '#e2e8f0', fontSize: '0.85rem',
            outline: 'none', boxSizing: 'border-box',
        }}
    >
        {children}
    </select>
);

const BTN = ({ onClick, children, variant = 'primary', small = false, disabled = false }) => {
    const bg = variant === 'primary' ? '#6366f1' : variant === 'danger' ? '#ef4444' : '#2d3748';
    return (
        <button
            onClick={onClick}
            disabled={disabled}
            style={{
                padding: small ? '0.3rem 0.65rem' : '0.5rem 1rem',
                background: disabled ? '#2d3748' : bg,
                color: disabled ? '#64748b' : '#fff',
                border: 'none', borderRadius: 6,
                fontSize: small ? '0.75rem' : '0.85rem',
                fontWeight: 600, cursor: disabled ? 'not-allowed' : 'pointer',
                transition: 'opacity 0.15s',
            }}
        >
            {children}
        </button>
    );
};

function AddOperatorForm({ onDone }) {
    const [username, setUsername] = React.useState('');
    const [displayName, setDisplayName] = React.useState('');
    const [password, setPassword] = React.useState('');
    const [role, setRole] = React.useState('operator');

    const handleAdd = () => {
        if (!username || !password) return;
        socket.emit('add_operator', { username, display_name: displayName || username, password, role });
        setUsername(''); setDisplayName(''); setPassword(''); setRole('operator');
        if (onDone) onDone();
    };

    return (
        <div style={{
            background: '#161b22', border: '1px solid #2d3748', borderRadius: 8,
            padding: '1rem', marginBottom: '1.5rem',
        }}>
            <div style={{ color: '#e2e8f0', fontWeight: 600, fontSize: '0.875rem', marginBottom: '0.75rem' }}>
                Add Operator
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                <FIELD label="Username *"><INPUT value={username} onChange={setUsername} /></FIELD>
                <FIELD label="Display Name"><INPUT value={displayName} onChange={setDisplayName} /></FIELD>
                <FIELD label="Password *"><INPUT type="password" value={password} onChange={setPassword} /></FIELD>
                <FIELD label="Role">
                    <SELECT value={role} onChange={setRole}>
                        <option value="operator">Operator</option>
                        <option value="admin">Admin</option>
                    </SELECT>
                </FIELD>
            </div>
            <div style={{ marginTop: '0.5rem' }}>
                <BTN onClick={handleAdd} disabled={!username || !password}>Add Operator</BTN>
            </div>
        </div>
    );
}

function OperatorRow({ op, currentId, onUpdate, onDelete, onChangePassword }) {
    const [editing, setEditing] = React.useState(false);
    const [displayName, setDisplayName] = React.useState(op.display_name);
    const [role, setRole] = React.useState(op.role);
    const [active, setActive] = React.useState(op.active);
    const [showPwd, setShowPwd] = React.useState(false);
    const [newPwd, setNewPwd] = React.useState('');

    const roleBadge = op.role === 'admin'
        ? { bg: 'rgba(99,102,241,0.15)', color: '#818cf8', text: 'Admin' }
        : { bg: 'rgba(16,185,129,0.1)', color: '#10b981', text: 'Operator' };
    const activeBadge = op.active
        ? { bg: 'rgba(16,185,129,0.1)', color: '#10b981', text: 'Active' }
        : { bg: 'rgba(100,116,139,0.15)', color: '#64748b', text: 'Inactive' };

    const Badge = ({ bg, color, text }) => (
        <span style={{
            background: bg, color, borderRadius: 4,
            padding: '2px 8px', fontSize: '0.7rem', fontWeight: 600,
        }}>{text}</span>
    );

    if (!editing) {
        return (
            <div style={{
                display: 'flex', alignItems: 'center', gap: '0.75rem',
                padding: '0.6rem 0.75rem', background: '#0d1117',
                borderRadius: 8, border: '1px solid #1e2a3a', marginBottom: '0.5rem',
            }}>
                <div style={{ flex: 1 }}>
                    <span style={{ color: '#e2e8f0', fontWeight: 600, fontSize: '0.875rem' }}>{op.display_name}</span>
                    <span style={{ color: '#64748b', fontSize: '0.75rem', marginLeft: 8 }}>@{op.username}</span>
                </div>
                <Badge {...roleBadge} />
                <Badge {...activeBadge} />
                <div style={{ display: 'flex', gap: '0.4rem' }}>
                    <BTN small onClick={() => setEditing(true)}>Edit</BTN>
                    <BTN small onClick={() => setShowPwd(!showPwd)} variant="secondary">Pwd</BTN>
                    {op.id !== currentId && (
                        <BTN small variant="danger" onClick={() => onDelete(op.id)}>Del</BTN>
                    )}
                </div>
                {showPwd && (
                    <div style={{ display: 'flex', gap: '0.4rem', marginLeft: '0.5rem' }}>
                        <input
                            type="password"
                            value={newPwd}
                            onChange={e => setNewPwd(e.target.value)}
                            placeholder="New password"
                            style={{
                                padding: '0.3rem 0.5rem', background: '#0d1117',
                                border: '1px solid #2d3748', borderRadius: 4,
                                color: '#e2e8f0', fontSize: '0.8rem', outline: 'none', width: 130,
                            }}
                        />
                        <BTN small onClick={() => { onChangePassword(op.id, newPwd); setNewPwd(''); setShowPwd(false); }}
                            disabled={!newPwd}>Set</BTN>
                    </div>
                )}
            </div>
        );
    }

    return (
        <div style={{
            padding: '0.75rem', background: '#0d1117', borderRadius: 8,
            border: '1px solid #6366f1', marginBottom: '0.5rem',
        }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <FIELD label="Display Name"><INPUT value={displayName} onChange={setDisplayName} /></FIELD>
                <FIELD label="Role">
                    <SELECT value={role} onChange={setRole}>
                        <option value="operator">Operator</option>
                        <option value="admin">Admin</option>
                    </SELECT>
                </FIELD>
                <FIELD label="Active">
                    <SELECT value={String(active)} onChange={v => setActive(v === 'true')}>
                        <option value="true">Active</option>
                        <option value="false">Inactive</option>
                    </SELECT>
                </FIELD>
            </div>
            <div style={{ display: 'flex', gap: '0.4rem' }}>
                <BTN small onClick={() => { onUpdate(op.id, displayName, role, active); setEditing(false); }}>Save</BTN>
                <BTN small variant="secondary" onClick={() => setEditing(false)}>Cancel</BTN>
            </div>
        </div>
    );
}

export default function AdminPage() {
    const [operators, setOperators] = React.useState([]);
    const [currentOp, setCurrentOp] = React.useState(null);
    const [isAdmin, setIsAdmin] = React.useState(false);

    React.useEffect(() => {
        const onState = (data) => {
            const op = data?.tester?.operator;
            setCurrentOp(op || null);
            setIsAdmin(op?.role === 'admin');
        };
        const onTester = (data) => {
            const op = data?.operator;
            setCurrentOp(op || null);
            setIsAdmin(op?.role === 'admin');
        };
        const onList = (data) => setOperators(data || []);
        socket.on('state', onState);
        socket.on('tester', onTester);
        socket.on('operator_list', onList);
        socket.emit('get_state');
        socket.emit('list_operators');
        return () => {
            socket.off('state', onState);
            socket.off('tester', onTester);
            socket.off('operator_list', onList);
        };
    }, []);

    const refresh = () => socket.emit('list_operators');

    const handleUpdate = (id, display_name, role, active) => {
        socket.emit('update_operator', { id, display_name, role, active });
    };
    const handleDelete = (id) => {
        socket.emit('delete_operator', { id });
    };
    const handleChangePassword = (id, password) => {
        socket.emit('update_operator_password', { id, password });
    };

    if (!isAdmin) {
        return (
            <div style={{ padding: '2rem', color: '#64748b', textAlign: 'center' }}>
                Admin access required.
            </div>
        );
    }

    return (
        <div style={{ padding: '1.5rem', maxWidth: 760, margin: '0 auto' }}>
            <div style={{ color: '#e2e8f0', fontWeight: 700, fontSize: '1.1rem', marginBottom: '1.25rem' }}>
                Operator Management
            </div>

            <AddOperatorForm onDone={refresh} />

            <div style={{ color: '#8b9eb0', fontSize: '0.75rem', marginBottom: '0.5rem' }}>
                {operators.length} operator{operators.length !== 1 ? 's' : ''}
            </div>
            {operators.map(op => (
                <OperatorRow
                    key={op.id}
                    op={op}
                    currentId={currentOp?.id}
                    onUpdate={handleUpdate}
                    onDelete={handleDelete}
                    onChangePassword={handleChangePassword}
                />
            ))}
        </div>
    );
}
