// Jenkinsfile
// This pipeline defines the steps for your Python CI/CD process.
pipeline {
    // 'agent any' means Jenkins can run this pipeline on any available agent.
    // Since you have a single Jenkins server on your PC, it will run there.
    agent any

    // Define the stages of your CI/CD pipeline.
    stages {
        // Stage 1: Checkout Code from GitHub
        stage('Checkout Code') {
            steps {
                // The 'git' step pulls the code from your GitHub repository.
                git branch: 'main', credentialsId: 'github-username-pat', url: 'https://github.com/Ghubuser570/jenkins-python-ci-demo.git'
            }
        }

        // Stage 2: Prepare Python Environment and Install Dependencies
        // We will create and activate a virtual environment within the Jenkins workspace
        // to ensure isolated and consistent dependency management for the client script.
        stage('Prepare Python Env') {
            steps {
                script {
                    // Create a Python virtual environment in the workspace
                    // Using 'python' directly assumes it's in PATH or specified in Jenkins global config
                    // For robustness, we'll keep the full path for now, but aim for 'python -m venv venv'
                    // if Python is properly configured in Jenkins agent's PATH.
                    bat '"C:\\Users\\75\\AppData\\Local\\Programs\\Python\\Python310\\python.exe" -m venv venv'
                    echo "Virtual environment created."

                    // Activate the virtual environment and install dependencies for ml_api_client.py
                    // These dependencies are requests, sqlite3 (built-in), etc.
                    // Assuming requirements.txt in the repo contains these.
                    // If ml_api_client.py has very few, specific dependencies, you could install them directly.
                    // For now, let's assume requirements.txt has what ml_api_client.py needs.
                    bat 'venv\\Scripts\\activate && pip install -r requirements.txt'
                    echo "Dependencies installed into virtual environment."
                }
            }
        }

        // Stage 3: Run Tests
        stage('Run Tests') {
            steps {
                script {
                    // Activate venv and then run pytest
                    bat 'venv\\Scripts\\activate && "C:\\Users\\75\\AppData\\Local\\Programs\\Python\\Python310\\python.exe" -m pytest'
                }
            }
        }

        // Stage 4: Code Formatting Check (Black)
        stage('Code Formatting Check') {
            steps {
                script {
                    // Activate venv and then run black
                    bat 'venv\\Scripts\\activate && "C:\\Users\\75\\AppData\\Local\\Programs\\Python\\Python310\\python.exe" -m black --check --diff .'
                }
            }
        }

        // Stage 5: Code Linting (Pylint)
        stage('Code Linting') {
            steps {
                script {
                    // Activate venv and then run pylint
                    // Ensure 'app.py', 'test_app.py', 'ml_api_client.py' are in your repo's root or adjust paths.
                    // If app.py and test_app.py are in ml-service/ folder, you'd need to adjust paths here.
                    // Assuming they are in the root of the checked-out repo for now.
                    bat 'venv\\Scripts\\activate && "C:\\Users\\75\\AppData\\Local\\Programs\\Python\\Python310\\python.exe" -m pylint app.py test_app.py ml_api_client.py'
                }
            }
        }

        // Stage 6: ML Quality Gate - Interact with Containerized ML Service
        stage('ML Quality Gate') {
            steps {
                script {
                    // Ensure the Docker Compose stack is UP and running before this stage.
                    // This Jenkinsfile does NOT start the Docker Compose stack itself.
                    // It assumes the stack (ml-api, prometheus, grafana) is already running.
                    echo "Running ML Quality Gate against containerized ML service..."
                    // Activate venv and then run the client script
                    bat 'venv\\Scripts\\activate && "C:\\Users\\75\\AppData\\Local\\Programs\\Python\\Python310\\python.exe" ml_api_client.py'
                    echo "ML Quality Gate complete."
                }
            }
        }

        // Stage 7: Simple Build/Verification (Placeholder for more complex build steps)
        stage('Build/Verify') {
            steps {
                bat 'echo "Building and verifying the application..."'
                bat 'echo "Build/Verification complete!"'
            }
        }
    }

    // Post-build actions: These steps run after all stages are complete, regardless of success or failure.
    post {
        always {
            echo 'Post-build actions always executed.'
            script {
                // Define the source path of the DB in the Jenkins workspace
                def sourceDbPath = "data\\build_history.db"
                // Define the destination path on the host machine, which is mounted by the Docker container
                def destinationDbPath = "C:\\Users\\75\\Desktop\\Capstone\\Jenkins-python-ci-demo\\data\\build_history.db"

                // Check if the source DB file exists in the workspace before attempting to copy
                def workspaceDataDir = "${env.WORKSPACE}\\data"
                def sourceFileExists = fileExists("${workspaceDataDir}\\build_history.db")

                if (sourceFileExists) {
                    // Copy the DB from Jenkins workspace to the host path (which is mounted by the container)
                    bat "copy /Y \"${sourceDbPath}\" \"${destinationDbPath}\""
                    echo "Copied build_history.db from Jenkins workspace to ${destinationDbPath}"
                } else {
                    echo "build_history.db not found in Jenkins workspace, skipping copy."
                }
            }
            cleanWs() // Clean the Jenkins workspace after the build
        }
        success {
            echo 'Pipeline finished successfully!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}
