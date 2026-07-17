import numpy as np


def visualize_conjunction(
    path1: np.ndarray,
    path2: np.ndarray,
    id1: str,
    id2: str,
    filename: str = "conjunction_view.html",
) -> None:
    try:
        import plotly.graph_objects as go
    except ImportError:
        print("Please install plotly to use visualization features.")
        return

    fig = go.Figure()

    # Earth Sphere (Radius ~ 6371 km)
    R_earth = 6371.0
    u, v = np.mgrid[0 : 2 * np.pi : 50j, 0 : np.pi : 25j]
    x = R_earth * np.cos(u) * np.sin(v)
    y = R_earth * np.sin(u) * np.sin(v)
    z = R_earth * np.cos(v)

    fig.add_trace(
        go.Surface(
            x=x,
            y=y,
            z=z,
            colorscale="Blues",
            opacity=0.3,
            showscale=False,
            name="Earth",
        )
    )

    # Satellite 1 Path
    fig.add_trace(
        go.Scatter3d(
            x=path1[:, 0],
            y=path1[:, 1],
            z=path1[:, 2],
            mode="lines+markers",
            marker=dict(size=3, color="red"),
            line=dict(color="red", width=2),
            name=f"Sat {id1}",
        )
    )

    # Satellite 2 Path
    fig.add_trace(
        go.Scatter3d(
            x=path2[:, 0],
            y=path2[:, 1],
            z=path2[:, 2],
            mode="lines+markers",
            marker=dict(size=3, color="orange"),
            line=dict(color="orange", width=2),
            name=f"Sat {id2}",
        )
    )

    fig.update_layout(
        title="OURE Conjunction View",
        scene=dict(xaxis_title="X (km)", yaxis_title="Y (km)", zaxis_title="Z (km)"),
        margin=dict(l=0, r=0, b=0, t=40),
    )

    fig.write_html(filename)
    print(f"Visualization saved to {filename}")
