'use client';
import {
    TableCell,
    TableRow
} from '@mui/material';
import _ from "lodash";
import * as React from 'react';
import {
    CartesianGrid,
    Legend,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis
} from 'recharts';

export default function ResultPlot(props) {
    const { show, plotData } = props;

    if (show) {
        const points = _.get(plotData, 'points', []);
        const xValues = points.map(point => point.x);
        const minX = Math.min(...xValues);
        const maxX = Math.max(...xValues);


        return (
            <React.Fragment>
                <TableRow>
                    <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={10}>
                        <ResponsiveContainer width="100%" height={400}>
                            <LineChart
                                data={points}
                                margin={{ top: 20, right: 120, left: 60, bottom: 60 }}
                            >
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
                                <XAxis
                                    type="number"
                                    dataKey="x"
                                    domain={[minX, maxX]}
                                    label={{
                                        value: _.get(plotData, 'xlabel', 'X'),
                                        position: 'insideBottom',
                                        offset: -10,
                                        style: { textAnchor: 'middle', fill: '#94a3b8' }
                                    }}
                                    tickFormatter={(value) => value.toFixed(2)}
                                    tick={{ fill: '#64748b', fontSize: 12 }}
                                    axisLine={{ stroke: '#334155' }}
                                    tickLine={{ stroke: '#334155' }}
                                />
                                <YAxis
                                    label={{
                                        value: _.get(plotData, 'ylabel', 'Y'),
                                        angle: -90,
                                        position: 'insideLeft',
                                        style: { textAnchor: 'middle', fill: '#94a3b8' }
                                    }}
                                    tick={{ fill: '#64748b', fontSize: 12 }}
                                    axisLine={{ stroke: '#334155' }}
                                    tickLine={{ stroke: '#334155' }}
                                />
                                <Tooltip
                                    formatter={(value, name) => [
                                        typeof value === 'number' ? value.toFixed(3) : value,
                                        name === 'Min Tolerance' ? 'Min' :
                                            name === 'Max Tolerance' ? 'Max' :
                                                name
                                    ]}
                                    labelFormatter={(value) => `${_.get(plotData, 'xlabel', 'X')}: ${value.toFixed(3)}`}
                                    contentStyle={{
                                        backgroundColor: '#1e293b',
                                        border: '1px solid #334155',
                                        borderRadius: '8px',
                                        color: '#e2e8f0',
                                    }}
                                    labelStyle={{ color: '#94a3b8', marginBottom: 4 }}
                                    itemStyle={{ color: '#e2e8f0' }}
                                />
                                <Legend
                                    verticalAlign="middle"
                                    align="right"
                                    layout="vertical"
                                    wrapperStyle={{ paddingLeft: '20px', color: '#94a3b8' }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="min"
                                    stroke="#60a5fa"
                                    strokeDasharray="5 5"
                                    name="Min Tolerance"
                                    dot={false}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="value"
                                    stroke="#34d399"
                                    activeDot={{ r: 4 }}
                                    name="Measured"
                                    dot={{ r: 2 }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="max"
                                    stroke="#f87171"
                                    strokeDasharray="5 5"
                                    name="Max Tolerance"
                                    dot={false}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </TableCell>
                </TableRow>
            </React.Fragment>
        );
    }
    else {
        return;
    }
}
