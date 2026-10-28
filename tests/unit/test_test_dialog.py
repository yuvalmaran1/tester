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