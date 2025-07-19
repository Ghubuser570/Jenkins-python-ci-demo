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
                }
            }
            cleanWs()
        }
        success {
            echo 'Pipeline finished successfully!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}
