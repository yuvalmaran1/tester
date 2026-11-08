from tester.TestConfig import TestConfig as Config
from tester.TestReport import TestReport as Report
from tester.TestResults.PassFailTestResult import PassFailTestResult
from tester.TestResults.Numeric2dTestResult import Numeric2dTestResult
from tester.TestRun import TestRun as Run


def test_generate_pdf_returns_valid_pdf_document():
    run = Run(
        tester={"name": "Tester", "version": "1.0"},
        dut={"name": "DUT", "description": "", "product_id": "P1", "image": ""},
        program={"name": "Program", "description": "", "attr": {"mode": "production"}},
    )
    run.serial_number = "SN-001"
    run.config_hash = "abc123"
    run.start()
    result = PassFailTestResult(
        Config(name="Functional test", attr={}, tolerance={}),
        True,
        suite="Functional",
    )
    run.append_result(result)
    run.end()

    pdf = Report(run).generate_pdf()

    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 1000
    assert b"BitstreamVeraSans" in pdf


def test_html_embeds_the_same_vera_font_family_as_pdf():
    css = Report._get_css()

    assert "font-family:'Vera Sans'" in css
    assert css.count("data:font/ttf;base64,") == 2


def test_pdf_dut_image_preserves_aspect_ratio():
    image = Report._pdf_image(Report.DUT_IMAGE_PATH, max_width=72, max_height=72)

    assert image is not None
    assert image.drawWidth == image.drawHeight == 72


def test_pdf_dut_image_ignores_missing_file():
    assert Report._pdf_image("missing-dut-image.png", 72, 72) is None


def test_pdf_display_value_formats_measurements_concisely():
    assert Report._pdf_display_value("3.2775975168935814") == "3.2776"
    assert Report._pdf_display_value(121.40080803951177) == "121.401"
    assert Report._pdf_display_value("2.1.4") == "2.1.4"
    assert Report._pdf_display_value("") == ""


def test_pdf_safe_text_removes_orphan_leading_combining_mark():
    assert Report._pdf_safe_text("\u05b2°C") == "°C"
    assert Report._pdf_safe_text("café") == "café"


def test_generate_pdf_includes_numeric2d_plot():
    run = Run(
        tester={"name": "Tester", "version": "1.0"},
        dut={"name": "DUT", "description": "", "product_id": "P1", "image": ""},
        program={"name": "Program", "description": "", "attr": {}},
    )
    run.start()
    result = Numeric2dTestResult(
        Config(
            name="Voltage sweep",
            attr={},
            tolerance={"min": 0.0, "max": 2.0},
            unit="V",
            x_unit="s",
        ),
        {"x": [0, 1, 2], "y": [0.5, 1.0, 1.5]},
        suite="Sweep",
    )
    run.append_result(result)
    run.end()

    drawing = Report._pdf_plot_drawing(result.plot_data, result.result.name)
    pdf = Report(run).generate_pdf()

    assert len(drawing.contents) > 20
    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 3000