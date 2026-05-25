from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import numpy as np

from oure.data.ndm_parser import NDMParser


def test_parse_oem():
    with patch("ccsds_ndm.from_file") as mock_from_file:
        from ccsds_ndm import Oem

        mock_msg = MagicMock(spec=Oem)
        mock_segment = MagicMock()
        mock_segment.metadata.object_id = "25544"
        mock_segment.metadata.object_name = "ISS"

        mock_state = MagicMock()
        mock_state.epoch = "2025-05-09T12:00:00Z"
        mock_state.x = 7000.0
        mock_state.y = 0.0
        mock_state.z = 0.0
        mock_state.x_dot = 0.0
        mock_state.y_dot = 7.5
        mock_state.z_dot = 0.0

        mock_segment.data.state_vector = [mock_state]
        mock_msg.segments = [mock_segment]

        mock_from_file.return_value = mock_msg

        states = NDMParser.parse_oem("dummy.oem")
        assert len(states) == 1
        state = states[0]
        assert state.sat_id == "25544"
        assert np.array_equal(state.r, np.array([7000.0, 0.0, 0.0]))
        assert np.array_equal(state.v, np.array([0.0, 7.5, 0.0]))
        assert state.epoch == datetime(2025, 5, 9, 12, 0, tzinfo=UTC)


def test_parse_opm():
    with patch("ccsds_ndm.from_file") as mock_from_file:
        from ccsds_ndm import Opm

        mock_msg = MagicMock(spec=Opm)
        mock_segment = MagicMock()
        mock_segment.metadata.object_id = "25544"

        mock_sv = MagicMock()
        mock_sv.epoch = "2025-05-09T12:00:00Z"
        mock_sv.x = 7000.0
        mock_sv.y = 0.0
        mock_sv.z = 0.0
        mock_sv.x_dot = 0.0
        mock_sv.y_dot = 7.5
        mock_sv.z_dot = 0.0
        mock_segment.data.state_vector = mock_sv

        mock_cov = MagicMock()
        mock_cov.CX_X = 1.0
        mock_cov.CY_X = 0.0
        mock_cov.CY_Y = 1.0
        mock_cov.CZ_X = 0.0
        mock_cov.CZ_Y = 0.0
        mock_cov.CZ_Z = 1.0
        mock_cov.CX_DOT_X = 0.0
        mock_cov.CX_DOT_Y = 0.0
        mock_cov.CX_DOT_Z = 0.0
        mock_cov.CX_DOT_X_DOT = 1e-4
        mock_cov.CY_DOT_X = 0.0
        mock_cov.CY_DOT_Y = 0.0
        mock_cov.CY_DOT_Z = 0.0
        mock_cov.CY_DOT_X_DOT = 0.0
        mock_cov.CY_DOT_Y_DOT = 1e-4
        mock_cov.CZ_DOT_X = 0.0
        mock_cov.CZ_DOT_Y = 0.0
        mock_cov.CZ_DOT_Z = 0.0
        mock_cov.CZ_DOT_X_DOT = 0.0
        mock_cov.CZ_DOT_Y_DOT = 0.0
        mock_cov.CZ_DOT_Z_DOT = 1e-4

        mock_segment.data.covariance_matrix = mock_cov
        mock_msg.segments = [mock_segment]

        mock_from_file.return_value = mock_msg

        state, cov = NDMParser.parse_opm("dummy.opm")
        assert state.sat_id == "25544"
        assert np.array_equal(state.r, np.array([7000.0, 0.0, 0.0]))
        assert cov is not None
        assert np.isclose(cov.matrix[0, 0], 1.0)
        assert np.isclose(cov.matrix[5, 5], 1e-4)
        assert cov.epoch == datetime(2025, 5, 9, 12, 0, tzinfo=UTC)
