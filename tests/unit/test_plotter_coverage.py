from oure.risk.plotter import RiskPlotter


def test_risk_plotter_bplane(tmp_path):
    event_data = {
        "primary_id": "1",
        "secondary_id": "2",
        "pc": 1e-4,
        "miss_distance_km": 0.5,
        "hard_body_radius_m": 20.0,
        "sigma_bplane_km": [1.0, 2.0],
    }
    out_path = tmp_path / "plot.html"
    RiskPlotter.plot_bplane_from_json(event_data, out_path)
    assert out_path.exists()
