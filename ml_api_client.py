# ml_api_client.py
import json
import sqlite3
import datetime
import argparse
import sys  # NEW: Import sys for sys.exit()
import requests  # MOVED: requests import after standard library imports

# --- Configuration ---
ML_API_URL = "http://localhost:5000/predict"
SQLITE_DB_PATH = "data/build_history.db"  # Relative path within Jenkins workspace
# --- End Configuration ---


def create_db_and_table():
    """Creates the SQLite database and build_records table if they don't exist."""
    conn = None
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS build_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                build_number INTEGER NOT NULL,
                job_name TEXT NOT NULL,
                build_url TEXT NOT NULL,
                raw_features_json TEXT NOT NULL,
                raw_predictions_json TEXT NOT NULL
            );
            """
        )
        conn.commit()
        print(f"Database and table created/verified at {SQLITE_DB_PATH}")
    except sqlite3.Error as e:
        print(f"ERROR: Failed to create database or table: {e}")
    finally:
        if conn:
            conn.close()


def save_build_record(build_number, job_name, build_url, features, predictions):
    """Saves a build record to the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().isoformat()
        
        # Convert dicts to JSON strings for storage
        features_json = json.dumps(features)
        predictions_json = json.dumps(predictions)

        cursor.execute(
            """
            INSERT INTO build_records (timestamp, build_number, job_name, build_url, raw_features_json, raw_predictions_json)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (
                timestamp,
                build_number,
                job_name,
                build_url,
                features_json,
                predictions_json,
            ),
        )
        conn.commit()
        print(f"Build record for build {build_number} saved to DB.")
    except sqlite3.Error as e:
        print(f"ERROR: Failed to save build record: {e}")
    finally:
        if conn:
            conn.close()


def get_previous_build_status_from_db():
    """
    Fetches the status of the most recent previous build from the local database.
    Returns 1 for success, 0 for failure, or 1 if no previous record (assume success for first build).
    """
    conn = None
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row  # Allows accessing columns by name
        cursor = conn.cursor()
        cursor.execute(
            "SELECT raw_predictions_json FROM build_records ORDER BY timestamp DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if row:
            predictions = json.loads(row["raw_predictions_json"])
            # Assuming 'build_success_prediction' is 1 for success, 0 for failure
            return predictions.get("build_success_prediction", 1)
        # REMOVED ELSE BLOCK AND DE-INDENTED
        print(
            f"WARNING: Could not fetch previous build status from DB. Assuming previous success (1)."
        )  # Removed {e} as it's not available here
        return 1
    except sqlite3.Error as e:
        print(f"WARNING: Could not fetch previous build status from DB: {e}. Assuming previous success (1).")
        return 1
    finally:
        if conn:
            conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="ML API Client for Jenkins CI/CD Quality Gate."
    )
    parser.add_argument(
        "--build-number", type=int, required=True, help="Current Jenkins build number."
    )
    parser.add_argument(
        "--job-name", type=str, required=True, help="Current Jenkins job name."
    )
    parser.add_argument(
        "--build-url", type=str, required=True, help="Current Jenkins build URL."
    )
    args = parser.parse_args()

    # Create DB and table
    create_db_and_table()

    # Get previous build status from local DB
    previous_build_status = get_previous_build_status_from_db()
    print(f"Previous build status (from local DB): {previous_build_status}")

    # --- Simulate/Collect Features (replace with real data collection in a real pipeline) ---
    features = {
        "lines_of_code_changed": 150,
        "num_files_changed": 5,
        "commit_message_length": 45,
        "previous_build_status": previous_build_status,
        "num_tests_run": 100,
        "test_pass_rate": 0.98,
        "developer_experience_level": 3,
        "build_environment_load": 70,
        "avg_loc_changed_last_N": 50.0,
        "last_build_duration": 25.5,
        "consecutive_failures_last_N": 0,
        "avg_test_pass_rate_last_N": 0.95,
    }
    print(f"Features prepared: {features}")

    # Make prediction request to ML API
    try:
        response = requests.post(ML_API_URL, json=features, timeout=10)  # ADDED timeout=10
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        predictions = response.json()
        print(f"ML API Predictions: {predictions}")

        # Save the build record
        save_build_record(
            args.build_number, args.job_name, args.build_url, features, predictions
        )

        # --- Implement Quality Gate Logic ---
        if (
            predictions.get("build_success_prediction", 0) == 0
        ):
            print("QUALITY GATE FAILED: ML model predicts build failure!")
            sys.exit(1)  # CHANGED exit(1) to sys.exit(1)

        if predictions.get("is_anomaly_prediction") == "Anomaly":
            print(
                "QUALITY GATE FAILED: ML model detected an anomaly in build features!"
            )
            sys.exit(1)  # CHANGED exit(1) to sys.exit(1)

        print(
            "QUALITY GATE PASSED: ML model predicts build success and no anomalies detected."
        )

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to connect to ML API: {e}")
        print("QUALITY GATE FAILED: ML API connection error.")
        sys.exit(1)  # CHANGED exit(1) to sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to decode JSON response from ML API: {e}")
        print("QUALITY GATE FAILED: Invalid ML API response.")
        sys.exit(1)  # CHANGED exit(1) to sys.exit(1)
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        print("QUALITY GATE FAILED: Unexpected error during ML prediction.")
        sys.exit(1)  # CHANGED exit(1) to sys.exit(1)


if __name__ == "__main__":
    main()
