"use client";
import {
    Backdrop,
    Box,
    Button,
    Card,
    CardContent,
    CardHeader,
    Chip,
    CircularProgress,
    FormControl,
    Grid,
    InputLabel,
    MenuItem,
    OutlinedInput,
    Paper,
    Select,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    TextField,
    Typography
} from "@mui/material";
// import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
// import { DatePicker } from '@mui/x-date-pickers/DatePicker';
// import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import axios from 'axios';
import * as React from "react";
import ResultPlot from '../components/ResultPlot';
import TestHistogram from '../components/TestHistogram';
import { useConnection } from '../contexts/ConnectionContext';

export default function TestQueryPage() {
    const { connected, connecting, isOnline } = useConnection();
    const [loading, setLoading] = React.useState(false);
    const [testResults, setTestResults] = React.useState([]);
    const [availableTests, setAvailableTests] = React.useState([]);
    const [availablePrograms, setAvailablePrograms] = React.useState([]);
    const [availableDuts, setAvailableDuts] = React.useState([]);

    // Filter states - now supporting multiple selections
    const [selectedTests, setSelectedTests] = React.useState([]);
    const [selectedPrograms, setSelectedPrograms] = React.useState([]);
    const [selectedDuts, setSelectedDuts] = React.useState([]);
    const [selectedResults, setSelectedResults] = React.useState([]);
    const [startDate, setStartDate] = React.useState(null);
    const [endDate, setEndDate] = React.useState(null);

    const getAvailableTests = React.useCallback(() => {
        if (!isOnline) return;

        setLoading(true);
        axios
            .get("/get_available_tests")
            .then((response) => {
                setAvailableTests(response.data);
                setLoading(false);
            })
            .catch((error) => {
                console.error('Error fetching available tests:', error);
                setLoading(false);
            });
    }, [isOnline]);

    const getAvailablePrograms = React.useCallback(() => {
        if (!isOnline) return;

        axios
            .get("/get_available_programs")
            .then((response) => {
                setAvailablePrograms(response.data);
            })
            .catch((error) => {
                console.error('Error fetching available programs:', error);
            });
    }, [isOnline]);

    const getAvailableDuts = React.useCallback(() => {
        if (!isOnline) return;

        axios
            .get("/get_available_duts")
            .then((response) => {
                setAvailableDuts(response.data);
            })
            .catch((error) => {
                console.error('Error fetching available DUTs:', error);
            });
    }, [isOnline]);

    const queryTestResults = React.useCallback(() => {
        if (!isOnline || selectedTests.length === 0) return;

        setLoading(true);
        const params = {
            test_names: selectedTests.length > 0 ? selectedTests.join(',') : undefined,
            programs: selectedPrograms.length > 0 ? selectedPrograms.join(',') : undefined,
            duts: selectedDuts.length > 0 ? selectedDuts.join(',') : undefined,
            results: selectedResults.length > 0 ? selectedResults.join(',') : undefined,
            start_date: startDate ? startDate.toISOString().split('T')[0] : undefined,
            end_date: endDate ? endDate.toISOString().split('T')[0] : undefined
        };

        // Remove undefined values
        Object.keys(params).forEach(key => params[key] === undefined && delete params[key]);

        axios
            .get("/query_test_results", { params })
            .then((response) => {
                setTestResults(response.data);
                setLoading(false);
            })
            .catch((error) => {
                console.error('Error querying test results:', error);
                setLoading(false);
            });
    }, [selectedTests, selectedPrograms, selectedDuts, selectedResults, startDate, endDate, isOnline]);

    const clearFilters = React.useCallback(() => {
        setSelectedTests([]);
        setSelectedPrograms([]);
        setSelectedDuts([]);
        setSelectedResults([]);
        setStartDate(null);
        setEndDate(null);
        setTestResults([]);
    }, []);

    React.useEffect(() => {
        if (isOnline) {
            getAvailableTests();
            getAvailablePrograms();
            getAvailableDuts();
        }
    }, [isOnline, getAvailableTests, getAvailablePrograms, getAvailableDuts]);

    // Clear results when any filter changes to avoid user confusion
    React.useEffect(() => {
        setTestResults([]);
    }, [selectedTests, selectedPrograms, selectedDuts, selectedResults, startDate, endDate]);

    const getResultChip = (result) => {
        switch (result) {
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
                return <Chip label={result} size="small" sx={{ backgroundColor: '#dbeafe', color: '#1e40af', fontWeight: 600 }} />;
        }
    };

    const formatDuration = (startDate, endDate) => {
        if (!startDate || !endDate) return '--:--:--';

        try {
            const start = new Date(startDate);
            const end = new Date(endDate);
            const durationMs = end - start;

            if (durationMs < 0) return '--:--:--';

            const hours = Math.floor(durationMs / (1000 * 60 * 60));
            const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((durationMs % (1000 * 60)) / 1000);

            return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        } catch (error) {
            return '--:--:--';
        }
    };

    return (
        <main className="animate-fade-in">
            <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
                <div className="container mx-auto px-4 py-8">
                    {/* Header */}
                    <div className="mb-8">
                        <h1 className="text-4xl font-bold text-gray-900 mb-2">Tests</h1>
                        <p className="text-gray-600">Compare test results across multiple runs</p>
                    </div>

                    {/* Filters Section */}
                    <Card className="mb-8">
                        <CardHeader title="Filters" />
                        <CardContent>
                            <Grid container spacing={3}>
                                {/* Test Selection */}
                                <Grid item xs={12} md={6}>
                                    <FormControl fullWidth>
                                        <InputLabel>Test Names</InputLabel>
                                        <Select
                                            multiple
                                            value={selectedTests}
                                            onChange={(e) => setSelectedTests(e.target.value)}
                                            input={<OutlinedInput label="Test Names" />}
                                            renderValue={(selected) => (
                                                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                                    {selected.map((value) => (
                                                        <Chip key={value} label={value} size="small" />
                                                    ))}
                                                </Box>
                                            )}
                                        >
                                            {availableTests.map((test) => (
                                                <MenuItem key={test} value={test}>
                                                    {test}
                                                </MenuItem>
                                            ))}
                                        </Select>
                                    </FormControl>
                                </Grid>

                                {/* Program Filter */}
                                <Grid item xs={12} md={6}>
                                    <FormControl fullWidth>
                                        <InputLabel>Programs</InputLabel>
                                        <Select
                                            multiple
                                            value={selectedPrograms}
                                            onChange={(e) => setSelectedPrograms(e.target.value)}
                                            input={<OutlinedInput label="Programs" />}
                                            renderValue={(selected) => (
                                                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                                    {selected.map((value) => (
                                                        <Chip key={value} label={value} size="small" />
                                                    ))}
                                                </Box>
                                            )}
                                        >
                                            {availablePrograms.map((program) => (
                                                <MenuItem key={program} value={program}>
                                                    {program}
                                                </MenuItem>
                                            ))}
                                        </Select>
                                    </FormControl>
                                </Grid>

                                {/* DUT Filter */}
                                <Grid item xs={12} md={6}>
                                    <FormControl fullWidth>
                                        <InputLabel>Devices Under Test</InputLabel>
                                        <Select
                                            multiple
                                            value={selectedDuts}
                                            onChange={(e) => setSelectedDuts(e.target.value)}
                                            input={<OutlinedInput label="Devices Under Test" />}
                                            renderValue={(selected) => (
                                                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                                    {selected.map((value) => (
                                                        <Chip key={value} label={value} size="small" />
                                                    ))}
                                                </Box>
                                            )}
                                        >
                                            {availableDuts.map((dut) => (
                                                <MenuItem key={dut} value={dut}>
                                                    {dut}
                                                </MenuItem>
                                            ))}
                                        </Select>
                                    </FormControl>
                                </Grid>

                                {/* Result Filter */}
                                <Grid item xs={12} md={6}>
                                    <FormControl fullWidth>
                                        <InputLabel>Test Results</InputLabel>
                                        <Select
                                            multiple
                                            value={selectedResults}
                                            onChange={(e) => setSelectedResults(e.target.value)}
                                            input={<OutlinedInput label="Test Results" />}
                                            renderValue={(selected) => (
                                                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                                    {selected.map((value) => (
                                                        <Chip key={value} label={value} size="small" />
                                                    ))}
                                                </Box>
                                            )}
                                        >
                                            <MenuItem value="PASS">PASS</MenuItem>
                                            <MenuItem value="FAIL">FAIL</MenuItem>
                                            <MenuItem value="ERROR">ERROR</MenuItem>
                                            <MenuItem value="SKIPPED">SKIPPED</MenuItem>
                                            <MenuItem value="ABORTED">ABORTED</MenuItem>
                                        </Select>
                                    </FormControl>
                                </Grid>

                                {/* Date Range */}
                                <Grid item xs={12} md={6}>
                                    <TextField
                                        label="Start Date"
                                        type="date"
                                        value={startDate ? startDate.toISOString().split('T')[0] : ''}
                                        onChange={(e) => setStartDate(e.target.value ? new Date(e.target.value) : null)}
                                        InputLabelProps={{ shrink: true }}
                                        fullWidth
                                    />
                                </Grid>

                                <Grid item xs={12} md={6}>
                                    <TextField
                                        label="End Date"
                                        type="date"
                                        value={endDate ? endDate.toISOString().split('T')[0] : ''}
                                        onChange={(e) => setEndDate(e.target.value ? new Date(e.target.value) : null)}
                                        InputLabelProps={{ shrink: true }}
                                        fullWidth
                                    />
                                </Grid>

                                {/* Query and Clear Buttons */}
                                <Grid item xs={12}>
                                    <Box display="flex" justifyContent="center" gap={2} mt={2}>
                                        <Button
                                            variant="contained"
                                            onClick={queryTestResults}
                                            disabled={loading || selectedTests.length === 0}
                                            size="large"
                                            sx={{ minWidth: 200 }}
                                        >
                                            {loading ? <CircularProgress size={24} /> : 'Query Results'}
                                        </Button>
                                        <Button
                                            variant="outlined"
                                            onClick={clearFilters}
                                            disabled={loading}
                                            size="large"
                                            sx={{ minWidth: 120 }}
                                        >
                                            Clear
                                        </Button>
                                    </Box>
                                </Grid>
                            </Grid>
                        </CardContent>
                    </Card>

                    {/* Histogram Section */}
                    {testResults.length > 0 && selectedTests.length > 0 && (
                        (() => {
                            // Group results by test name for histogram
                            const resultsByTest = testResults.reduce((acc, result) => {
                                const testName = result.Name;
                                if (!acc[testName]) {
                                    acc[testName] = [];
                                }
                                acc[testName].push(result);
                                return acc;
                            }, {});

                            // Show histogram for each selected test that has numeric/bool/string/passfail results
                            return Object.entries(resultsByTest).map(([testName, results]) => {
                                const firstResult = results[0];
                                const testType = firstResult?.ResultType?.toLowerCase();

                                // Show histogram for numeric, bool, string, and passfail types
                                if (['numeric', 'bool', 'string', 'passfail'].includes(testType)) {
                                    return (
                                        <TestHistogram
                                            key={testName}
                                            testResults={results}
                                            testType={testType}
                                            testName={testName}
                                        />
                                    );
                                }
                                return null;
                            }).filter(Boolean);
                        })()
                    )}

                    {/* Results Section */}
                    {testResults.length > 0 && (
                        <Card>
                            <CardHeader
                                title={`Results for ${selectedTests.length > 0 ? selectedTests.join(', ') : 'All Tests'}`}
                                subheader={`${testResults.length} test result(s) found`}
                            />
                            <CardContent>
                                <TableContainer component={Paper}>
                                    <Table stickyHeader>
                                        <TableHead>
                                            <TableRow>
                                                <TableCell sx={{ fontWeight: 'bold', backgroundColor: '#f5f5f5' }}>Run ID</TableCell>
                                                <TableCell sx={{ fontWeight: 'bold', backgroundColor: '#f5f5f5' }}>Program</TableCell>
                                                <TableCell sx={{ fontWeight: 'bold', backgroundColor: '#f5f5f5' }}>DUT</TableCell>
                                                <TableCell sx={{ fontWeight: 'bold', backgroundColor: '#f5f5f5' }}>Suite</TableCell>
                                                <TableCell sx={{ fontWeight: 'bold', backgroundColor: '#f5f5f5' }}>Test Name</TableCell>
                                                <TableCell sx={{ fontWeight: 'bold', backgroundColor: '#f5f5f5' }}>Result</TableCell>
                                                <TableCell sx={{ fontWeight: 'bold', backgroundColor: '#f5f5f5', minWidth: '150px', width: '150px', textAlign: 'center' }}>Value</TableCell>
                                                <TableCell sx={{ fontWeight: 'bold', backgroundColor: '#f5f5f5' }}>Unit</TableCell>
                                                <TableCell sx={{ fontWeight: 'bold', backgroundColor: '#f5f5f5' }}>Start Time</TableCell>
                                                <TableCell sx={{ fontWeight: 'bold', backgroundColor: '#f5f5f5' }}>Duration</TableCell>
                                            </TableRow>
                                        </TableHead>
                                        <TableBody>
                                            {testResults.map((result, index) => {
                                                const hasPlot = result.PlotData && result.PlotData.points && result.PlotData.points.length > 0;

                                                return (
                                                    <React.Fragment key={index}>
                                                        <TableRow>
                                                            <TableCell sx={{ fontWeight: 'bold', color: '#1976d2' }}>
                                                                {result.run_id || '-'}
                                                            </TableCell>
                                                            <TableCell>{result.Program || '-'}</TableCell>
                                                            <TableCell>{result.DUT || '-'}</TableCell>
                                                            <TableCell>{result.Suite || '-'}</TableCell>
                                                            <TableCell>{result.Name || '-'}</TableCell>
                                                            <TableCell>{getResultChip(result.Result)}</TableCell>
                                                            <TableCell sx={{
                                                                fontFamily: 'monospace',
                                                                minWidth: '150px',
                                                                width: '150px',
                                                                backgroundColor: '#fafafa',
                                                                border: '1px solid #e0e0e0',
                                                                textAlign: 'center'
                                                            }}>
                                                                {result.Value || '-'}
                                                            </TableCell>
                                                            <TableCell>{result.Unit || '-'}</TableCell>
                                                            <TableCell sx={{ fontFamily: 'monospace' }}>
                                                                {result.Time ? new Date(result.Time).toLocaleString() : '-'}
                                                            </TableCell>
                                                            <TableCell sx={{ fontFamily: 'monospace' }}>
                                                                {formatDuration(result.Time, result.Time)}
                                                            </TableCell>
                                                        </TableRow>
                                                        {hasPlot && (
                                                            <ResultPlot
                                                                show={true}
                                                                plotData={result.PlotData}
                                                            />
                                                        )}
                                                    </React.Fragment>
                                                );
                                            })}
                                        </TableBody>
                                    </Table>
                                </TableContainer>
                            </CardContent>
                        </Card>
                    )}

                    {/* No Tests Selected Message */}
                    {selectedTests.length === 0 && (
                        <Card>
                            <CardContent>
                                <Typography variant="h6" align="center" color="textSecondary">
                                    Please select at least one test to query results
                                </Typography>
                            </CardContent>
                        </Card>
                    )}

                    {/* No Results Message */}
                    {selectedTests.length > 0 && testResults.length === 0 && !loading && (
                        <Card>
                            <CardContent>
                                <Typography variant="h6" align="center" color="textSecondary">
                                    No results found for the selected criteria
                                </Typography>
                            </CardContent>
                        </Card>
                    )}
                </div>
            </div>

            {/* Loading Backdrop */}
            <Backdrop
                sx={{ color: '#fff', zIndex: (theme) => theme.zIndex.drawer + 1 }}
                open={loading}
            >
                <CircularProgress color="inherit" />
            </Backdrop>
        </main>
    );
}
