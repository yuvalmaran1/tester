'use client';
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
import Markdown from 'markdown-to-jsx';
import * as React from 'react';

const MarkdownImageContext = React.createContext({});

const MarkdownImage = ({ src, alt, ...props }) => {
    const images = React.useContext(MarkdownImageContext);

    return (
        <Box
            component="img"
            src={images[src] || src}
            alt={alt || ''}
            {...props}
            sx={{
                display: 'block',
                maxWidth: '100%',
                maxHeight: '60vh',
                width: 'auto',
                height: 'auto',
                my: 2,
                borderRadius: '6px'
            }}
        />
    );
};

const markdownOptions = {
    disableParsingRawHTML: true,
    overrides: {
        h1: { props: { style: { fontSize: '1.75rem', margin: '0 0 16px' } } },
        h2: { props: { style: { fontSize: '1.4rem', margin: '24px 0 12px' } } },
        h3: { props: { style: { fontSize: '1.15rem', margin: '20px 0 8px' } } },
        p: { props: { style: { lineHeight: 1.65, margin: '0 0 12px' } } },
        a: { props: { target: '_blank', rel: 'noopener noreferrer' } },
        img: { component: MarkdownImage },
        code: { props: { style: { background: '#f1f5f9', padding: '2px 5px', borderRadius: '4px' } } },
        pre: { props: { style: { overflowX: 'auto', background: '#f1f5f9', padding: '12px', borderRadius: '6px' } } },
        blockquote: { props: { style: { margin: '16px 0', paddingLeft: '16px', borderLeft: '4px solid #94a3b8' } } }
    }
};

export default function TestDialog(props) {
    const { onClose, data } = props;
    const [responseData, setResponseData] = React.useState(_.get(data, 'defaults', {}));
    const show = _.get(data, 'show', false);

    React.useEffect(() => {
        if (show) {
            setResponseData(_.get(data, 'defaults', {}));
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [show]);

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
                        {_.get(data, 'text', '') && (
                            <Typography variant="body1" sx={{
                                color: '#64748b',
                                lineHeight: 1.6,
                                mb: _.get(data, 'markdown', '') ? 2 : 0
                            }}>
                                {_.get(data, 'text', '')}
                            </Typography>
                        )}
                        {_.get(data, 'markdown', '') && (
                            <MarkdownImageContext.Provider value={_.get(data, 'markdown_images', {})}>
                                <Box sx={{ color: '#334155', overflowWrap: 'anywhere' }}>
                                    <Markdown options={markdownOptions}>
                                        {_.get(data, 'markdown', '')}
                                    </Markdown>
                                </Box>
                            </MarkdownImageContext.Provider>
                        )}
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
