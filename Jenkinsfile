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
                // 'branch: 'main'' specifies the branch to build.
                // 'credentialsId: 'github-pat'' references the Secret text credential you set up in Jenkins.
                // 'url' is the HTTPS URL of your GitHub repository.
                git branch: 'main', credentialsId: 'github-username-pat', url: 'https://github.com/Ghubuser570/jenkins-python-ci-demo.git'
                // IMPORTANT: Replace YOUR_GITHUB_USERNAME with your actual GitHub username.
            }
        }

        // Stage 2: Install Python Dependencies
        stage('Install Dependencies') {
            steps {
                script {
                    // Create a Python virtual environment to isolate dependencies.
                    // 'py -3 -m venv venv' uses the Python launcher to create a venv for Python 3.
                    bat '"C:\\Users\\75\\AppData\\Local\\Programs\\Python\\Python310\\python.exe" -m pip install -r requirements.txt'
                }
            }
        }

        // Stage 3: Run Tests
        stage('Run Tests') {
            steps {
                script {
                    // Directly call python.exe to run pytest
                    bat '"C:\\Users\\75\\AppData\\Local\\Programs\\Python\\Python310\\python.exe" -m pytest'
                }
            }
        }

        stage('Code Formatting Check') {
            steps {
                script {
                    // Use black to check for formatting issues.
                    // --check: don't write changes, just return non-zero exit code if changes would be made.
                    // --diff: show the diff of what would be changed.
                    // . : check current directory
                    bat '"C:\\Users\\75\\AppData\\Local\\Programs\\Python\\Python310\\python.exe" -m black --check --diff .'
                }
            }
        }

        // --- NEW STAGE: Code Linting (Pylint) ---
        stage('Code Linting') {
            steps {
                script {
                    // Run pylint on your Python application files.
                    // Adjust 'app.py' and 'test_app.py' to include all your Python files.
                    // Consider adding ml_api_client.py if you want to lint it too.
                    bat '"C:\\Users\\75\\AppData\\Local\\Programs\\Python\\Python310\\python.exe" -m pylint app.py test_app.py ml_api_client.py'
                }
            }
        }

        stage('ML Quality Gate') {
            steps {
                script {
                    // Directly call python.exe to run the client script
                    bat '"C:\\Users\\75\\AppData\\Local\\Programs\\Python\\Python310\\python.exe" ml_api_client.py'
                }
            }
        }
        
        stage('Persist Build History DB') {
            steps {
                script {
                    // Source path: Relative to Jenkins workspace
                    def sourceDbPath = "data\\build_history.db"
                    // Destination path: Your absolute local project path + data folder
                    def destinationDbPath = "C:\\Users\\75\\Desktop\\Capstone\\Jenkins-python-ci-demo\\data\\build_history.db"

                    // Use 'xcopy /Y' to overwrite existing file without prompt
                    // Or 'copy /Y' if xcopy is not available or preferred for single file
                    // Using 'copy /Y' for simplicity and broad compatibility
                    bat "copy /Y \"${sourceDbPath}\" \"${destinationDbPath}\""
                    echo "Copied build_history.db from Jenkins workspace to ${destinationDbPath}"
                }
            }
        }

        // Stage 4: Simple Build/Verification (Placeholder for more complex build steps)
        stage('Build/Verify') {
            steps {
                // Echo commands to show progress.
                bat 'echo "Building and verifying the application..."'
                // You could add more complex build steps here, e.g., linting, static analysis.
                bat 'echo "Build/Verification complete!"'
            }
        }
    }

    // Post-build actions: These steps run after all stages are complete, regardless of success or failure.
    post {
        // 'always' block runs every time.
        always {
            // Clean up the workspace after the build to free up space.
            cleanWs()
        }
        // 'success' block runs only if all stages passed.
        success {
            echo 'Pipeline finished successfully!'
        }
        // 'failure' block runs only if any stage failed.
        failure {
            echo 'Pipeline failed!'
        }
    }
}