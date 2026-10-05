import numpy as np

from visualize import BLUE_RAMP, in_porto, read_dataset


# =========================================================
# 3D POINT CLOUD OF THE GPS POINTS (pptk)
# =========================================================
# Same approach as the pptk Geolife tutorial suggested by the professor:
#   - GPS points as a point cloud, z = 0, colored by a per-point attribute
#   - coordinates converted to meters (UTM) so the map is not stretched
#     (Porto is in UTM zone 29N, Beijing in the tutorial is in zone 50)
#
# Uses the same sample as visualize.py (1 trip every SAMPLE_EVERY).
#
# NB: pptk only has wheels for Python <= 3.7, e.g.
#   conda create -n pptk python=3.7 && conda activate pptk
#   pip install pptk pyproj pandas matplotlib
#
# Viewer (from the tutorial): 5 = orthographic view, 7 = top-down view,
# Shift + left mouse = pan, wheel = zoom, [ and ] = switch attribute.

CALL_TYPE_COLORS = {
    "A": (0x2a / 255, 0x78 / 255, 0xd6 / 255),  # blue
    "B": (0xeb / 255, 0x68 / 255, 0x34 / 255),  # orange
    "C": (0x1b / 255, 0xaf / 255, 0x7a / 255),  # aqua
}


def to_meters(longitude, latitude):
    try:
        import pyproj
        proj = pyproj.Proj(proj="utm", zone=29, ellps="WGS84")
        return proj(longitude.tolist(), latitude.tolist())

    except ImportError:
        # Without pyproj: local equirectangular projection around Porto,
        # good enough at city scale.
        print("pyproj not installed, using an approximate projection")
        earth_radius = 6371000
        lat0 = np.radians(41.15)
        x = earth_radius * np.radians(longitude) * np.cos(lat0)
        y = earth_radius * np.radians(latitude)
        return x, y


def main():
    import pptk

    points = in_porto(read_dataset()["points"])

    x, y = to_meters(points["lon"].to_numpy(), points["lat"].to_numpy())
    P = np.c_[x, y, np.zeros(len(points))]

    # Attribute 1: call type, as an RGB color per point
    call_type_rgb = np.array([CALL_TYPE_COLORS[c] for c in points["call_type"]])

    # Attribute 2: position in the trip, 0 = first point, 1 = last point
    progress = points["progress"].to_numpy()

    v = pptk.viewer(P)
    v.attributes(call_type_rgb, progress)
    v.color_map(BLUE_RAMP(np.linspace(0, 1, 256))[:, :3], scale=[0, 1])
    v.set(point_size=2)

    print("Attribute 1: call type (A blue, B orange, C aqua)")
    print("Attribute 2: position in the trip (light = start, dark = end)")
    print("Press ] / [ in the viewer to switch attribute")


if __name__ == "__main__":
    main()
