from tester.TestConfig import TestConfig as Config
from tester.TestReport import TestReport as Report
from tester.TestResults.PassFailTestResult import PassFailTestResult
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