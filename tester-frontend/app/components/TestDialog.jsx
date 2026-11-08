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
import { alpha, useTheme } from '@mui/material/styles';
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

const createMarkdownOptions = (theme) => ({
    disableParsingRawHTML: true,
    overrides: {
        h1: { props: { style: { fontSize: '1.75rem', margin: '0 0 16px' } } },
        h2: { props: { style: { fontSize: '1.4rem', margin: '24px 0 12px' } } },
        h3: { props: { style: { fontSize: '1.15rem', margin: '20px 0 8px' } } },
        p: { props: { style: { lineHeight: 1.65, margin: '0 0 12px' } } },
        a: { props: { target: '_blank', rel: 'noopener noreferrer' } },
        img: { component: MarkdownImage },
        code: { props: { style: { background: theme.palette.action.hover, color: theme.palette.text.primary, padding: '2px 5px', borderRadius: '4px' } } },
        pre: { props: { style: { overflowX: 'auto', background: theme.palette.action.hover, color: theme.palette.text.primary, padding: '12px', borderRadius: '6px' } } },
        blockquote: { props: { style: { color: theme.palette.text.secondary, margin: '16px 0', paddingLeft: '16px', borderLeft: `4px solid ${theme.palette.divider}` } } }
    }
});

export default function TestDialog(props) {
    const theme = useTheme();
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
                    borderRadius: '8px',
                    boxShadow: '0 20px 40px -10px rgba(0, 0, 0, 0.15), 0 10px 20px -5px rgba(0, 0, 0, 0.1)'
                }
            }}
        >
            <DialogTitle sx={{
                pb: 2,
                borderBottom: `1px solid ${theme.palette.divider}`
            }}>
                <Typography variant="h5" sx={{
                    fontWeight: 600,
                    color: 'text.primary'
                }}>
                    {_.get(data, 'title', 'Test Dialog')}
                </Typography>
            </DialogTitle>
            <DialogContent sx={{ p: 3 }}>
                <Grid container spacing={3}>
                    <Grid item xs={12}>
                        {_.get(data, 'text', '') && (
                            <Typography variant="body1" sx={{
                                color: 'text.secondary',
                                lineHeight: 1.6,
                                mb: _.get(data, 'markdown', '') ? 2 : 0
                            }}>
                                {_.get(data, 'text', '')}
                            </Typography>
                        )}
                        {_.get(data, 'markdown', '') && (
                            <MarkdownImageContext.Provider value={_.get(data, 'markdown_images', {})}>
                                <Box data-testid="dialog-markdown" sx={{ color: 'text.primary', overflowWrap: 'anywhere' }}>
                                    <Markdown options={createMarkdownOptions(theme)}>
                                        {_.get(data, 'markdown', '')}
                                    </Markdown>
                                </Box>
                            </MarkdownImageContext.Provider>
                        )}
                    </Grid>

                    {_.get(data, 'schema', {}).properties && Object.keys(_.get(data, 'schema', {}).properties).length > 0 && (
                        <Grid item xs={12}>
                            <Box sx={{
                                backgroundColor: 'background.default',
                                borderRadius: '12px',
                                p: 3,
                                border: `1px solid ${theme.palette.divider}`
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
                                color: 'text.secondary',
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
                                    backgroundColor: theme.palette.divider,
                                    '& .MuiLinearProgress-bar': {
                                        borderRadius: 4,
                                        backgroundColor: theme.palette.primary.main
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
                                            backgroundColor: theme.palette.primary.main,
                                            '&:hover': {
                                                backgroundColor: theme.palette.primary.dark
                                            }
                                        } : {
                                            borderColor: theme.palette.text.secondary,
                                            color: theme.palette.text.secondary,
                                            '&:hover': {
                                                borderColor: theme.palette.text.primary,
                                                backgroundColor: alpha(theme.palette.text.primary, 0.06)
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
