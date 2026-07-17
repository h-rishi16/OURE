import os

from ingest.tle_parser import parse_tles


def test_tle_parser():
    valid_line1 = (
        "1 25544U 98067A   20316.40055110  .00001859  00000-0  42125-4 0  9999"
    )
    valid_line2 = (
        "2 25544  51.6433  47.4526 0001594 117.7550 338.4144 15.49502621254886"
    )

    # Invalid checksum
    invalid_checksum_line1 = (
        "1 25544U 98067A   20316.40055110  .00001859  00000-0  42125-4 0  9998"
    )
    invalid_checksum_line2 = valid_line2

    content = f"{valid_line1}\n{valid_line2}\n{invalid_checksum_line1}\n{invalid_checksum_line2}\n"

    with open("tests/mock_tle.txt", "w") as f:
        f.write(content)

    if os.path.exists("rejected_tles.log"):
        os.remove("rejected_tles.log")

    tles = parse_tles("tests/mock_tle.txt")

    assert len(tles) == 1
    assert tles[0]["sat_id"] == "25544"

    # Check that log was written
    assert os.path.exists("rejected_tles.log")
    with open("rejected_tles.log", "r") as f:
        log_content = f.read()
        assert "Invalid checksum" in log_content
