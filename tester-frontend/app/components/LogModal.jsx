'use client';
import CloseIcon from '@mui/icons-material/Close';
import { IconButton, Modal } from '@mui/material';
import * as React from 'react';

export default function LogModal({ open, handleClose, log }) {
    const endRef = React.useRef(null);

    React.useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }, [log]);

    return (
        <Modal
            open={open}
            onClose={handleClose}
            sx={{ backdropFilter: 'blur(4px)', backgroundColor: 'rgba(0,0,0,0.6)' }}
        >
            <div style={{
                position: 'absolute', top: '50%', left: '50%',
                transform: 'translate(-50%,-50%)',
                width: '90%', maxWidth: 960, height: '80vh',
                backgroundColor: 'var(--bg-base)',
                border: '1px solid var(--border)',
                borderRadius: 12,
                display: 'flex', flexDirection: 'column',
                outline: 'none',
            }}>
                {/* Header */}
                <div className="flex items-center justify-between px-5 py-3"
                    style={{ borderBottom: '1px solid var(--border)' }}>
                    <span className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>
                        Framework Log
                    </span>
                    <IconButton onClick={handleClose} size="small"
                        sx={{ color: 'var(--text-muted)', '&:hover': { color: '#ef4444', backgroundColor: 'rgba(239,68,68,0.08)' } }}>
                        <CloseIcon fontSize="small" />
                    </IconButton>
                </div>

                {/* Log content */}
                <div className="flex-1 overflow-y-auto p-4" style={{ backgroundColor: 'var(--bg-base)' }}>
                    <pre style={{
                        margin: 0,
                        fontFamily: "'JetBrains Mono', 'Fira Code', 'Monaco', monospace",
                        fontSize: '13px',
                        lineHeight: '1.6',
                        color: 'var(--text-secondary)',
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                    }}>
                        {log}
                        <div ref={endRef} />
                    </pre>
                </div>
            </div>
        </Modal>
    );
}
