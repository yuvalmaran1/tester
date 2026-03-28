import os
from importlib.metadata import version
import plotly.graph_objects as go
import plotly.offline
from collections import Counter
from .TestRun import TestRun
import pathlib
from datetime import timedelta
import tempfile
import base64


class TestReport:
    LOGO_PATH = pathlib.Path(__file__).parent.resolve().joinpath('Assets').joinpath('tester.png')
    DUT_IMAGE_PATH = pathlib.Path(__file__).parent.resolve().joinpath('Assets').joinpath('dut.png')

    # Inline SVG logo — chip/IC with test waveform, indigo gradient
    LOGO_SVG = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none"'
        ' class="logo" aria-hidden="true">'
        '<defs>'
        '<linearGradient id="rpt_bg" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0%" stop-color="#6366f1"/>'
        '<stop offset="100%" stop-color="#4338ca"/>'
        '</linearGradient>'
        '<linearGradient id="rpt_wave" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0%" stop-color="#a5b4fc"/>'
        '<stop offset="100%" stop-color="#e0e7ff"/>'
        '</linearGradient>'
        '</defs>'
        '<rect x="14" y="14" width="36" height="36" rx="5" fill="url(#rpt_bg)"/>'
        '<rect x="20" y="20" width="24" height="24" rx="2" fill="#0d1117" opacity="0.5"/>'
        '<rect x="6"  y="21" width="8" height="3" rx="1.5" fill="#818cf8"/>'
        '<rect x="6"  y="28" width="8" height="3" rx="1.5" fill="#818cf8"/>'
        '<rect x="6"  y="35" width="8" height="3" rx="1.5" fill="#818cf8"/>'
        '<rect x="6"  y="42" width="8" height="3" rx="1.5" fill="#818cf8"/>'
        '<rect x="50" y="21" width="8" height="3" rx="1.5" fill="#818cf8"/>'
        '<rect x="50" y="28" width="8" height="3" rx="1.5" fill="#818cf8"/>'
        '<rect x="50" y="35" width="8" height="3" rx="1.5" fill="#818cf8"/>'
        '<rect x="50" y="42" width="8" height="3" rx="1.5" fill="#818cf8"/>'
        '<rect x="21" y="6"  width="3" height="8" rx="1.5" fill="#818cf8"/>'
        '<rect x="28" y="6"  width="3" height="8" rx="1.5" fill="#818cf8"/>'
        '<rect x="35" y="6"  width="3" height="8" rx="1.5" fill="#818cf8"/>'
        '<rect x="42" y="6"  width="3" height="8" rx="1.5" fill="#818cf8"/>'
        '<rect x="21" y="50" width="3" height="8" rx="1.5" fill="#818cf8"/>'
        '<rect x="28" y="50" width="3" height="8" rx="1.5" fill="#818cf8"/>'
        '<rect x="35" y="50" width="3" height="8" rx="1.5" fill="#818cf8"/>'
        '<rect x="42" y="50" width="3" height="8" rx="1.5" fill="#818cf8"/>'
        '<polyline points="22,32 24,32 25,26 27,38 29,26 31,38 33,26 35,38 36,32 42,32"'
        ' stroke="url(#rpt_wave)" stroke-width="2"'
        ' stroke-linecap="round" stroke-linejoin="round"/>'
        '</svg>'
    )

    # Same SVG as base64 data URI for the tab favicon
    _FAVICON_B64 = None  # lazily computed

    # Dark colour palette — mirrors the frontend
    RESULT_COLORS = {
        'PASS':     {'color': '#10b981', 'bg': 'rgba(16,185,129,0.15)',   'border': 'rgba(16,185,129,0.3)'},
        'FAIL':     {'color': '#ef4444', 'bg': 'rgba(239,68,68,0.15)',    'border': 'rgba(239,68,68,0.3)'},
        'ERROR':    {'color': '#f59e0b', 'bg': 'rgba(245,158,11,0.15)',   'border': 'rgba(245,158,11,0.3)'},
        'INFOONLY': {'color': '#60a5fa', 'bg': 'rgba(96,165,250,0.15)',   'border': 'rgba(96,165,250,0.3)'},
        'SKIPPED':  {'color': '#64748b', 'bg': 'rgba(100,116,139,0.15)', 'border': 'rgba(100,116,139,0.3)'},
        'ABORTED':  {'color': '#a78bfa', 'bg': 'rgba(167,139,250,0.15)', 'border': 'rgba(167,139,250,0.3)'},
        'UNKNOWN':  {'color': '#64748b', 'bg': 'rgba(100,116,139,0.15)', 'border': 'rgba(100,116,139,0.3)'},
    }
    DEFAULT_PALETTE = {'color': '#818cf8', 'bg': 'rgba(129,140,248,0.15)', 'border': 'rgba(129,140,248,0.3)'}

    def __init__(self, run: TestRun, path: str = None) -> None:
        self.run = run
        self.path = path

    def generate(self) -> str:
        html_content = self._generate_html_string(None)
        if self.path:
            with open(self.path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        return html_content

    # ------------------------------------------------------------------ helpers

    def _get_result_palette(self, result_name):
        return self.RESULT_COLORS.get(result_name, self.DEFAULT_PALETTE)

    def _dark_plot_layout(self, height=380):
        return dict(
            template='plotly_dark',
            paper_bgcolor='#161b2e',
            plot_bgcolor='#0d1117',
            font=dict(color='#94a3b8', size=11),
            height=height,
            margin=dict(l=64, r=32, t=36, b=64),
            showlegend=True,
            legend=dict(
                orientation='h', yanchor='bottom', y=1.02,
                xanchor='right', x=1,
                bgcolor='rgba(0,0,0,0)',
                font=dict(color='#94a3b8'),
            ),
        )

    def _scatter_trace(self, x, y, name, color, dash=None, fill=None, fillcolor=None, marker_size=4):
        line = dict(color=color, width=2)
        if dash:
            line['dash'] = dash
        kw = dict(x=x, y=y, mode='lines+markers', name=name, line=line,
                  marker=dict(size=marker_size, color=color))
        if dash:
            kw['mode'] = 'lines'
        if fill:
            kw['fill'] = fill
            kw['fillcolor'] = fillcolor
        return go.Scatter(**kw)

    def _axis_style(self, title, standoff=10):
        return dict(title=title, title_standoff=standoff,
                    gridcolor='#1e2d40', zerolinecolor='#2d3748')

    # --------------------------------------------------------------- plot HTML

    def _generate_numeric2d_plots_html(self, numeric2d_plots):
        if not numeric2d_plots:
            return ''

        html = '<div class="card"><div class="card-title">2D Test Results</div>'
        for plot in numeric2d_plots:
            plot_data = plot['data']
            plot_name = plot['name']
            points = plot_data.get('points', [])
            if not points:
                continue

            x = [p['x'] for p in points]
            y = [p['value'] for p in points]
            lo = [p.get('min') for p in points]
            hi = [p.get('max') for p in points]

            fig = go.Figure()
            if any(lo) and any(hi):
                fig.add_trace(self._scatter_trace(x, lo, 'Min', '#818cf8', dash='dash'))
                fig.add_trace(self._scatter_trace(x, hi, 'Max', '#ef4444', dash='dash',
                                                  fill='tonexty', fillcolor='rgba(99,102,241,0.06)'))
            fig.add_trace(self._scatter_trace(x, y, 'Measured', '#10b981'))

            fig.update_layout(
                **self._dark_plot_layout(380),
                title=dict(text=plot_name, font=dict(color='#e2e8f0', size=13)),
                xaxis=self._axis_style(plot_data.get('xlabel', 'X')),
                yaxis=self._axis_style(plot_data.get('ylabel', 'Y')),
            )
            div_id = f'plot_{plot_name.replace(" ", "_")}'
            html += f'<div style="margin-bottom:1.5rem">{fig.to_html(include_plotlyjs=False, div_id=div_id)}</div>'

        html += '</div>'
        return html

    def _generate_single_plot_html(self, plot_name, plot_data):
        points = plot_data.get('points', [])
        if not points:
            return ''

        x = [p['x'] for p in points]
        y = [p['value'] for p in points]
        lo = [p.get('min') for p in points]
        hi = [p.get('max') for p in points]

        fig = go.Figure()
        if any(lo) and any(hi):
            fig.add_trace(self._scatter_trace(x, lo, 'Min', '#818cf8', dash='dash'))
            fig.add_trace(self._scatter_trace(x, hi, 'Max', '#ef4444', dash='dash',
                                              fill='tonexty', fillcolor='rgba(99,102,241,0.06)'))
        fig.add_trace(self._scatter_trace(x, y, 'Measured', '#10b981', marker_size=3))

        fig.update_layout(
            **self._dark_plot_layout(260),
            xaxis=self._axis_style(plot_data.get('xlabel', 'X'), 8),
            yaxis=self._axis_style(plot_data.get('ylabel', 'Y'), 8),
        )
        div_id = f'inline_{plot_name.replace(" ", "_")}'
        return f'<div style="padding:.75rem;background:#0d1117">{fig.to_html(include_plotlyjs=False, div_id=div_id)}</div>'

    # --------------------------------------------------------------- table HTML

    def _generate_table_html(self, tests_results, colormap=None, numeric2d_plots=None):
        if not tests_results:
            return '<p style="color:#64748b;padding:1rem">No test results available</p>'

        CENTER_COLS = {'Time', 'Suite', 'Min', 'Value', 'Max', 'Unit', 'Result'}
        MONO_COLS   = {'Time', 'Min', 'Value', 'Max'}
        SKIP_COLS   = {'PlotData', 'ResultType', 'X_Unit'}

        columns = [c for c in tests_results[0].keys() if c not in SKIP_COLS]

        html = '<div class="table-wrapper"><table><thead><tr>'
        for col in columns:
            cls = ' class="text-center"' if col in CENTER_COLS else ''
            html += f'<th{cls}>{col}</th>'
        html += '</tr></thead><tbody>'

        for result in tests_results:
            is_numeric2d = result.get('ResultType') == 'numeric2d' and 'PlotData' in result
            html += '<tr>'
            for col in columns:
                classes = []
                if col in CENTER_COLS:
                    classes.append('text-center')
                if col in MONO_COLS:
                    classes.append('text-mono')
                cls = f' class="{" ".join(classes)}"' if classes else ''

                if col == 'Result':
                    val = result[col]
                    p = self._get_result_palette(val)
                    html += (f'<td class="text-center"><span class="badge" '
                             f'style="color:{p["color"]};background:{p["bg"]};border:1px solid {p["border"]}">'
                             f'{val}</span></td>')
                else:
                    html += f'<td{cls}>{result.get(col, "")}</td>'
            html += '</tr>'

            if is_numeric2d:
                plot_data = result.get('PlotData')
                if plot_data and 'points' in plot_data:
                    plot_html = self._generate_single_plot_html(result['Name'], plot_data)
                    html += f'<tr class="plot-row"><td colspan="{len(columns)}">{plot_html}</td></tr>'

        html += '</tbody></table></div>'
        return html

    # ----------------------------------------------------------- attachments

    def _generate_attachments_html(self):
        dl_svg = ('<svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">'
                  '<path d="M5 20h14v-2H5zM19 9h-4V3H9v6H5l7 7z"/></svg>')
        html = ''

        temp_dir = tempfile.TemporaryDirectory()
        log_filename = os.path.join(temp_dir.name, 'tester.log')
        with open(log_filename, 'w') as f:
            f.writelines(self.run.log)
        with open(log_filename, 'r') as f:
            log_b64 = base64.b64encode(f.read().encode()).decode()
        html += (f'<a href="data:text/plain;base64,{log_b64}" download="tester.log" '
                 f'class="btn-download">{dl_svg} tester.log</a>')

        if self.run.attachment_exists():
            attach_filename = os.path.join(temp_dir.name, 'attachments.zip')
            with open(attach_filename, 'wb') as f:
                f.write(self.run.get_attachment())
            with open(attach_filename, 'rb') as f:
                attach_b64 = base64.b64encode(f.read()).decode()
            html += (f'<a href="data:application/zip;base64,{attach_b64}" download="attachments.zip" '
                     f'class="btn-download">{dl_svg} attachments.zip</a>')

        return html

    # ------------------------------------------------------- program sections

    def _get_program_modification_indicator(self):
        if not hasattr(self.run, 'program_modified') or not self.run.program_modified:
            return ''
        return '<span class="modified-badge">Modified</span>'

    def _generate_program_attributes_html(self):
        if not hasattr(self.run, 'program_attr') or not self.run.program_attr:
            return ''

        rows = ''.join(f'<tr><td>{k}</td><td>{v}</td></tr>'
                       for k, v in self.run.program_attr.items())
        return (
            '<div class="card">'
            '<div class="card-title">Program Attributes</div>'
            '<div class="table-wrapper">'
            '<table class="attr-table">'
            '<thead><tr><th>Attribute</th><th>Value</th></tr></thead>'
            f'<tbody>{rows}</tbody>'
            '</table></div></div>'
        )

    # --------------------------------------------------------------- utilities

    def _format_duration(self, start_date, end_date):
        if not start_date or not end_date:
            return '--:--:--'
        try:
            s = (end_date - start_date).total_seconds()
            if s < 0:
                return '--:--:--'
            return f'{int(s // 3600):02d}:{int((s % 3600) // 60):02d}:{int(s % 60):02d}'
        except Exception:
            return '--:--:--'

    def _get_overall_result_color(self, result_name):
        return self._get_result_palette(result_name)['color']

    def _encode_image(self, image_path):
        try:
            with open(image_path, 'rb') as f:
                return base64.b64encode(f.read()).decode()
        except Exception:
            return ''

    def _get_result_color(self, result_name):
        return self._get_result_palette(result_name)['color']

    # ------------------------------------------------------------------ CSS

    @staticmethod
    def _get_css():
        # Plain string — no f-string escaping needed for CSS braces.
        return """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
     background:#0d1117;color:#e2e8f0;line-height:1.6;font-size:15px}
a{color:#818cf8;text-decoration:none}

/* ── Header ── */
.header{background:linear-gradient(135deg,#161b2e 0%,#1a1f3a 100%);
        border-bottom:1px solid #2d3748;padding:1.25rem 2rem}
.header-inner{max-width:1400px;margin:0 auto;display:flex;align-items:center;
              justify-content:space-between;flex-wrap:wrap;gap:1rem}
.header-brand{display:flex;align-items:center;gap:1rem}
.logo{height:44px;width:44px;flex-shrink:0}
.header-title h1{font-size:1.375rem;font-weight:700;color:#e2e8f0;letter-spacing:-0.01em}
.header-title p{font-size:.8125rem;color:#64748b;margin-top:2px}
.header-meta{display:flex;gap:2rem;flex-wrap:wrap}
.meta-item{font-size:.8rem;color:#64748b;line-height:1.5}
.meta-item strong{color:#a5b4fc;font-weight:600;display:block}

/* ── Container ── */
.container{max-width:1400px;margin:0 auto;padding:1.75rem 2rem}

/* ── Card ── */
.card{background:#161b2e;border:1px solid #2d3748;border-radius:10px;
      padding:1.5rem;margin-bottom:1.5rem}
.card-title{font-size:.72rem;font-weight:700;text-transform:uppercase;
            letter-spacing:.08em;color:#6366f1;margin-bottom:1.25rem}

/* ── Stats ── */
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(148px,1fr));
            gap:1rem;margin-bottom:1.5rem}
.stat-card{background:#161b2e;border:1px solid #2d3748;
           border-left:3px solid var(--accent,#6366f1);
           border-radius:8px;padding:1.25rem;text-align:center}
.stat-number{font-size:1.625rem;font-weight:700;
             color:var(--accent,#6366f1);line-height:1.2;
             word-break:break-word}
.stat-label{font-size:.6875rem;font-weight:600;text-transform:uppercase;
            letter-spacing:.07em;color:#64748b;margin-top:.375rem}

/* ── Two-col ── */
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-bottom:1.5rem}

/* ── Info items ── */
.info-item{display:flex;justify-content:space-between;align-items:flex-start;
           padding:.5625rem 0;border-bottom:1px solid rgba(45,55,72,.6);
           font-size:.875rem;gap:1rem}
.info-item:last-child{border-bottom:none}
.info-label{color:#64748b;font-weight:500;flex-shrink:0}
.info-value{color:#cbd5e1;font-weight:500;text-align:right}

/* ── DUT image ── */
.dut-layout{display:flex;gap:1.5rem;align-items:flex-start}
.dut-info{flex:1;min-width:0}
.dut-image{width:110px;height:110px;object-fit:contain;border-radius:8px;
           border:1px solid #2d3748;background:#0d1117;display:block;flex-shrink:0}

/* ── Table ── */
.table-wrapper{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:.8375rem}
thead th{background:#1a2035;color:#818cf8;font-weight:600;text-transform:uppercase;
         letter-spacing:.06em;font-size:.7rem;padding:.875rem 1rem;
         text-align:left;border-bottom:2px solid #2d3748;white-space:nowrap}
tbody td{padding:.6875rem 1rem;border-bottom:1px solid rgba(45,55,72,.5);
         color:#cbd5e1;vertical-align:middle}
tbody tr:hover td{background:rgba(99,102,241,.04)}
.text-center{text-align:center!important}
.text-mono{font-family:'Courier New',monospace;font-size:.8rem}
.plot-row td{background:#0d1117!important;padding:0!important;
             border-bottom:1px solid rgba(45,55,72,.5)}

/* ── Badge ── */
.badge{display:inline-block;padding:.2rem .625rem;border-radius:9999px;
       font-size:.7rem;font-weight:700;text-transform:uppercase;
       letter-spacing:.05em}

/* ── Download buttons ── */
.btn-download{display:inline-flex;align-items:center;gap:.5rem;
              padding:.5rem 1rem;background:#1a2035;
              border:1px solid rgba(99,102,241,.4);border-radius:7px;
              color:#818cf8;font-size:.8375rem;font-weight:600;
              margin:.25rem .5rem .25rem 0;
              transition:background .15s,color .15s}
.btn-download:hover{background:rgba(99,102,241,.15);color:#a5b4fc}

/* ── Attributes table ── */
.attr-table{width:100%;border-collapse:collapse;font-size:.8375rem}
.attr-table thead th{background:#1a2035;color:#818cf8;font-weight:600;
                     font-size:.7rem;text-transform:uppercase;
                     letter-spacing:.06em;padding:.75rem 1rem;
                     border-bottom:2px solid #2d3748;text-align:left}
.attr-table td{padding:.5625rem 1rem;border-bottom:1px solid rgba(45,55,72,.5);
               vertical-align:top}
.attr-table td:first-child{color:#818cf8;font-weight:600;
                           width:30%;white-space:nowrap}
.attr-table td:last-child{font-family:monospace;color:#cbd5e1;word-break:break-all}

/* ── Modified indicator ── */
.modified-badge{display:inline-flex;align-items:center;gap:.25rem;
                padding:.15rem .5rem;border-radius:4px;
                background:rgba(245,158,11,.12);color:#f59e0b;
                border:1px solid rgba(245,158,11,.3);
                font-size:.7rem;font-weight:700;margin-left:.5rem;
                vertical-align:middle;text-transform:uppercase;
                letter-spacing:.04em}

/* ── Responsive ── */
@media(max-width:900px){
  .two-col{grid-template-columns:1fr}
}
@media(max-width:768px){
  .header{padding:1rem}
  .container{padding:1rem}
  .header-meta{gap:1rem}
  .stats-grid{grid-template-columns:repeat(2,1fr)}
  .dut-layout{flex-direction:column}
  .dut-image{width:100%;height:auto;max-height:140px}
}
"""

    # --------------------------------------------------------------- main HTML

    def _generate_html_string(self, app):
        # ---- Process test results ----
        tests_results = [t.to_dict() for t in self.run.test_results]
        numeric2d_plots = []
        for result in tests_results:
            result['Time'] = str(timedelta(seconds=(result['Time'] - self.run.start_date).seconds))
            if 'PlotData' in result and result.get('ResultType') == 'numeric2d':
                plot_data = result['PlotData']
                if plot_data and 'points' in plot_data:
                    numeric2d_plots.append({'name': result['Name'], 'data': plot_data})
            else:
                result.pop('PlotData', None)

        duration  = self._format_duration(self.run.start_date, self.run.end_date)
        num_tests = len(self.run.test_results)
        stats_count   = Counter([t.result.name for t in self.run.test_results])
        overall_color = self._get_overall_result_color(self.run.result.name)

        # ---- Sub-sections ----
        table_html       = self._generate_table_html(tests_results, numeric2d_plots=numeric2d_plots)
        attrs_html       = self._generate_program_attributes_html()
        attachments_html = self._generate_attachments_html()
        modified_ind     = self._get_program_modification_indicator()

        # ---- Logo (inline SVG — no file dependency) ----
        logo_html = TestReport.LOGO_SVG

        dut_img_path = self.run.dut_image if os.path.isfile(self.run.dut_image) else TestReport.DUT_IMAGE_PATH
        dut_b64 = self._encode_image(dut_img_path)
        dut_img_html = (f'<img src="data:image/png;base64,{dut_b64}" class="dut-image" alt="DUT">'
                        if dut_b64 else '')

        # ---- Framework version ----
        try:
            fw_ver = version('tester')
        except Exception:
            fw_ver = 'N/A'

        tester_ver = self.run.tester_ver if self.run.tester_ver else 'N/A'
        generated  = self.run.end_date.strftime('%d %b %Y, %H:%M')
        serial_number = getattr(self.run, 'serial_number', '') or '—'
        config_hash = getattr(self.run, 'config_hash', '') or '—'
        config_hash_display = (config_hash[:16] + '…') if len(config_hash) > 16 else config_hash

        # ---- Stats cards ----
        stat_items = [
            (self.run.result.name, 'Overall Result', overall_color),
            (num_tests,                     'Tests Executed', '#818cf8'),
            (stats_count.get('PASS',  0),   'Passed',         '#10b981'),
            (stats_count.get('FAIL',  0),   'Failed',         '#ef4444'),
            (stats_count.get('ERROR', 0),   'Errors',         '#f59e0b'),
            (duration,                       'Duration',       '#06b6d4'),
        ]
        stats_html = ''.join(
            f'<div class="stat-card" style="--accent:{color}">'
            f'<div class="stat-number">{val}</div>'
            f'<div class="stat-label">{label}</div></div>'
            for val, label, color in stat_items
        )

        tester_name  = self.run.tester
        program_name = self.run.program
        program_desc = self.run.program_desc
        dut_name     = self.run.dut
        dut_desc     = self.run.dut_desc
        dut_pid      = self.run.dut_product_id
        start_str    = self.run.start_date.strftime('%H:%M:%S  %d/%m/%Y')
        dur_str      = self._format_duration(self.run.start_date, self.run.end_date)
        operator_str = getattr(self.run, 'operator', '') or '—'

        css = self._get_css()

        # ---- Assemble HTML (split around plotly_js to avoid f-string brace conflicts) ----
        # Favicon: inline SVG as base64 data URI so it works in the standalone file
        svg_bytes = TestReport.LOGO_SVG.encode('utf-8')
        favicon_b64 = base64.b64encode(svg_bytes).decode()
        favicon_link = f'<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,{favicon_b64}">'

        head = (
            f'<!DOCTYPE html>\n'
            f'<html lang="en">\n'
            f'<head>\n'
            f'<title>Test Report \u2014 {tester_name}</title>\n'
            f'<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'{favicon_link}\n'
            f'<script>'
        )

        rest = (
            f'</script>\n'
            f'<style>{css}</style>\n'
            f'</head>\n'
            f'<body>\n'

            # ── Header ──
            f'<div class="header"><div class="header-inner">'
            f'<div class="header-brand">'
            f'{logo_html}'
            f'<div class="header-title">'
            f'<h1>{tester_name}</h1>'
            f'<p>Test Execution Report</p>'
            f'</div></div>'
            f'<div class="header-meta">'
            f'<div class="meta-item"><strong>Framework</strong>{fw_ver}</div>'
            f'<div class="meta-item"><strong>Tester</strong>{tester_ver}</div>'
            f'<div class="meta-item"><strong>Generated</strong>{generated}</div>'
            f'</div>'
            f'</div></div>\n'

            # ── Body ──
            f'<div class="container">\n'

            # Stats
            f'<div class="stats-grid">{stats_html}</div>\n'

            # DUT + Program
            f'<div class="two-col">'

            # DUT card
            f'<div class="card" style="margin-bottom:0">'
            f'<div class="card-title">Device Under Test</div>'
            f'<div class="dut-layout">'
            f'<div class="dut-info">'
            f'<div class="info-item"><span class="info-label">Name</span>'
            f'<span class="info-value">{dut_name}</span></div>'
            f'<div class="info-item"><span class="info-label">Description</span>'
            f'<span class="info-value">{dut_desc}</span></div>'
            f'<div class="info-item"><span class="info-label">Product ID</span>'
            f'<span class="info-value">{dut_pid}</span></div>'
            f'<div class="info-item"><span class="info-label">Serial Number</span>'
            f'<span class="info-value text-mono">{serial_number}</span></div>'
            f'</div>'
            f'{dut_img_html}'
            f'</div></div>'

            # Program card
            f'<div class="card" style="margin-bottom:0">'
            f'<div class="card-title">Test Program {modified_ind}</div>'
            f'<div class="info-item"><span class="info-label">Program</span>'
            f'<span class="info-value">{program_name}</span></div>'
            f'<div class="info-item"><span class="info-label">Description</span>'
            f'<span class="info-value">{program_desc}</span></div>'
            f'<div class="info-item"><span class="info-label">Start Time</span>'
            f'<span class="info-value text-mono">{start_str}</span></div>'
            f'<div class="info-item"><span class="info-label">Duration</span>'
            f'<span class="info-value text-mono">{dur_str}</span></div>'
            f'<div class="info-item"><span class="info-label">Operator</span>'
            f'<span class="info-value">{operator_str}</span></div>'
            f'<div class="info-item"><span class="info-label">Config Hash</span>'
            f'<span class="info-value text-mono" style="font-size:0.75rem">{config_hash_display}</span></div>'
            f'</div>'

            f'</div>\n'  # end .two-col

            # Attributes
            f'{attrs_html}\n'

            # Results table
            f'<div class="card">'
            f'<div class="card-title">Detailed Test Results</div>'
            f'{table_html}'
            f'</div>\n'


            # Attachments
            f'<div class="card">'
            f'<div class="card-title">Attachments</div>'
            f'{attachments_html}'
            f'</div>\n'

            f'</div>\n'  # end .container
            f'</body>\n'
            f'</html>'
        )

        plotly_js = plotly.offline.get_plotlyjs()
        return head + plotly_js + rest
