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
                git branch: 'main', credentialsId: 'github-pat', url: 'https://github.com/Ghubuser570/jenkins-python-ci-demo.git'
                // IMPORTANT: Replace YOUR_GITHUB_USERNAME with your actual GitHub username.
            }
        }

        // Stage 2: Install Python Dependencies
        stage('Install Dependencies') {
            steps {
                script {
                    // Create a Python virtual environment to isolate dependencies.
                    // 'py -3 -m venv venv' uses the Python launcher to create a venv for Python 3.
                    bat 'py -3 -m venv venv'

                    // Activate the virtual environment for subsequent commands.
                    // 'venv\\Scripts\\activate.bat' is the correct activation script for Windows.
                    bat 'venv\\Scripts\\activate.bat'

                    // Install packages listed in requirements.txt using pip.
                    bat 'pip install -r requirements.txt'
                }
            }
        }

        // Stage 3: Run Tests
        stage('Run Tests') {
            steps {
                script {
                    // Activate the virtual environment again to ensure pytest runs within it.
                    bat 'venv\\Scripts\\activate.bat'

                    // Run pytest to execute your Python tests.
                    bat 'pytest'
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