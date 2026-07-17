import os

import numpy as np

from oure.cli.visualizer import visualize_conjunction


def test_visualize_conjunction() -> None:
    if os.path.exists("test_conj.html"):
        os.remove("test_conj.html")

    path1 = np.array([[6771.0, 0, x * 10] for x in range(-5, 5)])
    path2 = np.array([[6771.0, x * 10, 0] for x in range(-5, 5)])

    visualize_conjunction(path1, path2, "SAT1", "SAT2", filename="test_conj.html")

    assert os.path.exists("test_conj.html")
    with open("test_conj.html", "r") as f:
        content = f.read()
        assert "plotly" in content
        assert "OURE Conjunction View" in content

    os.remove("test_conj.html")
