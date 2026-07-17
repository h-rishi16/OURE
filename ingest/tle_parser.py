import logging


def parse_tles(file_path):
    """
    Parses raw Two-Line Element (TLE) text files into structured Python dictionaries.
    Includes strict validation and SGP4 checksum validation.
    """
    parsed_tles = []

    # Setup logger to rejected_tles.log
    logger = logging.getLogger("tle_parser")
    logger.setLevel(logging.WARNING)
    fh = logging.FileHandler("rejected_tles.log")
    fh.setLevel(logging.WARNING)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)

    # Remove existing handlers to avoid duplicates in tests
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.addHandler(fh)

    def compute_checksum(line):
        """Computes the SGP4 checksum for a TLE line."""
        checksum = 0
        for char in line[:-1]:
            if char.isdigit():
                checksum += int(char)
            elif char == "-":
                checksum += 1
        return checksum % 10

    try:
        with open(file_path, "r") as f:
            lines = f.readlines()
    except Exception as e:
        logger.error(f"Failed to open file: {e}")
        return []

    i = 0
    while i < len(lines):
        line1 = lines[i].strip("\n\r")

        # If it's a title line, skip to next which should be line 1
        if len(line1) < 69 or not line1.startswith("1 "):
            i += 1
            continue

        if i + 1 >= len(lines):
            break

        line2 = lines[i + 1].strip("\n\r")

        # Validate length
        if len(line1) != 69:
            logger.warning(
                f"Line {i + 1} rejected: Length is {len(line1)}, expected 69"
            )
            i += 2
            continue

        if len(line2) != 69:
            logger.warning(
                f"Line {i + 2} rejected: Length is {len(line2)}, expected 69"
            )
            i += 2
            continue

        # Checksum validation
        try:
            expected_checksum1 = int(line1[68])
            # SGP4 checksum actually counts modulo 10
            # SGP4 validation:
            c1 = compute_checksum(line1)
            if c1 != expected_checksum1:
                logger.warning(
                    f"Line {i + 1} rejected: Invalid checksum. Expected {expected_checksum1}, got {c1}"
                )
                i += 2
                continue

            expected_checksum2 = int(line2[68])
            c2 = compute_checksum(line2)
            if c2 != expected_checksum2:
                logger.warning(
                    f"Line {i + 2} rejected: Invalid checksum. Expected {expected_checksum2}, got {c2}"
                )
                i += 2
                continue
        except ValueError:
            logger.warning("Line rejected: Checksum character is not a digit")
            i += 2
            continue

        # If we passed all checks, add to parsed
        parsed_tles.append(
            {"line1": line1, "line2": line2, "sat_id": line1[2:7].strip()}
        )
        i += 2

    return parsed_tles
