'use client';
import { TableCell, TableRow } from '@mui/material';
import _ from 'lodash';

const RESULT_META = {
    PASS:    { color: '#10b981', bg: 'rgba(16,185,129,0.12)',  border: 'rgba(16,185,129,0.3)'  },
    FAIL:    { color: '#ef4444', bg: 'rgba(239,68,68,0.12)',   border: 'rgba(239,68,68,0.3)'   },
    ERROR:   { color: '#f59e0b', bg: 'rgba(245,158,11,0.12)',  border: 'rgba(245,158,11,0.3)'  },
    SKIPPED: { color: '#64748b', bg: 'rgba(100,116,139,0.1)',  border: 'rgba(100,116,139,0.25)'},
    ABORTED: { color: '#a78bfa', bg: 'rgba(167,139,250,0.12)', border: 'rgba(167,139,250,0.3)' },
};
const DEFAULT_META = { color: '#60a5fa', bg: 'rgba(96,165,250,0.1)', border: 'rgba(96,165,250,0.25)' };

const formatDuration = (startDate, endDate) => {
    if (!startDate || !endDate) return '—';
    try {
        const ms = new Date(endDate) - new Date(startDate);
        if (ms < 0) return '—';
        const h = Math.floor(ms / 3600000);
        const m = Math.floor((ms % 3600000) / 60000);
        const s = Math.floor((ms % 60000) / 1000);
        return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
    } catch { return '—'; }
};

export default function TestRunRow({ row }) {
    const result = _.get(row, 'result', 'UNKNOWN');
    const meta   = RESULT_META[result] || DEFAULT_META;
    const runId  = _.get(row, 'run_id', '0');
    const sn     = _.get(row, 'serial_number', '') || '';
    const op     = _.get(row, 'operator', '') || '';

    return (
        <TableRow sx={{
            '&:hover': { backgroundColor: 'rgba(99,102,241,0.05)' },
            borderLeft: `2px solid ${meta.border}`,
            '& td': { borderBottom: '1px solid rgba(45,55,72,0.5)' },
        }}>
            {/* Download */}
            <TableCell align="center" sx={{ width: 56 }}>
                <a
                    href={`/generate_report/${runId}`}
                    className="inline-flex items-center justify-center w-7 h-7 rounded-md transition-colors"
                    style={{ color: '#10b981', border: '1px solid rgba(16,185,129,0.3)' }}
                    title="Download report"
                >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M5 20h14v-2H5zM19 9h-4V3H9v6H5l7 7z"/>
                        </svg>
                </a>
            </TableCell>

            {/* Run ID */}
            <TableCell align="center" sx={{ width: 72 }}>
                <a href={`/show_report/${runId}`}
                    style={{ color: '#818cf8', fontFamily: 'monospace', fontWeight: 700, fontSize: '0.8rem' }}>
                    #{runId}
                </a>
            </TableCell>

            {/* DUT */}
            <TableCell>
                <a href={`/show_report/${runId}`}
                    style={{ color: '#e2e8f0', fontWeight: 500, fontSize: '0.875rem' }}>
                    {_.get(row, 'dut', '')}
                </a>
            </TableCell>

            {/* Program */}
            <TableCell>
                <a href={`/show_report/${runId}`}
                    style={{ color: '#94a3b8', fontSize: '0.875rem' }}>
                    {_.get(row, 'program', '')}
                </a>
            </TableCell>

            {/* Serial Number */}
            <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.75rem', color: sn ? '#e2e8f0' : '#334155' }}>
                {sn || '—'}
            </TableCell>

            {/* Operator */}
            <TableCell sx={{ fontSize: '0.8rem', color: op ? '#94a3b8' : '#334155' }}>
                {op || '—'}
            </TableCell>

            {/* Start date */}
            <TableCell align="center" sx={{ fontFamily: 'monospace', fontSize: '0.75rem', color: '#64748b' }}>
                {_.get(row, 'start_date', '')}
            </TableCell>

            {/* Duration */}
            <TableCell align="center" sx={{ fontFamily: 'monospace', fontSize: '0.75rem', color: '#64748b' }}>
                {formatDuration(_.get(row, 'start_date'), _.get(row, 'end_date'))}
            </TableCell>

            {/* Result */}
            <TableCell align="center" sx={{ width: 96 }}>
                <span className="badge" style={{ backgroundColor: meta.bg, color: meta.color, border: `1px solid ${meta.border}` }}>
                    {result}
                </span>
            </TableCell>
        </TableRow>
    );
}
