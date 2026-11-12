
# all my import statements

from dataclasses import dataclass, field
from bakery import assert_equal
import time
import os
import drafter
from drafter import *
import matplotlib.pyplot as plt
import numpy as np
import serial


"""This program essentially consumes telemetry data from an arduino in bytes,
converts it into numerical data, and uses the libraries of NumPy and MatPlotLib to plot a Distance vs Time array.
The arduino has an ultrasonic sensor wired to it,
that provides thousands of data points per second. The data is converted into arrays and then plotted."""


# defining dataclasses and drafter initialization

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


# Here we are calculating the line of BEST FIT using NumPy linear regression

def calculate_linear_regression(
    time_arr: list[float], dist_arr: list[float]
) -> tuple[float, float]:
    """Here we are calculating the line of BEST FIT using NumPy linear regression, using time and distance data"""


    t = np.array(time_arr)
    d = np.array(dist_arr)

    m, b = np.polyfit(t, d, 1)

    return m, b


# HOME PAGE

@route("/")
def index(state: State) -> Page:

    """This function essentially shows the home page and links to the other parts of the website."""

    return Page(
        state,
        [
            Header("Arduino Distance Logger", level=1),
            Paragraph("Welcome to the sensor telemetry dashboard."),

            Link("Configure Session", "/config"),
            Link("View History", "/history"),
            Link("About This Project", "/about"),
            Link("Reset Application", "/reset"),
        ],
    )


# CONFIGURATION PAGE

@route("/config")
def config_page(state: State) -> Page:
    """This page let's the user choose how long to collect data and to display it, using an input (duration)"""

    return Page(
        state,
        [
            Header("Session Setup", level=1),

            Paragraph("Enter the duration in seconds:"),
            TextBox("duration", str(state.duration)),

            Paragraph("Display recorded data log?"),
            CheckBox("show_data_log", state.show_data_log),

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


# DATA COLLECTION PAGE

@route("/run")
def run_logger(
    state: State,
    duration: str,
    show_data_log: bool,
    graph_style: str
) -> Page:

    """This route collects the sensor data, and then calculates the line of 
    best fit by calling the helper function calculate_linear_regression,
    then creates a graph"""

    state.duration = float(duration)
    state.show_data_log = show_data_log
    state.graph_style = graph_style

    # Make sure the duration is positive

    if state.duration <= 0:
        state.duration = 5.0

    start_time = float(time.time())

    # Try connecting to the Arduino

    try:
        arduino = serial.Serial("COM5", 9600)

    except Exception as error:
        arduino = None
        print("Arduino connection failed. Using simulation.")

    # Lists to store the data

    time_array = []
    distances = []

    # Check if the Arduino is connected

    if arduino is None or not arduino.is_open:

        # Simulation if Arduino is not connected

        time.sleep(1)

        for i in range(1, int(state.duration) + 1):

            time_array.append(float(i))
            distances.append(12.5 + (i * 1.8))

    else:

        # Collect data from the Arduino

        for i in range(1, int(state.duration) + 1):

            target_time = start_time + i

            while time.time() < target_time:
                time.sleep(0.01)

            raw_data = arduino.readline()

            if raw_data:

                try:
                    distance_str = raw_data.decode("utf-8").strip()

                    if distance_str:
                        distances.append(float(distance_str))
                        time_array.append(float(i))

                except ValueError:
                    continue

        arduino.close()

    # Make sure there are enough readings for a graph

    if len(distances) < 2:

        time_array = [1.0, 2.0, 3.0]
        distances = [10.0, 14.0, 18.0]

    # Store the readings

    state.readings = []

    for t, d in zip(time_array, distances):

        state.readings.append(
            SensorReading(timestamp=t, distance=d)
        )

    # Calculate the linear regression

    m, b = calculate_linear_regression(time_array, distances)

    predicted_line = []

    for t in time_array:
        predicted_line.append(m * t + b)

    # Create the graph

    plt.figure()

    if state.graph_style == "Scatter":

        plt.scatter(
            time_array,
            distances,
            color="blue",
            label="Data"
        )

    else:

        plt.plot(
            time_array,
            distances,
            color="blue",
            label="Data"
        )

    plt.plot(
        time_array,
        predicted_line,
        color="red",
        linestyle="--",
        label="Fit"
    )

    plt.xlabel("Time (s)")
    plt.ylabel("Distance (cm)")
    plt.legend()

    # Save the graph

    state.graph_path = "graph.png"
    print(os.getcwd())
    print(os.path.exists(state.graph_path))
    plt.savefig(state.graph_path)
    print(os.path.exists(state.graph_path))
    print(os.path.abspath(state.graph_path))
    print(os.listdir("."))
    plt.close()
    print("Graph saved successfully!")

    # Update the status message

    state.status_message = (
        f"Collected {len(state.readings)} points successfully!"
    )

    return results_page(state)


# RESULTS PAGE

@route("/results")
def results_page(state: State) -> Page:

    """Show the graph and the recorded sensor data."""
    reading_paragraphs = []

    if state.show_data_log:

        for reading in state.readings:

            text = (
                f"Time: {reading.timestamp}s | "
                f"Distance: {reading.distance:.2f} cm"
            )

            reading_paragraphs.append(Paragraph(text))

    return Page(
        state,
        [
            Header("Results & Graph", level=1),
            Paragraph(state.status_message),

            Image(Picture.from_file(state.graph_path)),

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

    """This shows how many sensor readings have been collected so far."""

    return Page(
        state,
        [
            Header("History", level=1),
            Paragraph(
                f"Total readings currently in state: {len(state.readings)} \n"
                "If you want to go back to 0, reset the application..."
            ),
            Link("Home", "/"),
        ],
    )


# ABOUT PAGE

@route("/about")
def about_page(state: State) -> Page:

    """This page explains what the project is about and how the sensor data is used."""

    return Page(
        state,
        [
            Header("About This Project", level=1),
            Paragraph(
    "A project using a real-life ultrasonic sensor hooked up to an "
    "arduino. The ultrasonic sensor reports thousands of data "
    "points per second, and the arduino converts those data points "
    "into bytes, which are later converted into numerical data in "
    "python. The duration that the arduino transmits data is solely "
    "dependent on the user's input. This project uses NumPy for "
    "plotting the line of best-fit, and MatPlotLib to visually "
    "represent the graph using linear regression."
),
            Link("Home", "/"),
        ],
    )


# RESET PAGE

@route("/reset")
def reset_state(state: State) -> Page:

    """This page allows the user to reset the settings and clear all of the collected data within state."""

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


assert_equal(calculate_linear_regression([1, 2, 3], [2, 4, 6]), (2.0, 0.0))

assert_equal(calculate_linear_regression([1, 2, 3], [3, 5, 7]), (2.0, 1.0))

assert_equal(calculate_linear_regression([1, 2, 3], [5, 5, 5]), (0.0, 5.0))

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

assert_equal(results_page(State(
    graph_path="graph.png",
    show_data_log=True
)).state.show_data_log, True)

assert_equal(results_page(State(
    graph_path="graph.png",
    show_data_log=False
)).state.show_data_log, False)
