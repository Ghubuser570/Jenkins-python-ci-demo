# jenkins-python-ci-demo/ml_api_client.py
import requests
import json
import random # To simulate dynamic build features

def get_ml_predictions(build_features):
    """
    Sends build features to the ML API and returns the predictions.
    """
    ml_api_url = "http://localhost:5000/predict"
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(ml_api_url, headers=headers, data=json.dumps(build_features))
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        predictions = response.json()
        return predictions
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to ML API at {ml_api_url}. Is it running?")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error making request to ML API: {e}")
        return None

def simulate_current_build_features():
    """
    Simulates current build features. In a real scenario, these would be
    extracted from the actual build environment (e.g., Git, test results).
    """
    # Generate some semi-random features for demonstration
    return {
        'lines_of_code_changed': random.randint(10, 300),
        'num_files_changed': random.randint(1, 20),
        'num_tests_run': random.randint(100, 400),
        'test_pass_rate': round(random.uniform(0.80, 1.0), 2),
        'previous_build_status': random.choice([0, 1]),
        'commit_message_length': random.randint(20, 100),
        'developer_experience_level': random.randint(1, 5),
        'build_environment_load': random.randint(30, 90)
    }

if __name__ == "__main__":
    # This block runs when you execute the script directly for testing
    print("Simulating current build features...")
    current_features = simulate_current_build_features()
    print(f"Simulated Features: {current_features}")

    print("\nRequesting predictions from ML API...")
    predictions = get_ml_predictions(current_features)

    if predictions:
        print("\nML Predictions:")
        print(json.dumps(predictions, indent=4))

        # Example of simple quality gate logic
        if predictions.get("build_success_prediction") == 0:
            print("\n--- QUALITY GATE FAILED: ML predicted build failure! ---")
            exit(1) # Exit with error code to fail Jenkins build
        elif predictions.get("is_anomaly_prediction") == "Anomaly":
            print("\n--- QUALITY GATE FAILED: ML detected an anomaly! ---")
            exit(1) # Exit with error code to fail Jenkins build
        else:
            print("\n--- QUALITY GATE PASSED: Build looks good! ---")
            exit(0) # Exit with success code
    else:
        print("\nFailed to get predictions from ML API.")
        exit(1) # Fail if no predictions