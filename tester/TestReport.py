import os
from importlib.metadata import version
import plotly.graph_objects as go
import plotly.express as px
import plotly.subplots as sp
from collections import Counter
from .TestRun import TestRun
import pathlib
from datetime import timedelta
import tempfile
import base64

class TestReport:
    LOGO_PATH = pathlib.Path(__file__).parent.resolve().joinpath('Assets').joinpath('tester.png')
    DUT_IMAGE_PATH = pathlib.Path(__file__).parent.resolve().joinpath('Assets').joinpath('dut.png')

    def __init__(self, run: TestRun, path: str = None) -> None:
        self.run = run
        self.path = path

    def generate(self) -> str:
        colormap = {
            "PASS": "limegreen",
            "FAIL": "tomato",
            "INFOONLY": "cornflowerblue",
            "SKIPPED": "silver",
            "UNKNOWN": "dimgray",
            "ERROR": "orange",
            "ABORTED": "magenta"
        }

        tests_results = [t.to_dict() for t in self.run.test_results]
        # Process results and preserve PlotData for numeric2d results
        numeric2d_plots = []
        for result in tests_results:
            # Convert time to relative format
            result['Time'] = str(timedelta(seconds=(result['Time'] - self.run.start_date).seconds))

            # Preserve PlotData for numeric2d results and collect for plotting
            if 'PlotData' in result and result.get('ResultType') == 'numeric2d':
                plot_data = result['PlotData']
                if plot_data and 'points' in plot_data:
                    numeric2d_plots.append({
                        'name': result['Name'],
                        'data': plot_data
                    })
            else:
                # Remove PlotData for non-numeric2d results
                if 'PlotData' in result:
                    del result['PlotData']

        duration = str(timedelta(seconds=(self.run.end_date - self.run.start_date).seconds))
        num_tests = len(self.run.test_results)

        # generate result stats in bar chart
        stats_count = Counter([t.result.name for t in self.run.test_results])
        stats_res = list(stats_count.keys())
        stats_cnt = list(stats_count.values())
        stats_color = [colormap[s] for s in stats_res]

        # Create Plotly bar chart for result distribution
        stats_bar = go.Figure(data=[
            go.Bar(
                x=stats_res,
                y=stats_cnt,
                marker_color=stats_color,
                text=stats_cnt,
                textposition='auto'
            )
        ])
        stats_bar.update_layout(
            title="Test Result Distribution",
            xaxis_title="Result",
            yaxis_title="Count",
            showlegend=False
        )

        # Generate HTML string directly
        html_content = self._generate_html_string(None)

        if self.path:
            with open(self.path, 'w', encoding='utf-8') as f:
                f.write(html_content)

        return html_content

    def _generate_numeric2d_plots_html(self, numeric2d_plots):
        """Generate HTML for numeric2d plots"""
        if not numeric2d_plots:
            return ""

        plots_html = '<div class="plots-container"><h3 class="plots-title"><i class="fas fa-chart-line"></i> 2D Test Results</h3>'

        for plot in numeric2d_plots:
            plot_data = plot['data']
            plot_name = plot['name']

            # Extract data points
            points = plot_data.get('points', [])
            if not points:
                continue

            x_values = [point['x'] for point in points]
            y_values = [point['value'] for point in points]
            min_values = [point.get('min', None) for point in points]
            max_values = [point.get('max', None) for point in points]

            # Create Plotly figure
            fig = go.Figure()

            # Add tolerance traces if available
            if any(min_values) and any(max_values):
                # Add minimum tolerance line (blue)
                fig.add_trace(go.Scatter(
                    x=x_values,
                    y=min_values,
                    mode='lines',
                    name='Min Tolerance',
                    line=dict(color='blue', width=2, dash='dash'),
                    hovertemplate='<b>Min Tolerance</b><br>' +
                                 'X: %{x:.3f}<br>' +
                                 'Y: %{y:.3f}<extra></extra>'
                ))

                # Add maximum tolerance line (red)
                fig.add_trace(go.Scatter(
                    x=x_values,
                    y=max_values,
                    mode='lines',
                    name='Max Tolerance',
                    line=dict(color='red', width=2, dash='dash'),
                    hovertemplate='<b>Max Tolerance</b><br>' +
                                 'X: %{x:.3f}<br>' +
                                 'Y: %{y:.3f}<extra></extra>'
                ))

            # Add main data line (green)
            fig.add_trace(go.Scatter(
                x=x_values,
                y=y_values,
                mode='lines+markers',
                name='Measured',
                line=dict(color='green', width=2),
                marker=dict(size=4, color='green'),
                hovertemplate='<b>Measured</b><br>' +
                             'X: %{x:.3f}<br>' +
                             'Y: %{y:.3f}<br>' +
                             'Min: %{customdata[0]:.3f}<br>' +
                             'Max: %{customdata[1]:.3f}<extra></extra>',
                customdata=list(zip(min_values, max_values))
            ))

            # Update layout
            fig.update_layout(
                template='plotly_white',
                height=400,
                margin=dict(l=60, r=50, t=20, b=60),  # Increased margins for labels
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                # Fit plot to data limits
                xaxis=dict(
                    range=[min(x_values), max(x_values)],
                    title=plot_data.get('xlabel', 'X'),
                    title_standoff=10  # Space between title and axis
                ),
                yaxis=dict(
                    title=plot_data.get('ylabel', 'Y'),
                    title_standoff=10  # Space between title and axis
                )
            )

            # Convert to HTML
            plot_html = fig.to_html(include_plotlyjs=False, div_id=f"plot_{plot_name.replace(' ', '_')}")
            plots_html += f'<div class="plot-item">{plot_html}</div>'

        plots_html += '</div>'
        return plots_html

    def _generate_single_plot_html(self, plot_name, plot_data):
        """Generate HTML for a single inline plot"""
        # Extract data points
        points = plot_data.get('points', [])
        if not points:
            return ""

        x_values = [point['x'] for point in points]
        y_values = [point['value'] for point in points]
        min_values = [point.get('min', None) for point in points]
        max_values = [point.get('max', None) for point in points]

        # Create Plotly figure
        fig = go.Figure()

        # Add tolerance traces if available
        if any(min_values) and any(max_values):
            # Add minimum tolerance line (blue)
            fig.add_trace(go.Scatter(
                x=x_values,
                y=min_values,
                mode='lines',
                name='Min Tolerance',
                line=dict(color='blue', width=2, dash='dash'),
                hovertemplate='<b>Min Tolerance</b><br>' +
                             'X: %{x:.3f}<br>' +
                             'Y: %{y:.3f}<extra></extra>'
            ))

            # Add maximum tolerance line (red)
            fig.add_trace(go.Scatter(
                x=x_values,
                y=max_values,
                mode='lines',
                name='Max Tolerance',
                line=dict(color='red', width=2, dash='dash'),
                hovertemplate='<b>Max Tolerance</b><br>' +
                             'X: %{x:.3f}<br>' +
                             'Y: %{y:.3f}<extra></extra>'
            ))

        # Add main data line (green)
        fig.add_trace(go.Scatter(
            x=x_values,
            y=y_values,
            mode='lines+markers',
            name='Measured',
            line=dict(color='green', width=2),
            marker=dict(size=4, color='green'),
            hovertemplate='<b>Measured</b><br>' +
                         'X: %{x:.3f}<br>' +
                         'Y: %{y:.3f}<br>' +
                         'Min: %{customdata[0]:.3f}<br>' +
                         'Max: %{customdata[1]:.3f}<extra></extra>',
            customdata=list(zip(min_values, max_values))
        ))

        # Update layout for inline display
        fig.update_layout(
            template='plotly_white',
            height=300,  # Smaller height for inline display
            margin=dict(l=60, r=20, t=20, b=60),  # Increased margins for labels
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            # Fit plot to data limits
            xaxis=dict(
                range=[min(x_values), max(x_values)],
                title=plot_data.get('xlabel', 'X'),
                title_standoff=10  # Space between title and axis
            ),
            yaxis=dict(
                title=plot_data.get('ylabel', 'Y'),
                title_standoff=10  # Space between title and axis
            )
        )

        # Convert to HTML
        plot_html = fig.to_html(include_plotlyjs=False, div_id=f"inline_plot_{plot_name.replace(' ', '_')}")
        return f'<div class="inline-plot">{plot_html}</div>'

    def _generate_table_html(self, tests_results, colormap, numeric2d_plots=None):
        """Generate HTML table for test results with inline plots for numeric2d results"""
        if not tests_results:
            return "<p>No test results available</p>"

        # Get columns but exclude PlotData, ResultType, and X_Unit from table display
        all_columns = list(tests_results[0].keys())
        columns = [col for col in all_columns if col not in ['PlotData', 'ResultType', 'X_Unit']]

        table_html = '<div class="table-responsive"><table class="table table-striped table-hover">'
        table_html += '<thead><tr>'
        for col in columns:
            # Define alignment classes for different columns
            if col in ['Time', 'Suite', 'Min', 'Value', 'Max', 'Unit', 'Result']:
                align_class = 'text-center'
            else:  # Name, Comment
                align_class = 'text-left'
            table_html += f'<th class="{align_class}">{col}</th>'
        table_html += '</tr></thead><tbody>'

        for result in tests_results:
            # Check if this is a numeric2d result with plot data
            is_numeric2d = result.get('ResultType') == 'numeric2d' and 'PlotData' in result
            rowspan = 2 if is_numeric2d else 1

            table_html += '<tr>'
            for col in columns:
                # Define alignment classes for different columns
                if col in ['Time', 'Suite', 'Min', 'Value', 'Max', 'Unit', 'Result']:
                    align_class = 'text-center'
                else:  # Name, Comment
                    align_class = 'text-left'

                if col == 'Result':
                    status_class = f"status-{result[col].lower()}"
                    table_html += f'<td class="{align_class}"><span class="status-badge {status_class}">{result[col]}</span></td>'
                else:
                    table_html += f'<td class="{align_class}">{result[col]}</td>'
            table_html += '</tr>'

            # Add plot row for numeric2d results
            if is_numeric2d:
                plot_data = result['PlotData']
                if plot_data and 'points' in plot_data:
                    plot_html = self._generate_single_plot_html(result['Name'], plot_data)
                    table_html += f'<tr class="plot-row"><td colspan="{len(columns)}">{plot_html}</td></tr>'

        table_html += '</tbody></table></div>'
        return table_html

    def _generate_attachments_html(self):
        """Generate HTML for attachments section"""
        attachments_html = ""

        # Generate log file
        temp_dir = tempfile.TemporaryDirectory()
        log_filename = os.path.join(temp_dir.name, "tester.log")
        with open(log_filename, 'w') as log_file:
            log_file.writelines(self.run.log)

        # Create download link for log
        with open(log_filename, 'r') as log_file:
            log_content = log_file.read()
            log_b64 = base64.b64encode(log_content.encode()).decode()
            attachments_html += f'''
            <div class="mb-4">
                <h5 class="mb-3"><i class="fas fa-file-alt me-2"></i>Test Log</h5>
                <a href="data:text/plain;base64,{log_b64}" download="tester.log" class="btn-download">
                    <i class="fas fa-download"></i> Download tester.log
                </a>
            </div>
            '''

        # Generate attachment zip file if it exists
        if self.run.attachment_exists():
            attachments_filename = os.path.join(temp_dir.name, "attachments.zip")
            with open(attachments_filename, 'wb') as attach_file:
                attach_file.write(self.run.get_attachment())

            with open(attachments_filename, 'rb') as attach_file:
                attach_content = attach_file.read()
                attach_b64 = base64.b64encode(attach_content).decode()
                attachments_html += f'''
                <div class="mb-4">
                    <h5 class="mb-3"><i class="fas fa-archive me-2"></i>Test Attachments</h5>
                    <a href="data:application/zip;base64,{attach_b64}" download="attachments.zip" class="btn-download">
                        <i class="fas fa-download"></i> Download attachments.zip
                    </a>
                </div>
                '''

        return attachments_html


    def _get_program_modification_indicator(self):
        """Generate HTML for program modification indicator in the Test Program card"""
        if not hasattr(self.run, 'program_modified') or not self.run.program_modified:
            return ""

        return '''
            <span class="program-modified-indicator" title="This program was modified by the user">
                <i class="fas fa-edit" style="color: var(--tester-warning); margin-left: 10px;"></i>
                <span style="color: var(--tester-warning); font-size: 0.8em; margin-left: 5px;">Modified</span>
            </span>
        '''

    def _generate_program_attributes_html(self):
        """Generate HTML for program attributes section"""
        if not hasattr(self.run, 'program_attr') or not self.run.program_attr:
            return ''

        attributes_html = ''
        for key, value in self.run.program_attr.items():
            # Format the value for display
            if isinstance(value, (dict, list)):
                formatted_value = str(value)
            else:
                formatted_value = str(value)

            attributes_html += f'''
                <tr>
                    <td class="attr-key">{key}</td>
                    <td class="attr-value">{formatted_value}</td>
                </tr>
            '''

        return f'''
        <div class="row">
            <div class="col-12">
                <div class="info-card">
                    <h3><i class="fas fa-cogs"></i> Program Attributes</h3>
                    <div class="table-responsive">
                        <table class="table table-striped table-sm">
                            <thead>
                                <tr>
                                    <th class="attr-header">Attribute</th>
                                    <th class="attr-header">Value</th>
                                </tr>
                            </thead>
                            <tbody>
                                {attributes_html}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        '''

    def _format_duration(self, start_date, end_date):
        """Format duration as hh:mm:ss"""
        if not start_date or not end_date:
            return '--:--:--'

        try:
            duration_seconds = (end_date - start_date).total_seconds()
            if duration_seconds < 0:
                return '--:--:--'

            hours = int(duration_seconds // 3600)
            minutes = int((duration_seconds % 3600) // 60)
            seconds = int(duration_seconds % 60)

            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        except Exception:
            return '--:--:--'

    def _get_overall_result_color(self, result_name):
        """Get the appropriate color for the overall result"""
        color_map = {
            "PASS": "var(--tester-success)",      # Green
            "FAIL": "var(--tester-danger)",       # Red
            "ERROR": "var(--tester-warning)",     # Orange
            "INFOONLY": "var(--tester-info)",     # Blue
            "SKIPPED": "var(--tester-gray)",      # Gray
            "UNKNOWN": "#6b7280",                   # Dark gray
            "ABORTED": "#dc2626"                    # Dark red
        }
        return color_map.get(result_name, "var(--tester-primary)")

    def _get_bootstrap_css(self):
        """Get Bootstrap CSS as embedded string"""
        # Minimal Bootstrap CSS for the components we use
        return """
        /* Bootstrap 5.3.0 - Minimal CSS for our components */
        *,*::before,*::after{box-sizing:border-box}
        body{margin:0;font-family:var(--bs-font-sans-serif);font-size:1rem;font-weight:400;line-height:1.5;color:#212529;background-color:#fff}
        .container-fluid{width:100%;padding-right:var(--bs-gutter-x,.75rem);padding-left:var(--bs-gutter-x,.75rem);margin-right:auto;margin-left:auto}
        .row{--bs-gutter-x:1.5rem;--bs-gutter-y:0;display:flex;flex-wrap:wrap;margin-top:calc(-1 * var(--bs-gutter-y));margin-right:calc(-.5 * var(--bs-gutter-x));margin-left:calc(-.5 * var(--bs-gutter-x))}
        .row>*{flex-shrink:0;width:100%;max-width:100%;padding-right:calc(var(--bs-gutter-x) * .5);padding-left:calc(var(--bs-gutter-x) * .5);margin-top:var(--bs-gutter-y)}
        .col{flex:1 0 0%}
        .col-12{flex:0 0 auto;width:100%}
        .col-6{flex:0 0 auto;width:50%}
        .col-4{flex:0 0 auto;width:33.33333333%}
        .col-2{flex:0 0 auto;width:16.66666667%}
        .col-lg-8{flex:0 0 auto;width:66.66666667%}
        .col-lg-4{flex:0 0 auto;width:33.33333333%}
        .col-md-6{flex:0 0 auto;width:50%}
        .text-center{text-align:center!important}
        .text-white{color:#fff!important}
        .mb-3{margin-bottom:1rem!important}
        .mb-4{margin-bottom:1.5rem!important}
        .mt-4{margin-top:1.5rem!important}
        .me-2{margin-right:.5rem!important}
        .d-block{display:block!important}
        .mx-auto{margin-right:auto!important;margin-left:auto!important}
        .table{--bs-table-bg:transparent;--bs-table-accent-bg:transparent;--bs-table-striped-color:#212529;--bs-table-striped-bg:rgba(0,0,0,.05);--bs-table-active-color:#212529;--bs-table-active-bg:rgba(0,0,0,.1);--bs-table-hover-color:#212529;--bs-table-hover-bg:rgba(0,0,0,.075);width:100%;margin-bottom:1rem;color:#212529;vertical-align:top;border-color:#dee2e6}
        .table>:not(caption)>*>*{padding:.5rem .5rem;background-color:var(--bs-table-bg);border-bottom-width:1px}
        .table-striped>tbody>tr:nth-of-type(odd)>td,.table-striped>tbody>tr:nth-of-type(odd)>th{--bs-table-accent-bg:rgba(0,0,0,.05);color:var(--bs-table-striped-color)}
        .table-hover>tbody>tr:hover>td,.table-hover>tbody>tr:hover>th{--bs-table-accent-bg:rgba(0,0,0,.075);color:var(--bs-table-hover-color)}
        .table-responsive{overflow-x:auto}
        @media (max-width:575.98px){.table-responsive-sm{overflow-x:auto}}
        @media (max-width:767.98px){.table-responsive-md{overflow-x:auto}}
        @media (max-width:991.98px){.table-responsive-lg{overflow-x:auto}}
        @media (max-width:1199.98px){.table-responsive-xl{overflow-x:auto}}
        @media (max-width:1399.98px){.table-responsive-xxl{overflow-x:auto}}
        """

    def _get_fontawesome_css(self):
        """Get Font Awesome CSS as embedded string"""
        # Essential Font Awesome icons as CSS
        return """
        /* Font Awesome 6.4.0 - Essential Icons */
        .fas{font-family:"Font Awesome 6 Free";font-weight:900}
        .fa-microchip:before{content:"\\f2db"}
        .fa-play-circle:before{content:"\\f144"}
        .fa-chart-bar:before{content:"\\f080"}
        .fa-list-alt:before{content:"\\f022"}
        .fa-paperclip:before{content:"\\f0c6"}
        .fa-file-alt:before{content:"\\f15c"}
        .fa-archive:before{content:"\\f187"}
        .fa-download:before{content:"\\f019"}
        .fa-code-branch:before{content:"\\f126"}
        .fa-calendar:before{content:"\\f133"}
        """


    def _get_plotly_js(self):
        """Get Plotly.js as embedded string"""
        # Plotly.js CDN - using a specific version for stability
        return """
        <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
        """

    def _get_bootstrap_js(self):
        """Get Bootstrap JS as embedded string"""
        # Minimal Bootstrap JS for basic functionality
        return """
        // Bootstrap 5.3.0 - Minimal JS
        // Basic functionality without external dependencies
        console.log('Bootstrap JS loaded (minimal version)');
        """

    def _encode_image(self, image_path):
        """Encode image to base64 for embedding in HTML"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode()
        except:
            return ""

    def _get_result_color(self, result_name):
        """Get Bootstrap color class for result"""
        color_map = {
            "PASS": "success",
            "FAIL": "danger",
            "ERROR": "warning",
            "INFOONLY": "info",
            "SKIPPED": "secondary",
            "UNKNOWN": "secondary",
            "ABORTED": "dark"
        }
        return color_map.get(result_name, "secondary")


    def _generate_html_string(self, app):
        """Generate static HTML string for the report"""
        # Generate the report content as static HTML instead of using Dash
        colormap = {
            "PASS": "limegreen",
            "FAIL": "tomato",
            "INFOONLY": "cornflowerblue",
            "SKIPPED": "silver",
            "UNKNOWN": "dimgray",
            "ERROR": "orange",
            "ABORTED": "magenta"
        }

        tests_results = [t.to_dict() for t in self.run.test_results]
        # Process results and preserve PlotData for numeric2d results
        numeric2d_plots = []
        for result in tests_results:
            # Convert time to relative format
            result['Time'] = str(timedelta(seconds=(result['Time'] - self.run.start_date).seconds))

            # Preserve PlotData for numeric2d results and collect for plotting
            if 'PlotData' in result and result.get('ResultType') == 'numeric2d':
                plot_data = result['PlotData']
                if plot_data and 'points' in plot_data:
                    numeric2d_plots.append({
                        'name': result['Name'],
                        'data': plot_data
                    })
            else:
                # Remove PlotData for non-numeric2d results
                if 'PlotData' in result:
                    del result['PlotData']

        duration = str(timedelta(seconds=(self.run.end_date - self.run.start_date).seconds))
        num_tests = len(self.run.test_results)

        # Generate result stats
        stats_count = Counter([t.result.name for t in self.run.test_results])

        # Create Plotly chart data
        stats_res = list(stats_count.keys())
        stats_cnt = list(stats_count.values())
        stats_color = [colormap[s] for s in stats_res]

        # Generate table HTML (includes inline plots for numeric2d results)
        table_html = self._generate_table_html(tests_results, colormap, numeric2d_plots)

        # Get proper color for overall result
        overall_result_color = self._get_overall_result_color(self.run.result.name)

        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Test Report - {self.run.tester}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <!-- Embedded Dependencies for Offline Viewing -->
    {self._get_plotly_js()}
    <style>{self._get_bootstrap_css()}</style>
    <style>{self._get_fontawesome_css()}</style>
    <style>
        :root {{
            --tester-primary: #1e3a8a;
            --tester-secondary: #3b82f6;
            --tester-accent: #06b6d4;
            --tester-success: #10b981;
            --tester-warning: #f59e0b;
            --tester-danger: #ef4444;
            --tester-info: #6366f1;
            --tester-light: #f8fafc;
            --tester-dark: #1e293b;
            --tester-gray: #64748b;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            color: var(--tester-dark);
            line-height: 1.6;
        }}

        .main-container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}

        .header-section {{
            background: linear-gradient(135deg, var(--tester-primary) 0%, var(--tester-secondary) 100%);
            color: white;
            border-radius: 16px;
            padding: 1.5rem 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 20px 40px rgba(30, 58, 138, 0.15);
            position: relative;
            overflow: hidden;
        }}

        .header-section::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 50%, rgba(255,255,255,0.05) 100%);
            animation: subtle-shimmer 8s ease-in-out infinite;
        }}

        @keyframes subtle-shimmer {{
            0%, 100% {{ opacity: 0.3; }}
            50% {{ opacity: 0.6; }}
        }}

        .header-content {{
            position: relative;
            z-index: 2;
        }}

        .logo {{
            height: 60px;
            filter: brightness(0) invert(1);
            margin-right: 1.5rem;
        }}

        .report-title {{
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .report-subtitle {{
            font-size: 1rem;
            opacity: 0.9;
            font-weight: 300;
            margin-bottom: 0;
        }}

        .header-main {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1rem;
        }}

        .header-left {{
            display: flex;
            align-items: center;
        }}

        .header-right {{
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 0.25rem;
        }}

        .version-info {{
            display: flex;
            gap: 2rem;
            font-size: 0.9rem;
            opacity: 0.9;
        }}

        .version-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .info-card {{
            background: white;
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.08);
            border: 1px solid rgba(0,0,0,0.05);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}

        .info-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.12);
        }}

        .info-card h3 {{
            color: var(--tester-primary);
            font-weight: 600;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .info-card h3 i {{
            color: var(--tester-accent);
        }}

        .info-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 0;
            border-bottom: 1px solid #f1f5f9;
        }}

        .info-item:last-child {{
            border-bottom: none;
        }}

        .info-label {{
            font-weight: 600;
            color: var(--tester-gray);
        }}

        .info-value {{
            color: var(--tester-dark);
            font-weight: 500;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}

        .stat-card {{
            background: white;
            border-radius: 16px;
            padding: 2rem;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.08);
            border: 1px solid rgba(0,0,0,0.05);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            position: relative;
            overflow: hidden;
        }}

        .stat-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--card-color, var(--tester-primary));
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.12);
        }}

        .stat-number {{
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--card-color, var(--tester-primary));
            margin-bottom: 0.5rem;
        }}

        .stat-label {{
            color: var(--tester-gray);
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-size: 0.9rem;
        }}


        .plots-container {{
            background: white;
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.08);
            border: 1px solid rgba(0,0,0,0.05);
            overflow: hidden;
        }}

        .plots-title {{
            color: var(--tester-primary);
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .plot-item {{
            margin-bottom: 2rem;
        }}

        .plot-item:last-child {{
            margin-bottom: 0;
        }}

        .plot-row {{
            background-color: #f8fafc;
            border-top: none;
        }}

        .plot-row td {{
            padding: 1rem;
            border-top: none;
        }}

        .inline-plot {{
            background: white;
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border: 1px solid #e2e8f0;
        }}

        .table-container {{
            background: white;
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.08);
            border: 1px solid rgba(0,0,0,0.05);
            overflow: hidden;
        }}

        .table-title {{
            color: var(--tester-primary);
            font-weight: 600;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .table {{
            margin-bottom: 0;
        }}

        .table thead th {{
            background: var(--tester-primary);
            color: white;
            border: none;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-size: 0.9rem;
            padding: 1rem;
        }}

        .table tbody td {{
            padding: 1rem;
            border-color: #f1f5f9;
            vertical-align: middle;
        }}

        .table tbody tr:hover {{
            background-color: #f8fafc;
        }}

        .status-badge {{
            padding: 0.5rem 1rem;
            border-radius: 50px;
            font-weight: 600;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .status-pass {{ background-color: var(--tester-success); color: white; }}
        .status-fail {{ background-color: var(--tester-danger); color: white; }}
        .status-error {{ background-color: var(--tester-warning); color: white; }}
        .status-info {{ background-color: var(--tester-info); color: white; }}
        .status-skipped {{ background-color: var(--tester-gray); color: white; }}
        .status-unknown {{ background-color: #6b7280; color: white; }}
        .status-aborted {{ background-color: #dc2626; color: white; }}

        .attachments-container {{
            background: white;
            border-radius: 16px;
            padding: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.08);
            border: 1px solid rgba(0,0,0,0.05);
        }}

        .attachments-title {{
            color: var(--tester-primary);
            font-weight: 600;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .btn-download {{
            background: linear-gradient(135deg, var(--tester-primary) 0%, var(--tester-secondary) 100%);
            border: none;
            border-radius: 50px;
            padding: 0.75rem 2rem;
            color: white;
            font-weight: 600;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}

        .btn-download:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(30, 58, 138, 0.3);
            color: white;
        }}

        .modifications-list {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}

        .modification-item {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1rem;
            transition: all 0.3s ease;
        }}

        .modification-item:hover {{
            background: #f1f5f9;
            border-color: var(--tester-accent);
        }}

        .modification-header {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.5rem;
        }}

        .modification-action {{
            margin-left: auto;
            font-weight: 600;
            font-size: 0.9rem;
        }}

        .modification-details {{
            margin-left: 2rem;
        }}

        .badge {{
            padding: 0.25rem 0.5rem;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .badge-setup {{
            background-color: var(--tester-info);
            color: white;
        }}

        .badge-testcase {{
            background-color: var(--tester-primary);
            color: white;
        }}

        .badge-cleanup {{
            background-color: var(--tester-warning);
            color: white;
        }}

        .dut-image {{
            width: 100%;
            max-width: 100%;
            height: auto;
            object-fit: contain;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            display: block;
            margin: 0 auto;
        }}

        @media (max-width: 768px) {{
            .main-container {{
                padding: 1rem;
            }}

            .header-section {{
                padding: 1rem;
            }}

            .header-main {{
                flex-direction: column;
                align-items: flex-start;
                gap: 1rem;
            }}

            .header-right {{
                align-items: flex-start;
                width: 100%;
            }}

            .version-info {{
                flex-direction: column;
                gap: 0.5rem;
                width: 100%;
            }}

            .report-title {{
                font-size: 1.5rem;
            }}

            .logo {{
                height: 50px;
                margin-right: 1rem;
            }}

            .stats-grid {{
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 1rem;
            }}

            .stat-card {{
                padding: 1.5rem;
            }}

            .stat-number {{
                font-size: 2rem;
            }}
        }}

        /* Program Attributes Styles */
        .attr-header {{
            background-color: var(--tester-light);
            color: var(--tester-dark);
            font-weight: 600;
            border-bottom: 2px solid var(--tester-primary);
            padding: 0.75rem;
        }}

        .attr-key {{
            font-weight: 600;
            color: var(--tester-primary);
            background-color: rgba(30, 58, 138, 0.05);
            border-right: 1px solid var(--tester-light);
            padding: 0.75rem;
            width: 30%;
        }}

        .attr-value {{
            color: var(--tester-dark);
            padding: 0.75rem;
            word-break: break-word;
            font-family: 'Courier New', monospace;
            background-color: rgba(248, 250, 252, 0.5);
        }}

        .table.table-striped tbody tr:nth-of-type(odd) .attr-key {{
            background-color: rgba(30, 58, 138, 0.08);
        }}

        .table.table-striped tbody tr:nth-of-type(odd) .attr-value {{
            background-color: rgba(248, 250, 252, 0.8);
        }}
    </style>
</head>
<body>
    <div class="main-container">
        <!-- Header Section -->
        <div class="header-section">
            <div class="header-content">
                <div class="header-main">
                    <div class="header-left">
                        <img src="data:image/png;base64,{self._encode_image(TestReport.LOGO_PATH)}" class="logo">
                        <div>
                            <h1 class="report-title">{self.run.tester}</h1>
                            <p class="report-subtitle">Test Execution Report</p>
                        </div>
                    </div>
                    <div class="header-right">
                        <div class="version-info">
                            <div class="version-item">
                                <i class="fas fa-code-branch"></i>
                                <span><strong>Framework:</strong> {version('tester')}</span>
                            </div>
                            <div class="version-item">
                                <i class="fas fa-tools"></i>
                                <span><strong>Tester:</strong> {self.run.tester_ver if self.run.tester_ver else 'N/A'}</span>
                            </div>
                            <div class="version-item">
                                <i class="fas fa-calendar"></i>
                                <span><strong>Generated:</strong> {self.run.end_date.strftime('%B %d, %Y at %H:%M')}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Test Overview Stats -->
        <div class="stats-grid">
            <div class="stat-card" style="--card-color: {overall_result_color}">
                <div class="stat-number">{self.run.result.name}</div>
                <div class="stat-label">Overall Result</div>
            </div>
            <div class="stat-card" style="--card-color: var(--tester-info)">
                <div class="stat-number">{num_tests}</div>
                <div class="stat-label">Tests Executed</div>
            </div>
            <div class="stat-card" style="--card-color: var(--tester-success)">
                <div class="stat-number">{stats_count.get("PASS", 0)}</div>
                <div class="stat-label">Passed</div>
            </div>
            <div class="stat-card" style="--card-color: var(--tester-danger)">
                <div class="stat-number">{stats_count.get("FAIL", 0)}</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat-card" style="--card-color: var(--tester-warning)">
                <div class="stat-number">{stats_count.get("ERROR", 0)}</div>
                <div class="stat-label">Errors</div>
            </div>
            <div class="stat-card" style="--card-color: var(--tester-accent)">
                <div class="stat-number">{duration}</div>
                <div class="stat-label">Duration</div>
            </div>
        </div>

        <!-- DUT and Program Information -->
        <div class="row">
            <div class="col-lg-8">
                <div class="info-card">
                    <h3><i class="fas fa-microchip"></i> Device Under Test</h3>
                    <div class="info-item">
                        <span class="info-label">Name</span>
                        <span class="info-value">{self.run.dut}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Description</span>
                        <span class="info-value">{self.run.dut_desc}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Product ID</span>
                        <span class="info-value">{self.run.dut_product_id}</span>
                    </div>
                </div>
            </div>
            <div class="col-lg-4">
                <div class="info-card text-center">
                    <img src="data:image/png;base64,{self._encode_image(self.run.dut_image if os.path.isfile(self.run.dut_image) else TestReport.DUT_IMAGE_PATH)}" class="dut-image">
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-12">
                <div class="info-card">
                    <h3><i class="fas fa-play-circle"></i> Test Program
                        {self._get_program_modification_indicator()}
                    </h3>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="info-item">
                                <span class="info-label">Program Name</span>
                                <span class="info-value">{self.run.program}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Description</span>
                                <span class="info-value">{self.run.program_desc}</span>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="info-item">
                                <span class="info-label">Start Time</span>
                                <span class="info-value">{self.run.start_date.strftime('%H:%M:%S')} {self.run.start_date.strftime('%d/%m/%Y')}</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">Duration</span>
                                <span class="info-value">{self._format_duration(self.run.start_date, self.run.end_date)}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Program Attributes -->
        {self._generate_program_attributes_html()}

        <!-- Test Results Table -->
        <div class="table-container">
            <h3 class="table-title"><i class="fas fa-list-alt"></i> Detailed Test Results</h3>
            {table_html}
        </div>

        <!-- Attachments -->
        <div class="attachments-container">
            <h3 class="attachments-title"><i class="fas fa-paperclip"></i> Attachments</h3>
            {self._generate_attachments_html()}
        </div>
    </div>


    <script>{self._get_bootstrap_js()}</script>
</body>
</html>
        """
