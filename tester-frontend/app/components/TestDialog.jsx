import { materialCells, materialRenderers } from '@jsonforms/material-renderers';
import { JsonForms } from '@jsonforms/react';
import {
    Box,
    Button,
    Dialog,
    DialogContent,
    DialogTitle,
    Grid,
    LinearProgress,
    Typography
} from '@mui/material';
import _ from "lodash";
import * as React from 'react';

export default function TestDialog(props) {
    const { onClose, data } = props;
    const [responseData, setResponseData] = React.useState(_.get(data, 'defaults', {}));

    React.useEffect(() => {
        setResponseData(_.get(data, 'defaults', {}));
    }, [data]);

    const handleClose = () => {
        /* ignore */
        /*onClose("Cancel", responseData);*/
    };

    return (
        <Dialog
            open={_.get(data, 'show', false)}
            onClose={handleClose}
            maxWidth='md'
            fullWidth
            PaperProps={{
                sx: {
                    borderRadius: '16px',
                    boxShadow: '0 20px 40px -10px rgba(0, 0, 0, 0.15), 0 10px 20px -5px rgba(0, 0, 0, 0.1)'
                }
            }}
        >
            <DialogTitle sx={{
                pb: 2,
                borderBottom: '1px solid #e2e8f0'
            }}>
                <Typography variant="h5" sx={{
                    fontWeight: 600,
                    color: '#1e293b'
                }}>
                    {_.get(data, 'title', 'Test Dialog')}
                </Typography>
            </DialogTitle>
            <DialogContent sx={{ p: 3 }}>
                <Grid container spacing={3}>
                    <Grid item xs={12}>
                        <Typography variant="body1" sx={{
                            color: '#64748b',
                            lineHeight: 1.6
                        }}>
                            {_.get(data, 'text', '')}
                        </Typography>
                    </Grid>

                    {_.get(data, 'schema', {}).properties && Object.keys(_.get(data, 'schema', {}).properties).length > 0 && (
                        <Grid item xs={12}>
                            <Box sx={{
                                backgroundColor: '#f8fafc',
                                borderRadius: '12px',
                                p: 3,
                                border: '1px solid #e2e8f0'
                            }}>
                                <JsonForms
                                    schema={_.get(data, 'schema', { "type": "object", "properties": {} })}
                                    data={responseData}
                                    renderers={materialRenderers}
                                    cells={materialCells}
                                    onChange={({ data, errors }) => setResponseData(data)}
                                />
                            </Box>
                        </Grid>
                    )}

                    <Grid item xs={12}>
                        <Box sx={{ mb: 2 }}>
                            <Typography variant="body2" sx={{
                                color: '#64748b',
                                mb: 1
                            }}>
                                Progress: {Math.round(_.get(data, 'progress', 0))}%
                            </Typography>
                            <LinearProgress
                                variant="determinate"
                                value={_.get(data, 'progress', 0)}
                                sx={{
                                    height: 8,
                                    borderRadius: 4,
                                    backgroundColor: '#e2e8f0',
                                    '& .MuiLinearProgress-bar': {
                                        borderRadius: 4,
                                        background: 'linear-gradient(90deg, #3b82f6 0%, #1e3a8a 100%)'
                                    }
                                }}
                            />
                        </Box>
                    </Grid>

                    <Grid item xs={12}>
                        <Box sx={{
                            display: 'flex',
                            gap: 2,
                            flexWrap: 'wrap',
                            justifyContent: 'center'
                        }}>
                            {_.get(data, 'responses', []).map((rsp, index) => (
                                <Button
                                    key={index}
                                    onClick={() => onClose({ rsp }, responseData)}
                                    variant={rsp.toLowerCase() === 'ok' || rsp.toLowerCase() === 'yes' ? 'contained' : 'outlined'}
                                    sx={{
                                        minWidth: 120,
                                        height: 48,
                                        borderRadius: '12px',
                                        fontWeight: 600,
                                        ...(rsp.toLowerCase() === 'ok' || rsp.toLowerCase() === 'yes' ? {
                                            background: 'linear-gradient(135deg, #3b82f6 0%, #1e3a8a 100%)',
                                            '&:hover': {
                                                background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)'
                                            }
                                        } : {
                                            borderColor: '#64748b',
                                            color: '#64748b',
                                            '&:hover': {
                                                borderColor: '#475569',
                                                backgroundColor: '#f1f5f9'
                                            }
                                        })
                                    }}
                                >
                                    {rsp}
                                </Button>
                            ))}
                        </Box>
                    </Grid>
                </Grid>
            </DialogContent>
        </Dialog>
    );
}
