import DownloadIcon from '@mui/icons-material/Download';
import {
    Button,
    Chip,
    TableCell,
    TableRow
} from '@mui/material';
import _ from "lodash";
import Link from 'next/link';

export default function TestRunRow(props) {
    const { row } = props;

    const formatDuration = (startDate, endDate) => {
        if (!startDate || !endDate) {
            return '--:--:--';
        }

        try {
            const start = new Date(startDate);
            const end = new Date(endDate);
            const durationMs = end - start;

            if (durationMs < 0) {
                return '--:--:--';
            }

            const hours = Math.floor(durationMs / (1000 * 60 * 60));
            const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((durationMs % (1000 * 60)) / 1000);

            return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        } catch (error) {
            console.error('Error calculating duration:', error);
            return '--:--:--';
        }
    };

    const getResultChip = (result) => {
        const resultValue = _.get(row, 'result', 'UNKNOWN');

        switch (resultValue) {
            case 'PASS':
                return <Chip label="PASS" size="small" sx={{ backgroundColor: '#d1fae5', color: '#065f46', fontWeight: 600 }} />;
            case 'FAIL':
                return <Chip label="FAIL" size="small" sx={{ backgroundColor: '#fee2e2', color: '#991b1b', fontWeight: 600 }} />;
            case 'ERROR':
                return <Chip label="ERROR" size="small" sx={{ backgroundColor: '#fef3c7', color: '#92400e', fontWeight: 600 }} />;
            case 'SKIPPED':
                return <Chip label="SKIPPED" size="small" sx={{ backgroundColor: '#f1f5f9', color: '#475569', fontWeight: 600 }} />;
            case 'ABORTED':
                return <Chip label="ABORTED" size="small" sx={{ backgroundColor: '#e9d5ff', color: '#6b21a8', fontWeight: 600 }} />;
            default:
                return <Chip label={resultValue} size="small" sx={{ backgroundColor: '#dbeafe', color: '#1e40af', fontWeight: 600 }} />;
        }
    };

    return (
        <TableRow
            hover
            sx={{
                '&:hover': {
                    backgroundColor: '#f8fafc'
                },
                '& > *': {
                    borderBottom: '1px solid #f1f5f9'
                }
            }}
        >
            <TableCell align="center">
                <Button
                    variant="outlined"
                    href={'/generate_report/' + _.get(row, 'run_id', '0')}
                    sx={{
                        minWidth: 'auto',
                        width: 40,
                        height: 40,
                        borderRadius: '8px',
                        borderColor: '#10b981',
                        color: '#10b981',
                        '&:hover': {
                            borderColor: '#059669',
                            backgroundColor: '#ecfdf5'
                        }
                    }}
                >
                    <DownloadIcon fontSize="small" />
                </Button>
            </TableCell>

            <TableCell align="center">
                <Link
                    href={'/show_report/' + _.get(row, 'run_id', '0')}
                    className="text-primary-600 hover:text-primary-700 font-mono font-semibold"
                >
                    {_.get(row, 'run_id', '')}
                </Link>
            </TableCell>

            <TableCell align="left">
                <Link
                    href={'/show_report/' + _.get(row, 'run_id', '0')}
                    className="text-gray-700 hover:text-primary-600 font-medium"
                >
                    {_.get(row, 'dut', '')}
                </Link>
            </TableCell>

            <TableCell align="left">
                <Link
                    href={'/show_report/' + _.get(row, 'run_id', '0')}
                    className="text-gray-700 hover:text-primary-600 font-medium"
                >
                    {_.get(row, 'program', '')}
                </Link>
            </TableCell>

            <TableCell align="center" sx={{ fontFamily: 'monospace', fontSize: '0.875rem', color: '#64748b' }}>
                <Link
                    href={'/show_report/' + _.get(row, 'run_id', '0')}
                    className="text-gray-600 hover:text-primary-600"
                >
                    {_.get(row, 'start_date', '')}
                </Link>
            </TableCell>

            <TableCell align="center" sx={{ fontFamily: 'monospace', fontSize: '0.875rem', color: '#64748b' }}>
                <Link
                    href={'/show_report/' + _.get(row, 'run_id', '0')}
                    className="text-gray-600 hover:text-primary-600"
                >
                    {formatDuration(_.get(row, 'start_date', ''), _.get(row, 'end_date', ''))}
                </Link>
            </TableCell>

            <TableCell align="center">
                <Link
                    href={'/show_report/' + _.get(row, 'run_id', '0')}
                    className="hover:opacity-80 transition-opacity"
                >
                    {getResultChip(_.get(row, 'result', ''))}
                </Link>
            </TableCell>
        </TableRow>
    );
}
