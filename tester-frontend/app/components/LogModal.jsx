import CloseIcon from '@mui/icons-material/Close';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Modal from '@mui/material/Modal';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import * as React from 'react';

const style = {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: '90%',
    maxWidth: '1000px',
    height: '80vh',
    bgcolor: 'background.paper',
    borderRadius: '16px',
    boxShadow: '0 20px 40px -10px rgba(0, 0, 0, 0.15), 0 10px 20px -5px rgba(0, 0, 0, 0.1)',
    p: 0,
    outline: 'none',
    display: 'flex',
    flexDirection: 'column'
};

export default function LogModal(props) {
    const { open, handleClose, log } = props;
    let messagesEndRef = React.useRef(null);

    React.useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }, [log]);

    return (
        <Modal
            open={open}
            onClose={handleClose}
            aria-labelledby="modal-modal-title"
            aria-describedby="modal-modal-description"
            sx={{
                backdropFilter: 'blur(4px)',
                backgroundColor: 'rgba(0, 0, 0, 0.5)'
            }}
        >
            <Box sx={style}>
                {/* Header */}
                <Box sx={{
                    p: 3,
                    borderBottom: '1px solid #e2e8f0',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                }}>
                    <Typography
                        id="modal-modal-title"
                        variant="h5"
                        component="h2"
                        sx={{
                            fontWeight: 600,
                            color: '#1e293b'
                        }}
                    >
                        Test Framework Log
                    </Typography>
                    <IconButton
                        onClick={handleClose}
                        sx={{
                            color: '#64748b',
                            '&:hover': {
                                color: '#ef4444',
                                backgroundColor: '#fef2f2'
                            }
                        }}
                    >
                        <CloseIcon />
                    </IconButton>
                </Box>

                {/* Log Content */}
                <Paper sx={{
                    flex: 1,
                    m: 3,
                    mt: 0,
                    overflowY: 'auto',
                    backgroundColor: '#0f172a',
                    borderRadius: '12px',
                    border: '1px solid #334155'
                }}>
                    <Box sx={{ p: 2 }}>
                        <pre style={{
                            margin: 0,
                            fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                            fontSize: '14px',
                            lineHeight: '1.5',
                            color: '#e2e8f0',
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-word'
                        }}>
                            {log}
                            <div ref={messagesEndRef} />
                        </pre>
                    </Box>
                </Paper>
            </Box>
        </Modal>
    );
}
