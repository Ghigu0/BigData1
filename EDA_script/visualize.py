import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, LogNorm


# =========================================================
# EDA PLOTS FOR THE REPORT
# =========================================================
# One pass over the CSV (in chunks, like the other EDA scripts).
# Per-trip numbers are cheap (point count = number of "[" - 1), so
# they are computed on every row. GPS points have to be parsed with
# json, so only a sample of trips (1 every SAMPLE_EVERY) is kept for
# the maps.
#
# Output: PNG files in EDA_script/figures/

HERE = os.path.dirname(os.path.abspath(__file__))
FILE_NAME = os.path.join(HERE, "..", "porto", "porto.csv")
OUT_DIR = os.path.join(HERE, "figures")
CHUNK_SIZE = 100000
SAMPLE_EVERY = 50

CITY_HALL = (41.15794, -8.62911)  # (latitude, longitude), same as query 6

# Box around Porto used for the maps (drops GPS outliers far away)
LAT_RANGE = (41.05, 41.30)
LON_RANGE = (-8.75, -8.45)

# Colors
BLUE = "#2a78d6"
ORANGE = "#eb6834"
TEXT = "#0b0b0b"
TEXT_MUTED = "#52514e"
GRID = "#e4e3df"
BLUE_RAMP = LinearSegmentedColormap.from_list("blue_ramp", [
    "#cde2fb", "#86b6ef", "#3987e5", "#256abf", "#184f95", "#0d366b"
])

CALL_TYPE_NAMES = {"A": "A - dispatched", "B": "B - taxi stand", "C": "C - street"}


def setup_style():
    plt.rcParams.update({
        "figure.dpi": 150,
        "font.size": 10,
        "axes.edgecolor": GRID,
        "axes.labelcolor": TEXT_MUTED,
        "axes.titlecolor": TEXT,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "xtick.color": TEXT_MUTED,
        "ytick.color": TEXT_MUTED,
    })


# =========================================================
# READ THE CSV
# =========================================================

def read_dataset():
    call_type_counts = {}
    taxi_trip_counts = {}
    point_counts = []
    hours = []
    months = []
    sample_points = []  # (longitude, latitude, call_type, progress in the trip)

    row_number = 0

    for chunk in pd.read_csv(
        FILE_NAME,
        chunksize=CHUNK_SIZE,
        usecols=["CALL_TYPE", "TAXI_ID", "TIMESTAMP", "POLYLINE"],
    ):
        for value, count in chunk["CALL_TYPE"].value_counts().items():
            call_type_counts[value] = call_type_counts.get(value, 0) + count

        for taxi_id, count in chunk["TAXI_ID"].value_counts().items():
            taxi_trip_counts[taxi_id] = taxi_trip_counts.get(taxi_id, 0) + count

        # "[]" -> 0 points, "[[x,y]]" -> 1 point, ...
        point_counts.append(chunk["POLYLINE"].str.count(r"\[").to_numpy() - 1)

        # Porto local time, same as populate (Europe/Lisbon)
        start_time = pd.to_datetime(chunk["TIMESTAMP"], unit="s", utc=True).dt.tz_convert("Europe/Lisbon")
        hours.append(start_time.dt.hour.to_numpy())
        months.append(start_time.dt.strftime("%Y-%m").to_numpy())

        # The chunk index is the row number in the whole file
        sample = chunk[chunk.index % SAMPLE_EVERY == 0]
        for polyline, call_type in zip(sample["POLYLINE"], sample["CALL_TYPE"]):
            points = json.loads(polyline)
            for index, (longitude, latitude) in enumerate(points):
                progress = index / (len(points) - 1) if len(points) > 1 else 0.0
                sample_points.append((longitude, latitude, call_type, progress))

        row_number += len(chunk)
        print("Rows read:", row_number)

    points = pd.DataFrame(sample_points, columns=["lon", "lat", "call_type", "progress"])

    return {
        "call_type_counts": call_type_counts,
        "taxi_trip_counts": np.array(list(taxi_trip_counts.values())),
        "point_counts": np.concatenate(point_counts),
        "hours": np.concatenate(hours),
        "months": np.concatenate(months),
        "points": points,
    }


def in_porto(points):
    return points[
        points["lat"].between(*LAT_RANGE)
        & points["lon"].between(*LON_RANGE)
    ]


# =========================================================
# PLOTS
# =========================================================

def save(fig, name):
    path = os.path.join(OUT_DIR, name)
    fig.tight_layout()
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    print("Saved:", path)


def label_bars(ax, bars, values, fmt="{:,}"):
    for bar, value in zip(bars, values):
        ax.annotate(
            fmt.format(value),
            (bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 3), textcoords="offset points",
            ha="center", va="bottom", color=TEXT, fontsize=9,
        )


def plot_call_type(data):
    keys = sorted(data["call_type_counts"])
    values = [data["call_type_counts"][k] for k in keys]

    fig, ax = plt.subplots(figsize=(6, 3.8))
    bars = ax.bar([CALL_TYPE_NAMES.get(k, k) for k in keys], values, color=BLUE, width=0.6)
    label_bars(ax, bars, values)
    ax.set_title("Trips per call type")
    ax.set_ylabel("Trips")
    ax.grid(axis="x", visible=False)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v / 1000:,.0f}k"))
    save(fig, "trips_per_call_type.png")


def plot_points_per_trip(data):
    counts = data["point_counts"]
    max_shown = 400  # ~100 minutes, the long tail is cut

    fig, ax = plt.subplots(figsize=(7, 3.8))
    ax.hist(np.clip(counts, 0, max_shown), bins=np.arange(0, max_shown + 2), color=BLUE)
    ax.set_yscale("log")
    ax.axvline(3, color=TEXT_MUTED, linestyle="--", linewidth=1)
    invalid = int((counts < 3).sum())
    ax.annotate(
        f"< 3 points (invalid): {invalid:,} trips",
        (3, 1), xycoords=("data", "axes fraction"),
        xytext=(12, -14), textcoords="offset points", color=TEXT, fontsize=9,
    )
    ax.set_ylim(top=ax.get_ylim()[1] * 4)  # room for the label above the bars
    ax.set_title("GPS points per trip (1 point every 15 s)")
    ax.set_xlabel(f"Points per trip (trips with more than {max_shown} are in the last bar)")
    ax.set_ylabel("Trips (log scale)")
    save(fig, "points_per_trip.png")


def plot_trips_per_taxi(data):
    fig, ax = plt.subplots(figsize=(7, 3.8))
    ax.hist(data["taxi_trip_counts"], bins=40, color=BLUE, edgecolor="white", linewidth=1)
    ax.set_title(f"Trips per taxi ({len(data['taxi_trip_counts'])} taxis)")
    ax.set_xlabel("Trips")
    ax.set_ylabel("Taxis")
    save(fig, "trips_per_taxi.png")


def plot_trips_per_hour(data):
    values = np.bincount(data["hours"], minlength=24)

    fig, ax = plt.subplots(figsize=(7, 3.8))
    ax.bar(np.arange(24), values, color=BLUE, width=0.8)
    ax.set_title("Trips per hour of the day (Porto local time)")
    ax.set_xlabel("Hour")
    ax.set_ylabel("Trips")
    ax.set_xticks(np.arange(0, 24, 2))
    ax.grid(axis="x", visible=False)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v / 1000:,.0f}k"))
    save(fig, "trips_per_hour.png")


def plot_trips_per_month(data):
    months, values = np.unique(data["months"], return_counts=True)

    fig, ax = plt.subplots(figsize=(7, 3.8))
    ax.bar(months, values, color=BLUE, width=0.7)
    ax.set_title("Trips per month")
    ax.set_ylabel("Trips")
    ax.grid(axis="x", visible=False)
    ax.tick_params(axis="x", rotation=45)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v / 1000:,.0f}k"))
    save(fig, "trips_per_month.png")


def plot_density_map(data):
    points = in_porto(data["points"])

    # 1 degree of longitude is shorter than 1 degree of latitude at 41° N:
    # the aspect ratio keeps the map from looking stretched.
    fig, ax = plt.subplots(figsize=(7, 6.5))
    hb = ax.hexbin(
        points["lon"], points["lat"], gridsize=250, cmap=BLUE_RAMP,
        norm=LogNorm(), mincnt=1, linewidths=0,
    )
    ax.set_aspect(1 / np.cos(np.radians(41.15)))
    ax.grid(False)
    ax.plot(CITY_HALL[1], CITY_HALL[0], "o", color=ORANGE, markersize=7,
            markeredgecolor="white", markeredgewidth=1.5)
    ax.annotate("City Hall (query 6)", (CITY_HALL[1], CITY_HALL[0]),
                xytext=(8, 8), textcoords="offset points", color=TEXT, fontsize=9)
    fig.colorbar(hb, ax=ax, label="GPS points (log scale)", shrink=0.8)
    ax.set_title(f"GPS points around Porto (1 trip every {SAMPLE_EVERY})")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    save(fig, "gps_density_map.png")


def plot_start_points(data):
    # First point of every sampled trip, one panel per call type:
    # A/C start anywhere, B starts at the taxi stands.
    points = in_porto(data["points"])
    starts = points[points["progress"] == 0]
    keys = sorted(starts["call_type"].unique())

    fig, axes = plt.subplots(1, len(keys), figsize=(4 * len(keys), 4.4), sharex=True, sharey=True)
    for ax, key in zip(np.atleast_1d(axes), keys):
        subset = starts[starts["call_type"] == key]
        ax.scatter(subset["lon"], subset["lat"], s=1, color=BLUE, alpha=0.3, linewidths=0)
        ax.set_aspect(1 / np.cos(np.radians(41.15)))
        ax.set_xlim(-8.70, -8.55)
        ax.set_ylim(41.10, 41.20)
        ax.set_title(CALL_TYPE_NAMES.get(key, key), fontsize=10)
        ax.tick_params(labelsize=7)
    fig.suptitle("Where trips start, by call type", x=0.01, ha="left", fontweight="bold", color=TEXT)
    save(fig, "start_points_by_call_type.png")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    setup_style()

    data = read_dataset()

    plot_call_type(data)
    plot_points_per_trip(data)
    plot_trips_per_taxi(data)
    plot_trips_per_hour(data)
    plot_trips_per_month(data)
    plot_density_map(data)
    plot_start_points(data)


if __name__ == "__main__":
    main()
