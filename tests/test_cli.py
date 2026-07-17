import json
import os
import signal
import sys
from unittest.mock import patch

from cli.main import handle_sigint, main


def test_cli_propagate(capsys):
    test_args = [
        "cli",
        "propagate",
        "--input-file",
        "dummy.txt",
        "--days",
        "5",
        "--step-size",
        "60.0",
    ]
    with patch.object(sys, "argv", test_args):
        main()

    captured = capsys.readouterr()
    assert "Propagating dummy.txt for 5 days with step size 60.0" in captured.out


def test_cli_risk_check(capsys):
    test_args = [
        "cli",
        "risk-check",
        "--target-id",
        "12345",
        "--threshold",
        "10.0",
        "--output-json",
        "out.json",
    ]
    with patch.object(sys, "argv", test_args):
        main()

    captured = capsys.readouterr()
    assert "Risk check for 12345 with threshold 10.0 to out.json" in captured.out


def test_sigint_handler(capsys):
    if os.path.exists("recovery_state.json"):
        os.remove("recovery_state.json")

    try:
        handle_sigint(signal.SIGINT, None)
    except SystemExit as e:
        assert e.code == 0

    captured = capsys.readouterr()
    assert "Simulation paused and saved." in captured.out
    assert os.path.exists("recovery_state.json")

    with open("recovery_state.json", "r") as f:
        data = json.load(f)
        assert data["status"] == "paused"
