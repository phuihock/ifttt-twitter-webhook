import requests
import json
import sys
import os

# Add the src directory to the path so we can import the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

# Test the IFTTT Twitter webhook handler
def test_ifttt_twitter_webhook():
    url = 'http://localhost:5000/ifttt/twitter'
    
    # Sample payload similar to what IFTTT would send
    payload = {
        "UserName": "testuser",
        "LinkToTweet": "https://twitter.com/testuser/status/123456789",
        "CreatedAt": "September 08, 2025 at 02:39PM",
        "Text": "This is a test tweet from IFTTT"
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    print("Testing IFTTT Twitter webhook handler...")
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ifttt_twitter_webhook()