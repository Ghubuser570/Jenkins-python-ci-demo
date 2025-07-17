# test_jenkins_connection.py
import jenkins
import sys

JENKINS_URL = "http://localhost:8080"
JENKINS_USERNAME = "75" # Your Jenkins admin username
JENKINS_API_TOKEN = "11e3184493de95cb86776f62d6a90e0bfc" # Your Jenkins API Token
JENKINS_JOB_NAME = "jenkins-python-pipeline" # The name of your Jenkins pipeline job

try:
    print(f"Attempting to connect to Jenkins at {JENKINS_URL} with user {JENKINS_USERNAME}...")
    server = jenkins.Jenkins(JENKINS_URL, username=JENKINS_USERNAME, password=JENKINS_API_TOKEN)

    # Verify connection by getting Jenkins version
    version = server.get_version()
    print(f"Successfully connected to Jenkins! Version: {version}")

    # Try to get job info
    job_info = server.get_job_info(JENKINS_JOB_NAME)
    print(f"Successfully retrieved info for job '{JENKINS_JOB_NAME}'.")
    print(f"Last completed build number: {job_info['lastCompletedBuild']['number']}")
    print(f"Last completed build result: {server.get_build_info(JENKINS_JOB_NAME, job_info['lastCompletedBuild']['number'])['result']}")

    print("\nJenkins connection test successful!")

except jenkins.JenkinsException as e:
    print(f"Jenkins Connection Error: {e}")
    print("Possible causes:")
    print("1. Incorrect JENKINS_USERNAME or JENKINS_API_TOKEN.")
    print("2. Jenkins is not running or accessible at http://localhost:8080.")
    print("3. The user '75' does not have sufficient permissions (e.g., Overall/Read, Job/Read).")
    print("4. Jenkins CSRF protection might be blocking the request (less common with python-jenkins).")
    sys.exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    sys.exit(1)