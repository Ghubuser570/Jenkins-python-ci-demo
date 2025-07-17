# raw_jenkins_test.py
import requests
import sys

JENKINS_URL = "http://localhost:8080"

try:
    print(f"Attempting a raw GET request to Jenkins at {JENKINS_URL}...")
    # Make a simple GET request to the Jenkins base URL
    response = requests.get(JENKINS_URL, timeout=10) # Add a timeout for safety
    response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

    print(f"Successfully received response from Jenkins!")
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {response.headers}")
    # print(f"First 500 characters of response body:\n{response.text[:500]}") # Uncomment to see HTML

except requests.exceptions.ConnectionError as e:
    print(f"CONNECTION ERROR: Could not connect to Jenkins at {JENKINS_URL}.")
    print(f"Details: {e}")
    print("This often indicates a firewall blocking the connection, or Jenkins is not running/listening.")
    sys.exit(1)
except requests.exceptions.Timeout:
    print(f"TIMEOUT ERROR: Request to {JENKINS_URL} timed out.")
    print("Jenkins might be running but very slow to respond, or a network issue.")
    sys.exit(1)
except requests.exceptions.RequestException as e:
    print(f"HTTP ERROR: Received an unexpected HTTP response from {JENKINS_URL}.")
    print(f"Details: {e}")
    print("This could be a 403 Forbidden, 401 Unauthorized, or other server error.")
    sys.exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    sys.exit(1)