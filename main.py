
from dataclasses import dataclass, field
from bakery import assert_equal
import time
import os
import json
from drafter import *
import matplotlib.pyplot as plt
import numpy as np
import random

set_website_title("Arduino Distance Logger")

set_site_information(
    author="Sachchit Shankar",
    description="An Arduino Distance Logger that collects distance readings, analyzes data, and displays graphs.",
    sources="Drafter, NumPy, and Matplotlib documentation.",
    planning=[
        "CS1 Final Project 0_ Pick a Problem (1).pdf",
        "_CS1 Final Project 1_ Design.pdf"
    ],
    links=[
        "https://github.com/sachmarine/arduino-distance-logger"
    ]
)

hide_debug_information()
set_website_framed(False)


"""This program generates simulated distance measurements,
converts them into numerical data, and uses NumPy and Matplotlib
to calculate and plot a Distance vs Time graph."""


@dataclass
class SensorReading:
    timestamp: float
    distance: float


@dataclass
class State:
    duration: float = 5.0
    status_message: str = "Ready to collect data."
    readings: list = field(default_factory=list)
    graph_path: str = ""
    show_data_log: bool = True
    graph_style: str = "Scatter"


def calculate_linear_regression(
    time_arr: list[float], dist_arr: list[float]
) -> tuple[float, float]:
    """Calculate the line of best fit using NumPy linear regression."""

    t = np.array(time_arr)
    d = np.array(dist_arr)

    valid = (d >= 5) & (d <= 100)

    t = t[valid]
    d = d[valid]

    if len(t) < 2:
        raise ValueError(
            "At least two valid measurements are required."
        )

    m, b = np.polyfit(t, d, 1)

    return m, b


# LOAD THE LATEST UPLOADED SESSION

def latest_session_content():

    try:
        with open("latest_data.json", "r", encoding="utf-8") as file:
            data = json.load(file)

        content = [
            Header("Latest Arduino Session", level=2),

            Paragraph(f"Collected: {data['collected_at']}"),

            Paragraph(
                f"Duration: {data['duration_seconds']} seconds"
            ),

            Paragraph(
                f"Measurements: {len(data['readings'])}"
            ),

            Image(Picture.from_file("latest_graph.png")),

            Header("Recorded Data Log", level=3)
        ]

        for reading in data["readings"]:

            content.append(
                Paragraph(
                    f"Time: {reading['timestamp']}s | "
                    f"Distance: {reading['distance']:.2f} cm"
                )
            )

        return content

    except (OSError, ValueError, KeyError, TypeError):

        return [
            Header("Latest Arduino Session", level=2),
            Paragraph("No uploaded session is available yet.")
        ]


@route("/")
def index(state: State) -> Page:

    """Display the homepage and links to other pages."""

    return Page(
        state,
        [
            Header("Arduino Distance Logger", level=1),

            Paragraph(
                "Welcome to the sensor telemetry dashboard."
            ),

            *latest_session_content(),

            Link("Configure Session", "/config"),
            Link("View History", "/history"),
            Link("About This Project", "/about"),
            Link("Reset Application", "/reset"),
        ],
    )


@route("/config")
def config_page(state: State) -> Page:

    """Allow the user to choose the collection duration and graph style."""

    return Page(
        state,
        [
            Header("Session Setup", level=1),

            Paragraph("Enter the duration in seconds:"),

            TextBox("duration", str(state.duration)),

            Paragraph("Display recorded data log?"),

            CheckBox(
                "show_data_log",
                state.show_data_log
            ),

            Paragraph("Choose graph style:"),

            SelectBox(
                "graph_style",
                ["Scatter", "Line"],
                state.graph_style
            ),

            Button("Run Logger", "/run"),

            Link("Back To Home", "/"),
        ],
    )


@route("/run")
def run_logger(
    state: State,
    duration: str,
    show_data_log: bool,
    graph_style: str
) -> Page:

    """Generate simulated measurements for the selected duration."""

    try:
        state.duration = float(duration)

    except (ValueError, TypeError):
        state.duration = 5.0

    if state.duration <= 0:
        state.duration = 5.0

    state.show_data_log = show_data_log
    state.graph_style = graph_style

    time_array = []
    distances = []

    state.readings = []

    start_time = time.time()

    # COLLECT SIMULATED MEASUREMENTS

    while time.time() - start_time < state.duration:

        remaining_time = (
            state.duration - (time.time() - start_time)
        )

        time.sleep(min(1.0, remaining_time))

        elapsed_time = time.time() - start_time

        distance = random.randint(10, 100)

        time_array.append(elapsed_time)
        distances.append(float(distance))

    # STORE MEASUREMENTS IN STATE

    for t, d in zip(time_array, distances):

        state.readings.append(
            SensorReading(
                timestamp=round(t, 2),
                distance=d
            )
        )

    # CALCULATE LINE OF BEST FIT

    m, b = calculate_linear_regression(
        time_array,
        distances
    )

    predicted_line = []

    for t in time_array:

        predicted_line.append(m * t + b)

    # CREATE GRAPH

    plt.figure()

    if state.graph_style == "Scatter":

        plt.scatter(
            time_array,
            distances,
            color="blue",
            label="Simulated Data"
        )

    else:

        plt.plot(
            time_array,
            distances,
            color="blue",
            marker="o",
            label="Simulated Data"
        )

    plt.plot(
        time_array,
        predicted_line,
        color="red",
        linestyle="--",
        label=f"y = {m:.2f}x + {b:.2f}"
    )

    plt.xlabel("Time (s)")
    plt.ylabel("Distance (cm)")

    plt.title("Simulated Distance Measurements")

    plt.legend()

    state.graph_path = "graph.png"

    plt.savefig(state.graph_path)

    plt.close()

    # UPDATE STATUS

    state.status_message = (
        f"Collected {len(state.readings)} simulated points "
        f"over approximately {state.duration} seconds. "
        "These are fabricated measurements."
    )

    return results_page(state)


@route("/results")
def results_page(state: State) -> Page:

    """Show the graph and recorded simulated measurements."""

    reading_paragraphs = []

    if state.show_data_log:

        for reading in state.readings:

            text = (
                f"Time: {reading.timestamp}s | "
                f"Distance: {reading.distance:.2f} cm"
            )

            reading_paragraphs.append(
                Paragraph(text)
            )

    if state.graph_path and os.path.exists(state.graph_path):

        show_picture = Image(
            Picture.from_file(state.graph_path)
        )

    else:

        show_picture = "❌"

    return Page(
        state,
        [
            Header("Results & Graph", level=1),

            Paragraph("SIMULATED DATA"),

            Paragraph(state.status_message),

            show_picture,

            *(
                [Header("Recorded Data Log", level=2)]
                + reading_paragraphs
                if state.show_data_log
                else []
            ),

            Link("Run Again", "/config"),
            Link("Home", "/"),
        ],
    )


# HISTORY PAGE

@route("/history")
def history_page(state: State) -> Page:

    """Show how many sensor readings have been collected."""

    return Page(
        state,
        [
            Header("History", level=1),

            Paragraph(
                f"Total readings currently in state: "
                f"{len(state.readings)}\n"
                "If you want to go back to 0, reset the application..."
            ),

            Link("Home", "/"),
        ],
    )


# ABOUT PAGE

@route("/about")
def about_page(state: State) -> Page:

    """Explain the project and how the measurements are analyzed."""

    return Page(
        state,
        [
            Header("About This Project", level=1),

            Paragraph(
                "A project demonstrating distance measurements from an "
                "ultrasonic sensor. This version uses simulated measurements "
                "to demonstrate the data collection and analysis process. "
                "The duration of data collection is dependent on the user's "
                "input. This project uses NumPy to calculate the line of "
                "best fit and Matplotlib to visually represent the graph."
            ),

            Link("Home", "/"),
        ],
    )


# RESET PAGE

@route("/reset")
def reset_state(state: State) -> Page:

    """Reset application settings and clear collected data."""

    state.duration = 5.0
    state.status_message = "Reset."
    state.readings = []
    state.graph_path = ""
    state.show_data_log = True
    state.graph_style = "Scatter"

    return index(state)


# START THE PROGRAM

if __name__ == "__main__":
    start_server(State())


# TESTS

assert_equal(
    calculate_linear_regression([1, 2, 3], [10, 20, 30]),
    (10.0, 0.0)
)

assert_equal(
    calculate_linear_regression([1, 2, 3], [3, 5, 7]),
    (2.0, 1.0)
)

assert_equal(
    calculate_linear_regression([1, 2, 3], [5, 5, 5]),
    (0.0, 5.0)
)

assert_equal(index(State()).state, State())
assert_equal(config_page(State()).state, State())
assert_equal(history_page(State()).state, State())
assert_equal(about_page(State()).state, State())

test_state = State(
    duration=10.0,
    status_message="Testing",
    graph_path="graph.png",
    show_data_log=False,
    graph_style="Line"
)

reset_state(test_state)

assert_equal(test_state.duration, 5.0)
assert_equal(test_state.status_message, "Reset.")
assert_equal(test_state.readings, [])
assert_equal(test_state.graph_path, "")
assert_equal(test_state.show_data_log, True)
assert_equal(test_state.graph_style, "Scatter")

assert_equal(
    results_page(State(
        graph_path="graph.png",
        show_data_log=True
    )).state.show_data_log,
    True
)

assert_equal(
    results_page(State(
        graph_path="graph.png",
        show_data_log=False
    )).state.show_data_log,
    False
)
