# jenkins-python-ci-demo/ml_api_client.py (Enhanced Version with GitPython & Python-Jenkins)
import requests
import json
import os
import git # For GitPython
import jenkins # For Python-Jenkins
import sys # For sys.exit()
import numpy as np

# --- Configuration ---
ML_API_URL = "http://localhost:5000/predict"
JENKINS_URL = "http://localhost:8080"
JENKINS_USERNAME = "75" # Your Jenkins admin username
JENKINS_API_TOKEN = "11996ed55f52b97013614dde3865c5b594" # Your Jenkins API Token
JENKINS_JOB_NAME = "jenkins-python-pipeline"

def get_ml_predictions(build_features):
    """
    Sends build features to the ML API and returns the predictions.
    """
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(ML_API_URL, headers=headers, data=json.dumps(build_features))
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        predictions = response.json()
        return predictions
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Could not connect to ML API at {ML_API_URL}. Is it running?")
        return None
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Request to ML API failed: {e}")
        return None

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
        features['lines_of_code_changed'] = diff_stats['lines']
        features['num_files_changed'] = diff_stats['files']

        # commit_message_length
        features['commit_message_length'] = len(latest_commit.message)

        print(f"Git Features Extracted: LOC Changed={features['lines_of_code_changed']}, Files Changed={features['num_files_changed']}, Commit Msg Len={features['commit_message_length']}")

    except Exception as e:
        print(f"WARNING: Could not extract Git features: {e}. Using default/simulated values.")
        # Fallback to simulated values if Git extraction fails
        features['lines_of_code_changed'] = 50
        features['num_files_changed'] = 5
        features['commit_message_length'] = 50

    # --- Extract Jenkins Features using Python-Jenkins ---
    try:
        server = jenkins.Jenkins(JENKINS_URL, username=JENKINS_USERNAME, password=JENKINS_API_TOKEN)
        # Verify connection
        server.get_version()

        # Get the last completed build for the current job
        job_info = server.get_job_info(JENKINS_JOB_NAME)
        last_build_number = job_info['lastCompletedBuild']['number']
        last_build_info = server.get_build_info(JENKINS_JOB_NAME, last_build_number)

        # previous_build_status
        # Jenkins build result: 'SUCCESS', 'FAILURE', 'UNSTABLE', 'ABORTED', 'NOT_BUILT'
        last_build_result = last_build_info['result']
        features['previous_build_status'] = 1 if last_build_result == 'SUCCESS' else 0
        print(f"Jenkins Feature Extracted: Previous Build Status={last_build_result} ({features['previous_build_status']})")

    except Exception as e:
        print(f"WARNING: Could not extract Jenkins features: {e}. Using default/simulated values.")
        # Fallback to simulated values if Jenkins extraction fails
        features['previous_build_status'] = 1 # Assume success if cannot check

    # --- Remaining Features (Simulated for simplicity) ---
    # Truly dynamic values for these would require more complex monitoring/instrumentation
    features['num_tests_run'] = 200 # Simulated
    features['test_pass_rate'] = round(np.random.uniform(0.90, 1.0), 2) # Simulated, but can be influenced by other factors
    features['developer_experience_level'] = 3 # Simulated (e.g., 1=junior, 5=senior)
    features['build_environment_load'] = np.random.randint(40, 90) # Simulated load

    # --- TEMPORARY: Logic to force a failure scenario for demo (REMOVE FOR NORMAL OPERATION) ---
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
    print("Extracting real-ish build features...")
    current_features = extract_real_build_features()
    print(f"\nFeatures to send to ML API: {current_features}")

    print("\nRequesting predictions from ML API...")
    predictions = get_ml_predictions(current_features)

    if predictions:
        print("\nML Predictions:")
        print(json.dumps(predictions, indent=4))

        # --- Quality Gate Logic ---
        # This logic determines if the Jenkins build should pass or fail based on ML predictions
        if predictions.get("build_success_prediction") == 0:
            print("\n--- QUALITY GATE FAILED: ML predicted build failure! ---")
            sys.exit(1) # Exit with error code to fail Jenkins build
        elif predictions.get("is_anomaly_prediction") == "Anomaly":
            print("\n--- QUALITY GATE FAILED: ML detected an anomaly! ---")
            sys.exit(1) # Exit with error code to fail Jenkins build
        elif predictions.get("build_duration_estimation_minutes") > 45: # Example: fail if estimated time is too high
            print(f"\n--- QUALITY GATE FAILED: Estimated build time ({predictions.get('build_duration_estimation_minutes')} min) is too high! ---")
            sys.exit(1)
        else:
            print("\n--- QUALITY GATE PASSED: Build looks good! ---")
            sys.exit(0) # Exit with success code
    else:
        print("\nFailed to get predictions from ML API. Quality Gate FAILED.")
        sys.exit(1) # Fail if no predictions