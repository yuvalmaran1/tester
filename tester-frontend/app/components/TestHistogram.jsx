'use client';
import { Box, Card, CardContent, Chip, Typography } from '@mui/material';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const TestHistogram = ({ testResults, testType, testName }) => {
    // Filter results that have valid values for histogram
    const validResults = testResults.filter(result => {
        const value = result.Value;
        if (value === null || value === undefined || value === '' || value === '-') {
            return false;
        }
        return true;
    });

    if (validResults.length === 0) {
        return (
            <Card sx={{ marginBottom: 2, border: '1px solid #e0e0e0' }}>
                <CardContent>
                    <Typography variant="h6" color="textSecondary" align="center">
                        No valid data for histogram
                    </Typography>
                </CardContent>
            </Card>
        );
    }

    let histogramData = [];
    let statistics = null;

    if (testType === 'numeric') {
        // For numeric data, create bins and calculate statistics
        const numericValues = validResults.map(result => parseFloat(result.Value)).filter(val => !isNaN(val));

        if (numericValues.length === 0) {
            return (
                <Card sx={{ marginBottom: 2, border: '1px solid #e0e0e0' }}>
                    <CardContent>
                        <Typography variant="h6" color="textSecondary" align="center">
                            No valid numeric data for histogram
                        </Typography>
                    </CardContent>
                </Card>
            );
        }

        // Calculate statistics
        const mean = numericValues.reduce((sum, val) => sum + val, 0) / numericValues.length;
        const variance = numericValues.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / numericValues.length;
        const stdev = Math.sqrt(variance);

        statistics = { mean, stdev, count: numericValues.length };

        // Create histogram bins
        const min = Math.min(...numericValues);
        const max = Math.max(...numericValues);
        const range = max - min;

        // Handle edge case where all values are the same
        if (range === 0) {
            histogramData = [{
                bin: 0,
                range: `${min.toFixed(2)}`,
                count: numericValues.length
            }];
        } else {
            const numBins = Math.min(10, Math.max(5, Math.ceil(Math.sqrt(numericValues.length))));
            const binWidth = range / numBins;

            // Initialize bins
            const bins = Array(numBins).fill(0).map((_, i) => ({
                bin: i,
                range: `${(min + i * binWidth).toFixed(2)}-${(min + (i + 1) * binWidth).toFixed(2)}`,
                count: 0
            }));

            // Count values in each bin
            numericValues.forEach(value => {
                let binIndex = Math.floor((value - min) / binWidth);
                // Ensure binIndex is within bounds
                binIndex = Math.max(0, Math.min(binIndex, numBins - 1));

                if (bins[binIndex] && typeof bins[binIndex].count === 'number') {
                    bins[binIndex].count++;
                }
            });

            histogramData = bins;
        }

    } else if (testType === 'bool') {
        // For boolean data, count true/false values
        const trueCount = validResults.filter(result =>
            result.Value === 'True' || result.Value === 'true' || result.Value === true
        ).length;
        const falseCount = validResults.filter(result =>
            result.Value === 'False' || result.Value === 'false' || result.Value === false
        ).length;

        histogramData = [
            { bin: 0, range: 'False', count: falseCount },
            { bin: 1, range: 'True', count: trueCount }
        ];

    } else if (testType === 'string') {
        // For string data, count unique values
        const valueCounts = {};
        validResults.forEach(result => {
            const value = String(result.Value);
            valueCounts[value] = (valueCounts[value] || 0) + 1;
        });

        // Convert to histogram format, limit to top 10 most frequent values
        const sortedValues = Object.entries(valueCounts)
            .sort(([, a], [, b]) => b - a)
            .slice(0, 10);

        histogramData = sortedValues.map(([value, count], index) => ({
            bin: index,
            range: value.length > 20 ? value.substring(0, 20) + '...' : value,
            count
        }));

    } else if (testType === 'passfail') {
        // For passfail data, count PASS/FAIL results
        const passCount = validResults.filter(result =>
            result.Result === 'PASS' || result.Result === 'pass'
        ).length;
        const failCount = validResults.filter(result =>
            result.Result === 'FAIL' || result.Result === 'fail'
        ).length;

        histogramData = [
            { bin: 0, range: 'FAIL', count: failCount },
            { bin: 1, range: 'PASS', count: passCount }
        ];
    }

    return (
        <Card sx={{ marginBottom: 2, border: '1px solid #e0e0e0' }}>
            <CardContent>
                <Typography variant="h6" gutterBottom>
                    Value Distribution - {testName}
                </Typography>

                {statistics && (
                    <Box sx={{ mb: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        <Chip
                            label={`Mean: ${statistics.mean.toFixed(4)}`}
                            color="primary"
                            variant="outlined"
                        />
                        <Chip
                            label={`Std Dev: ${statistics.stdev.toFixed(4)}`}
                            color="secondary"
                            variant="outlined"
                        />
                        <Chip
                            label={`Count: ${statistics.count}`}
                            color="default"
                            variant="outlined"
                        />
                    </Box>
                )}

                <Box sx={{ width: '100%', height: 300 }}>
                    <ResponsiveContainer>
                        <BarChart data={histogramData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis
                                dataKey="range"
                                angle={-45}
                                textAnchor="end"
                                height={80}
                                fontSize={12}
                            />
                            <YAxis />
                            <Tooltip
                                formatter={(value, name) => [value, 'Count']}
                                labelFormatter={(label) => `Range: ${label}`}
                            />
                            <Bar
                                dataKey="count"
                                fill="#3b82f6"
                                stroke="#1e40af"
                                strokeWidth={1}
                            />
                        </BarChart>
                    </ResponsiveContainer>
                </Box>

                <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                    Based on {validResults.length} valid test results
                </Typography>
            </CardContent>
        </Card>
    );
};

export default TestHistogram;
