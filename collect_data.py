
import json
import time
from datetime import datetime
from pathlib import Path

import serial
import matplotlib.pyplot as plt


PORT = "COM5"
BAUD_RATE = 9600

DATA_FILE = Path("latest_data.json")
GRAPH_FILE = Path("latest_graph.png")


def collect_data(duration):
    time_array = []
    distances = []

    print(f"Connecting to Arduino on {PORT}...")

    with serial.Serial(PORT, BAUD_RATE, timeout=0.1) as arduino:
        time.sleep(2)
        arduino.reset_input_buffer()

        print("Connected! Collecting real measurements...")

        start_time = time.monotonic()
        next_sample = start_time

        latest_distance = None

        while time.monotonic() - start_time < duration:

            raw_data = arduino.readline()

            if raw_data:
                try:
                    value = float(raw_data.decode("utf-8").strip())

                    if 5 <= value <= 100:
                        latest_distance = value

                except ValueError:
                    continue

            current_time = time.monotonic()

            if current_time >= next_sample:
                if latest_distance is not None:
                    elapsed = round(current_time - start_time, 2)

                    time_array.append(elapsed)
                    distances.append(latest_distance)

                    print(
                        f"Time: {elapsed:.2f}s | "
                        f"Distance: {latest_distance:.2f} cm"
                    )

                next_sample += 1

    if len(distances) < 2:
        raise RuntimeError(
            "Not enough valid Arduino measurements. "
            "No files were updated."
        )

    return time_array, distances


def save_results(time_array, distances, duration):

    readings = []

    for t, d in zip(time_array, distances):
        readings.append({
            "timestamp": t,
            "distance": d
        })

    data = {
        "collected_at": datetime.now().astimezone().isoformat(),
        "port": PORT,
        "baud_rate": BAUD_RATE,
        "duration_seconds": duration,
        "readings": readings
    }

    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

    plt.figure(figsize=(9, 5))
    plt.scatter(time_array, distances, label="Arduino Data")

    plt.xlabel("Time (seconds)")
    plt.ylabel("Distance (cm)")
    plt.title("Arduino Distance Measurements")
    plt.legend()
    plt.grid(True)

    plt.savefig(GRAPH_FILE, dpi=150, bbox_inches="tight")
    plt.close()

    print("\nSession saved successfully!")
    print(f"Measurements: {len(readings)}")
    print(f"Data: {DATA_FILE}")
    print(f"Graph: {GRAPH_FILE}")


def main():

    try:
        duration = int(input("How many seconds should we collect data? "))

        if duration < 2:
            print("Please enter at least 2 seconds.")
            return

        time_array, distances = collect_data(duration)

        save_results(time_array, distances, duration)

    except serial.SerialException as error:
        print(f"\nArduino connection error: {error}")

    except KeyboardInterrupt:
        print("\nCollection interrupted.")

    except RuntimeError as error:
        print(f"\n{error}")


if __name__ == "__main__":
    main()
