// Jenkinsfile
// This pipeline defines the steps for your Python CI/CD process.
pipeline {
    agent any

    stages {
        stage('Checkout Code') {
            steps {
                git branch: 'main', credentialsId: 'github-username-pat', url: 'https://github.com/Ghubuser570/jenkins-python-ci-demo.git'
            }
        }

        stage('Prepare Python Env') {
            steps {
                script {
                    bat '"C:\\Users\\75\\AppData\\Local\\Programs\\Python\\Python310\\python.exe" -m venv venv'
                    echo "Virtual environment created."
                    bat 'venv\\Scripts\\activate && pip install -r requirements.txt'
                    echo "Dependencies installed into virtual environment."
                }
            }
        }

        stage('Run Tests') {
            steps {
                script {
                    bat 'venv\\Scripts\\activate && "C:\\Users\\75\\AppData\\Local\\Programs\\Python\\Python310\\python.exe" -m pytest'
                }
            }
        }

        stage('Code Formatting Check') {
            steps {
                script {
                    bat 'venv\\Scripts\\activate && "C:\\Users\\75\\AppData\\Local\\Programs\\Python\\Python310\\python.exe" -m black --check --diff . --exclude venv'
                }
            }
        }

        stage('Code Linting') {
            steps {
                script {
                    bat 'venv\\Scripts\\activate && "C:\\Users\\75\\AppData\\Local\\Programs\\Python\\Python310\\python.exe" -m pylint app.py test_app.py ml_api_client.py'
                }
            }
        }

        stage('ML Quality Gate') {
            steps {
                script {
                    echo "Running ML Quality Gate against containerized ML service..."
                    bat 'venv\\Scripts\\activate && "C:\\Users\\75\\AppData\\Local\\Programs\\Python\\Python310\\python.exe" ml_api_client.py ' +
                        '--build-number=%BUILD_NUMBER% ' +
                        '--job-name=%JOB_NAME% ' +
                        '--build-url=%BUILD_URL%'
                    echo "ML Quality Gate complete."
                }
            }
        }

        stage('Build/Verify') {
            steps {
                bat 'echo "Building and verifying the application..."'
                bat 'echo "Build/Verification complete!"'
            }
        }
    }

    post {
        always {
            echo 'Post-build actions always executed.'
            script {
                def sourceDbPath = "data\\build_history.db"
                def destinationDbPath = "C:\\Users\\75\\Desktop\\Capstone\\Jenkins-python-ci-demo\\data\\build_history.db"

                def workspaceDataDir = "${env.WORKSPACE}\\data"
                def sourceFileExists = fileExists("${workspaceDataDir}\\build_history.db")

                if (sourceFileExists) {
                    bat "copy /Y \"${sourceDbPath}\" \"${destinationDbPath}\""
                    echo "Copied build_history.db from Jenkins workspace to ${destinationDbPath}"
                } else {
                    echo "build_history.db not found in Jenkins workspace, skipping copy."
                (
            "WARNING: Could not fetch previous build status from DB. Assuming previous success (1)."
        )
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
