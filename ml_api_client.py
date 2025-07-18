# jenkins-python-ci-demo/ml_api_client.py (Corrected Version with Pylint Fixes and Refactoring)
import os
import sys
from datetime import datetime
import sqlite3
import json

import requests
import git
import jenkins
import numpy as np

# --- Configuration ---
ML_API_URL = "http://localhost:5000/predict"
JENKINS_URL = "http://localhost:8080"
JENKINS_USERNAME = "75"
JENKINS_API_TOKEN = "11996ed55f52b97013614dde3865c5b594"
JENKINS_JOB_NAME = "jenkins-python-pipeline"
SQLITE_DB_PATH = os.path.join("data", "build_history.db")


def get_ml_predictions(build_features):
    """
    Sends build features to the ML API and returns the predictions.
    """
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(
            ML_API_URL, headers=headers, data=json.dumps(build_features), timeout=10
        )
        response.raise_for_status()
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
                raw_features_json TEXT,
                raw_predictions_json TEXT
            )
        """
        )
        conn.commit()
        print(f"SQLite database '{SQLITE_DB_PATH}' initialized successfully.")
    except sqlite3.Error as e:
        print(f"ERROR: SQLite database initialization failed: {e}")
        sys.exit(1)
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

        timestamp = data["timestamp"]
        features = data["features"]
        predictions = data["predictions"]

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
                json.dumps(features),
                json.dumps(predictions),
            ),
        )
        conn.commit()
        print(f"Build data saved to SQLite database '{SQLITE_DB_PATH}'.")
    except sqlite3.Error as e:
        print(f"ERROR: Failed to save build data to SQLite: {e}")
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
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM build_records ORDER BY timestamp DESC LIMIT ?", (num_builds,)
        )
        rows = cursor.fetchall()
        for row in rows:
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


def calculate_temporal_features(build_history):  # Removed 'current_features'
    """
    Calculates temporal features based on historical build data.
    """
    temporal_features = {}

    if build_history:
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
            temporal_features["avg_loc_changed_last_N"] = 0

        if (
            len(build_history) >= 1
            and build_history[0].get("build_duration_estimation_minutes") is not None
        ):
            last_build_duration = build_history[0]["build_duration_estimation_minutes"]
            temporal_features["last_build_duration"] = last_build_duration
        else:
            temporal_features["last_build_duration"] = 0

        consecutive_failures = 0
        for rec in build_history:
            if rec["features"].get("previous_build_status") == 0:
                consecutive_failures += 1
            else:
                break
        temporal_features["consecutive_failures_last_N"] = consecutive_failures

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
            temporal_features["avg_test_pass_rate_last_N"] = 1.0
    else:
        temporal_features["avg_loc_changed_last_N"] = 0
        temporal_features["last_build_duration"] = 0
        temporal_features["consecutive_failures_last_N"] = 0
        temporal_features["avg_test_pass_rate_last_N"] = 1.0

    print(f"Calculated Temporal Features: {temporal_features}")
    return temporal_features


def _extract_git_features():
    """Helper to extract Git-related features."""
    git_features = {}
    try:
        repo_path = os.getcwd()
        repo = git.Repo(repo_path)
        latest_commit = repo.head.commit
        diff_stats = latest_commit.stats.total
        git_features["lines_of_code_changed"] = diff_stats["lines"]
        git_features["num_files_changed"] = diff_stats["files"]
        git_features["commit_message_length"] = len(latest_commit.message)
        print(
            f"Git Features Extracted: LOC Changed={git_features['lines_of_code_changed']}, Files Changed={git_features['num_files_changed']}, Commit Msg Len={git_features['commit_message_length']}"
        )
    except (git.InvalidGitRepositoryError, Exception) as e:
        print(
            f"WARNING: Could not extract Git features: {e}. Using default/simulated values."
        )
        git_features["lines_of_code_changed"] = 50
        git_features["num_files_changed"] = 5
        git_features["commit_message_length"] = 50
    return git_features


def _extract_jenkins_features():
    """Helper to extract Jenkins-related features."""
    jenkins_features = {}
    try:
        print("Attempting to connect to Jenkins for feature extraction...")
        server = jenkins.Jenkins(
            JENKINS_URL,
            username=JENKINS_USERNAME,
            password=JENKINS_API_TOKEN,
            timeout=10,
        )
        server_version = server.get_version()
        print(f"Successfully connected to Jenkins API! Version: {server_version}")
        job_info = server.get_job_info(JENKINS_JOB_NAME)
        last_build_number = job_info["lastCompletedBuild"]["number"]
        last_build_info = server.get_build_info(JENKINS_JOB_NAME, last_build_number)
        last_build_result = last_build_info["result"]
        jenkins_features["previous_build_status"] = (
            1 if last_build_result == "SUCCESS" else 0
        )
        print(
            f"Jenkins Feature Extracted: Previous Build Status={last_build_result} ({jenkins_features['previous_build_status']})"
        )
    except (
        jenkins.JenkinsException,
        requests.exceptions.ConnectionError,
        Exception,
    ) as e:
        print(
            f"WARNING: Jenkins feature extraction failed: {e}. Using default/simulated values."
        )
        jenkins_features["previous_build_status"] = 1
    return jenkins_features


def _get_simulated_features():
    """Helper to get simulated features."""
    simulated_features = {}
    simulated_features["num_tests_run"] = 200
    simulated_features["test_pass_rate"] = round(np.random.uniform(0.90, 1.0), 2)
    simulated_features["developer_experience_level"] = 3
    simulated_features["build_environment_load"] = np.random.randint(40, 90)
    return simulated_features


def extract_real_build_features():
    """
    Extracts real-ish build features from the Git repository and Jenkins,
    and includes simulated and temporal features.
    """
    features = {}

    # Combine features from helper functions
    features.update(_extract_git_features())
    features.update(_extract_jenkins_features())
    features.update(_get_simulated_features())

    # Calculate Temporal Features
    print("Fetching recent build history for temporal feature calculation...")
    recent_history = get_recent_build_history(num_builds=5)
    temporal_feats = calculate_temporal_features(
        recent_history
    )  # Removed 'features' argument
    features.update(temporal_feats)

    # --- TEMPORARY: Logic to force a failure scenario for demo (UNCOMMENT FOR DEMO, COMMENT FOR NORMAL OPERATION) ---
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
    initialize_db()

    print("Extracting real-ish build features...")
    current_features = extract_real_build_features()
    print(f"\nFeatures to send to ML API: {current_features}")

    print("\nRequesting predictions from ML API...")
    predictions = get_ml_predictions(current_features)

    if predictions:
        print("\nML Predictions:")
        print(json.dumps(predictions, indent=4))

        build_record = {
            "timestamp": datetime.now().isoformat(),
            "features": current_features,
            "predictions": predictions,
        }
        save_build_data(build_record)

        if predictions.get("build_success_prediction") == 0:
            print("\n--- QUALITY GATE FAILED: ML predicted build failure! ---")
            sys.exit(1)
        elif predictions.get("is_anomaly_prediction") == "Anomaly":
            print("\n--- QUALITY GATE FAILED: ML detected an anomaly! ---")
            sys.exit(1)
        elif predictions.get("build_duration_estimation_minutes") > 45:
            print(
                f"\n--- QUALITY GATE FAILED: Estimated build time ({predictions.get('build_duration_estimation_minutes')} min) is too high! ---"
            )
            sys.exit(1)
        else:
            print("\n--- QUALITY GATE PASSED: Build looks good! ---")
            sys.exit(0)
    else:
        print("\nFailed to get predictions from ML API. Quality Gate FAILED.")
        sys.exit(1)
