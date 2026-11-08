import threading
import time

from tester.TestUtil import TestDialog as Dialog


def test_non_blocking_dialog_stays_open_after_response():
    dialog = Dialog()
    dialog.close()
    dialog.display_non_blocking(title="Manual step", responses=[Dialog.Response.Ok])

    dialog.submit_response({"rsp": "Ok"}, {"confirmed": True})

    assert dialog.show is True
    assert dialog.wait_for_response(timeout=0) == {"rsp": "Ok"}
    assert dialog.response_data == {"confirmed": True}
    dialog.close()


def test_non_blocking_dialog_can_update_progress_and_close():
    dialog = Dialog()
    dialog.display_non_blocking(title="Manual step")

    dialog.update(text="Running measurement", progress=45)

    state = dialog.encode()
    assert state["show"] is True
    assert state["text"] == "Running measurement"
    assert state["progress"] == 45

    dialog.close()
    assert dialog.encode()["show"] is False


def test_blocking_dialog_remains_compatible():
    dialog = Dialog()

    responder = threading.Thread(
        target=lambda: (time.sleep(0.01), dialog.submit_response({"rsp": "Yes"}, {}))
    )
    responder.start()
    response = dialog.display(responses=[Dialog.Response.Yes], timeout=1)
    responder.join()

    assert response == {"rsp": "Yes"}
    assert dialog.show is False


def test_dialog_encodes_markdown_file_and_local_images(tmp_path):
    image = tmp_path / "fixture.png"
    image.write_bytes(b"png content")
    markdown = tmp_path / "instructions.md"
    markdown.write_text(
        "# Connect fixture\n\n![Fixture](fixture.png)",
        encoding="utf-8",
    )

    dialog = Dialog().display_non_blocking(markdown_file=markdown)
    state = dialog.encode()

    assert state["markdown"] == "# Connect fixture\n\n![Fixture](fixture.png)"
    assert state["markdown_images"]["fixture.png"].startswith("data:image/png;base64,")
    dialog.close()


def test_non_blocking_dialog_can_update_markdown_file(tmp_path):
    markdown = tmp_path / "complete.md"
    markdown.write_text("## Programming complete", encoding="utf-8")
    dialog = Dialog().display_non_blocking(text="Programming...")

    dialog.update(markdown_file=markdown, progress=100)

    assert dialog.encode()["markdown"] == "## Programming complete"
    dialog.close()


def test_dialog_rejects_non_markdown_file(tmp_path):
    text_file = tmp_path / "instructions.txt"
    text_file.write_text("Not Markdown", encoding="utf-8")

    try:
        Dialog().display_non_blocking(markdown_file=text_file)
    except ValueError as error:
        assert str(error) == "markdown_file must reference a .md file"
    else:
        raise AssertionError("Expected a ValueError for a non-Markdown file")