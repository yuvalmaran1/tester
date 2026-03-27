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
                backgroundColor: '#0d1117',
                border: '1px solid #2d3748',
                borderRadius: 12,
                display: 'flex', flexDirection: 'column',
                outline: 'none',
            }}>
                {/* Header */}
                <div className="flex items-center justify-between px-5 py-3"
                    style={{ borderBottom: '1px solid #2d3748' }}>
                    <span className="font-semibold text-sm" style={{ color: '#e2e8f0' }}>
                        Framework Log
                    </span>
                    <IconButton onClick={handleClose} size="small"
                        sx={{ color: '#64748b', '&:hover': { color: '#ef4444', backgroundColor: 'rgba(239,68,68,0.08)' } }}>
                        <CloseIcon fontSize="small" />
                    </IconButton>
                </div>

                {/* Log content */}
                <div className="flex-1 overflow-y-auto p-4" style={{ backgroundColor: '#0d1117' }}>
                    <pre style={{
                        margin: 0,
                        fontFamily: "'JetBrains Mono', 'Fira Code', 'Monaco', monospace",
                        fontSize: '13px',
                        lineHeight: '1.6',
                        color: '#94a3b8',
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
