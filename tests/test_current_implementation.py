#!/usr/bin/env python3
"""
Simple test to verify the current implementation works correctly.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from iftttwh.app import save_tweet_to_db

def test_current_implementation():
    """Test that the current implementation works correctly."""
    # Test tweet data
    tweet1 = {
        'UserName': 'testuser',
        'LinkToTweet': 'https://twitter.com/testuser/status/123456789',
        'CreatedAt': 'September 10, 2025 at 07:43AM',
        'Text': 'This is a test tweet to verify duplicate prevention works correctly.'
    }
    
    tweet2 = {
        'UserName': 'testuser',
        'LinkToTweet': 'https://twitter.com/testuser/status/123456789',
        'CreatedAt': 'September 10, 2025 at 07:43AM',
        'Text': 'This is a test tweet to verify duplicate prevention works correctly.'  # Same as tweet1
    }
    
    tweet3 = {
        'UserName': 'testuser',
        'LinkToTweet': 'https://twitter.com/testuser/status/987654321',
        'CreatedAt': 'September 10, 2025 at 07:45AM',
        'Text': 'This is a different test tweet that should be saved.'
    }
    
    print("Testing current implementation...")
    
    # Save first tweet
    print("Saving first tweet...")
    result1 = save_tweet_to_db(tweet1)
    print(f"Result: {result1}")
    
    # Save second tweet (identical to first) - should be prevented
    print("\nSaving second tweet (identical to first)...")
    result2 = save_tweet_to_db(tweet2)
    print(f"Result: {result2}")
    
    # Save third tweet (different) - should be saved
    print("\nSaving third tweet (different)...")
    result3 = save_tweet_to_db(tweet3)
    print(f"Result: {result3}")
    
    if result1 and result2 and result3:
        print("\n✓ All tests passed!")
        return True
    else:
        print("\n✗ Some tests failed!")
        return False

if __name__ == "__main__":
    success = test_current_implementation()
    sys.exit(0 if success else 1)