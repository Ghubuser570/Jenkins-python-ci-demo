# jenkins-python-ci-demo/ml_api_client.py (Corrected Version with Dynamic Feature Extraction, SQLite & Temporal Features)
import os
import sys
from datetime import datetime
import sqlite3  # For SQLite database operations
import json  # For JSON serialization (for database storage and printing)

import requests  # For API calls
import git  # For GitPython
import jenkins  # For Python-Jenkins
import numpy as np  # For random number generation (for simulated features)

# --- Configuration ---
ML_API_URL = "http://localhost:5000/predict"
JENKINS_URL = "http://localhost:8080"
JENKINS_USERNAME = "75"  # Your Jenkins admin username
JENKINS_API_TOKEN = "11996ed55f52b97013614dde3865c5b594"  # Your Jenkins API Token
JENKINS_JOB_NAME = "jenkins-python-pipeline"  # The name of your Jenkins pipeline job
SQLITE_DB_PATH = os.path.join(
    "data", "build_history.db"
)  # Path to SQLite database file


def get_ml_predictions(build_features):
    """
    Sends build features to the ML API and returns the predictions.
    """
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(
            ML_API_URL, headers=headers, data=json.dumps(build_features), timeout=10
        )
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        predictions = response.json()
        return predictions
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Could not connect to ML API at {ML_API_URL}. Is it running?")
        return None
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Request to ML API failed: {e}")
        return None


def initialize_db():
    """
    Initializes the SQLite database and creates the build_records table
    if it does not already exist.
    """
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)

    conn = None
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS build_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                loc_changed INTEGER,
                files_changed INTEGER,
                commit_msg_len INTEGER,
                previous_build_status INTEGER,
                num_tests_run INTEGER,
                test_pass_rate REAL,
                developer_experience_level INTEGER,
                build_environment_load INTEGER,
                build_success_prediction INTEGER,
                build_success_probability REAL,
                build_duration_estimation_minutes REAL,
                anomaly_score REAL,
                is_anomaly_prediction TEXT,
                raw_features_json TEXT,  -- Store raw features as JSON string
                raw_predictions_json TEXT -- Store raw predictions as JSON string
            )
        """
        )
        conn.commit()
        print(f"SQLite database '{SQLITE_DB_PATH}' initialized successfully.")
    except sqlite3.Error as e:
        print(f"ERROR: SQLite database initialization failed: {e}")
        sys.exit(1)  # Critical error, exit pipeline if DB cannot be initialized
    finally:
        if conn:
            conn.close()


def save_build_data(data):
    """
    Inserts a new build's features and predictions into the SQLite database.
    """
    conn = None
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()

        # Extract data for direct columns
        timestamp = data["timestamp"]
        features = data["features"]
        predictions = data["predictions"]

        # Prepare data for insertion
        cursor.execute(
            """
            INSERT INTO build_records (
                timestamp, loc_changed, files_changed, commit_msg_len,
                previous_build_status, num_tests_run, test_pass_rate,
                developer_experience_level, build_environment_load,
                build_success_prediction, build_success_probability,
                build_duration_estimation_minutes, anomaly_score,
                is_anomaly_prediction, raw_features_json, raw_predictions_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                timestamp,
                features.get("lines_of_code_changed"),
                features.get("num_files_changed"),
                features.get("commit_message_length"),
                features.get("previous_build_status"),
                features.get("num_tests_run"),
                features.get("test_pass_rate"),
                features.get("developer_experience_level"),
                features.get("build_environment_load"),
                predictions.get("build_success_prediction"),
                predictions.get("build_success_probability"),
                predictions.get("build_duration_estimation_minutes"),
                predictions.get("anomaly_score"),
                predictions.get("is_anomaly_prediction"),
                json.dumps(features),  # Store full features as JSON string
                json.dumps(predictions),  # Store full predictions as JSON string
            ),
        )
        conn.commit()
        print(f"Build data saved to SQLite database '{SQLITE_DB_PATH}'.")
    except sqlite3.Error as e:
        print(f"ERROR: Failed to save build data to SQLite: {e}")
        # Do not sys.exit(1) here, as we still want the quality gate to run
        # but log the error clearly.
    finally:
        if conn:
            conn.close()


def get_recent_build_history(num_builds=5):
    """
    Fetches the last N build records from the SQLite database.
    Returns a list of dictionaries, each representing a build record.
    """
    conn = None
    history = []
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row  # This makes rows behave like dictionaries
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM build_records ORDER BY timestamp DESC LIMIT ?", (num_builds,)
        )
        rows = cursor.fetchall()
        for row in rows:
            # Convert row to a dictionary and parse JSON strings
            record = dict(row)
            record["features"] = json.loads(record["raw_features_json"])
            record["predictions"] = json.loads(record["raw_predictions_json"])
            history.append(record)
        print(f"Fetched {len(history)} recent build records from SQLite.")
    except sqlite3.Error as e:
        print(f"ERROR: Failed to fetch recent build history from SQLite: {e}")
    finally:
        if conn:
            conn.close()
    return history


def calculate_temporal_features(current_features, build_history):
    """
    Calculates temporal features based on current features and historical build data.
    """
    temporal_features = {}

    # Example 1: Average lines of code changed in recent builds
    if build_history:
        # Filter out records where 'loc_changed' might be None or missing
        valid_loc_changes = [
            rec["loc_changed"]
            for rec in build_history
            if rec.get("loc_changed") is not None
        ]
        if valid_loc_changes:
            temporal_features["avg_loc_changed_last_N"] = sum(valid_loc_changes) / len(
                valid_loc_changes
            )
        else:
            temporal_features["avg_loc_changed_last_N"] = 0  # Default if no valid data

        # Example 2: Trend in build duration (simple difference from last build)
        # We need the predicted duration of the current build for this, which is not available yet here.
        # This feature will be more useful if calculated *after* ML prediction, or if we use
        # the *previous* build's predicted duration. For now, we'll use the last historical build.
        if (
            len(build_history) >= 1
            and build_history[0].get("build_duration_estimation_minutes") is not None
        ):
            last_build_duration = build_history[0]["build_duration_estimation_minutes"]
            # This feature will be more accurate if calculated after the current build's prediction is known.
            # For now, we'll just use the last build's duration as a feature itself.
            temporal_features["last_build_duration"] = last_build_duration
        else:
            temporal_features["last_build_duration"] = 0

        # Example 3: Number of consecutive failures (simple count)
        consecutive_failures = 0
        for rec in build_history:
            # Check actual build status from features, or predicted if actual not available
            if rec["features"].get("previous_build_status") == 0:  # 0 for FAILURE
                consecutive_failures += 1
            else:
                break  # Stop if a successful build is encountered
        temporal_features["consecutive_failures_last_N"] = consecutive_failures

        # Example 4: Average test pass rate in recent builds
        valid_test_pass_rates = [
            rec["test_pass_rate"]
            for rec in build_history
            if rec.get("test_pass_rate") is not None
        ]
        if valid_test_pass_rates:
            temporal_features["avg_test_pass_rate_last_N"] = sum(
                valid_test_pass_rates
            ) / len(valid_test_pass_rates)
        else:
            temporal_features["avg_test_pass_rate_last_N"] = (
                1.0  # Default to perfect if no data
            )

    else:
        # If no history, set default/zero values for temporal features
        temporal_features["avg_loc_changed_last_N"] = 0
        temporal_features["last_build_duration"] = 0  # Changed from duration_diff
        temporal_features["consecutive_failures_last_N"] = 0
        temporal_features["avg_test_pass_rate_last_N"] = 1.0

    print(f"Calculated Temporal Features: {temporal_features}")
    return temporal_features


def extract_real_build_features():
    """
    Extracts real-ish build features from the Git repository and Jenkins.
    """
    features = {}

    # --- Extract Git Features using GitPython ---
    try:
        # Get the path to the Jenkins workspace where the repo is cloned
        # This script runs from the root of the cloned repo in Jenkins workspace
        repo_path = os.getcwd()
        repo = git.Repo(repo_path)
        latest_commit = repo.head.commit

        # lines_of_code_changed, num_files_changed
        # This is a simplification. A more robust way would compare against a base branch.
        # For simplicity, we'll just get stats for the latest commit's changes.
        # This gets diff stats relative to its parent commit
        diff_stats = latest_commit.stats.total
        features["lines_of_code_changed"] = diff_stats["lines"]
        features["num_files_changed"] = diff_stats["files"]

        # commit_message_length
        features["commit_message_length"] = len(latest_commit.message)

        print(
            f"Git Features Extracted: LOC Changed={features['lines_of_code_changed']}, Files Changed={features['num_files_changed']}, Commit Msg Len={features['commit_message_length']}"
        )

    except git.InvalidGitRepositoryError as e:  # More specific for Git errors
        print(
            f"WARNING: Invalid Git repository or no commits: {e}. Using default/simulated values."
        )
        features["lines_of_code_changed"] = 50
        features["num_files_changed"] = 5
        features["commit_message_length"] = 50
    except Exception as e:  # Catch other unexpected Git-related errors
        print(
            f"WARNING: Could not extract Git features: {e}. Using default/simulated values."
        )
        features["lines_of_code_changed"] = 50
        features["num_files_changed"] = 5
        features["commit_message_length"] = 50

    # --- Extract Jenkins Features using Python-Jenkins ---
    try:
        print("Attempting to connect to Jenkins for feature extraction...")
        # Initialize Jenkins client with explicit CSRF handling
        # The 'timeout' is good practice.
        server = jenkins.Jenkins(
            JENKINS_URL,
            username=JENKINS_USERNAME,
            password=JENKINS_API_TOKEN,
            timeout=10,
        )

        # Verify connection by getting Jenkins version (this also implicitly tests authentication)
        server_version = server.get_version()
        print(f"Successfully connected to Jenkins API! Version: {server_version}")

        # Get the last completed build for the current job
        job_info = server.get_job_info(JENKINS_JOB_NAME)
        last_build_number = job_info["lastCompletedBuild"]["number"]
        last_build_info = server.get_build_info(JENKINS_JOB_NAME, last_build_number)

        # previous_build_status
        # Jenkins build result: 'SUCCESS', 'FAILURE', 'UNSTABLE', 'ABORTED', 'NOT_BUILT'
        last_build_result = last_build_info["result"]
        features["previous_build_status"] = 1 if last_build_result == "SUCCESS" else 0
        print(
            f"Jenkins Feature Extracted: Previous Build Status={last_build_result} ({features['previous_build_status']})"
        )

    except jenkins.JenkinsException as e:
        # Catch specific Jenkins errors for better debugging
        print(
            f"WARNING: Jenkins API error during feature extraction: {e}. Using default/simulated values."
        )
        features["previous_build_status"] = 1  # Fallback
    except requests.exceptions.ConnectionError as e:  # Specific for network issues
        print(
            f"WARNING: Jenkins connection error: {e}. Using default/simulated values."
        )
        features["previous_build_status"] = 1
    except Exception as e:  # Catch other unexpected Jenkins-related errors
        print(
            f"WARNING: An unexpected error occurred during Jenkins feature extraction: {e}. Using default/simulated values."
        )
        features["previous_build_status"] = 1

    # --- Remaining Features (Simulated for simplicity) ---
    # Truly dynamic values for these would require more complex monitoring/instrumentation
    features["num_tests_run"] = 200  # Simulated
    features["test_pass_rate"] = round(
        np.random.uniform(0.90, 1.0), 2
    )  # Simulated, but can be influenced by other factors
    features["developer_experience_level"] = 3  # Simulated (e.g., 1=junior, 5=senior)
    features["build_environment_load"] = np.random.randint(40, 90)  # Simulated load

    # --- NEW: Calculate Temporal Features ---
    print("Fetching recent build history for temporal feature calculation...")
    # Pass 5 to get_recent_build_history to fetch the last 5 records
    recent_history = get_recent_build_history(num_builds=5)
    temporal_feats = calculate_temporal_features(features, recent_history)
    features.update(
        temporal_feats
    )  # Merge temporal features into the main features dictionary

    # --- TEMPORARY: Logic to force a failure scenario for demo (UNCOMMENT FOR DEMO, COMMENT FOR NORMAL OPERATION) ---
    # Uncomment this block to demonstrate a quality gate failure
    # Forcing a scenario that ML models would likely flag as failure/anomaly
    # features['lines_of_code_changed'] = 450
    # features['num_files_changed'] = 40
    # features['num_tests_run'] = 50
    # features['test_pass_rate'] = 0.60
    # features['previous_build_status'] = 0
    # features['commit_message_length'] = 120
    # features['developer_experience_level'] = 2
    # features['build_environment_load'] = 95
    # print("\n--- DEMO MODE: FORCING FAILURE SCENARIO FEATURES ---")
    # --- END TEMPORARY ---

    return features


if __name__ == "__main__":
    initialize_db()  # Initialize the SQLite database at the start

    print("Extracting real-ish build features...")
    current_features = extract_real_build_features()
    print(f"\nFeatures to send to ML API: {current_features}")

    print("\nRequesting predictions from ML API...")
    predictions = get_ml_predictions(current_features)

    if predictions:
        print("\nML Predictions:")
        print(json.dumps(predictions, indent=4))

        # Combine features and predictions for saving
        build_record = {
            "timestamp": datetime.now().isoformat(),
            "features": current_features,  # This now includes temporal features
            "predictions": predictions,
        }
        save_build_data(build_record)  # Save data to SQLite

        # --- Quality Gate Logic ---
        # This logic determines if the Jenkins build should pass or fail based on ML predictions
        if predictions.get("build_success_prediction") == 0:
            print("\n--- QUALITY GATE FAILED: ML predicted build failure! ---")
            sys.exit(1)  # Exit with error code to fail Jenkins build
        elif predictions.get("is_anomaly_prediction") == "Anomaly":
            print("\n--- QUALITY GATE FAILED: ML detected an anomaly! ---")
            sys.exit(1)  # Exit with error code to fail Jenkins build
        elif (
            predictions.get("build_duration_estimation_minutes") > 45
        ):  # Example: fail if estimated time is too high
            print(
                f"\n--- QUALITY GATE FAILED: Estimated build time ({predictions.get('build_duration_estimation_minutes')} min) is too high! ---"
            )
            sys.exit(1)
        else:
            print("\n--- QUALITY GATE PASSED: Build looks good! ---")
            sys.exit(0)  # Exit with success code
    else:
        print("\nFailed to get predictions from ML API. Quality Gate FAILED.")
        sys.exit(1)  # Fail if no predictions
