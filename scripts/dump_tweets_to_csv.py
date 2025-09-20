#!/usr/bin/env python3
"""
Script to dump tweets from SQLite database to CSV format.
This can be used to backup tweets or reinitialize the database.
"""

import sqlite3
import csv
import os
import sys
import json
from datetime import datetime

def load_config():
    """Load configuration from config.json file."""
    try:
        with open("config/config.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # Default configuration
        return {
            "database": {
                "path": "data/tweets.db"
            }
        }

def dump_tweets_to_csv(db_path, csv_path):
    """Dump all tweets from SQLite database to CSV file."""
    try:
        # Check if database exists
        if not os.path.exists(db_path):
            print(f"Database file {db_path} does not exist.")
            return False
            
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query all tweets
        cursor.execute("""
            SELECT created_at, user_name, text, link_to_tweet 
            FROM tweets 
            ORDER BY created_at_parsed DESC, created_at DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        # Write to CSV
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['CreatedAt', 'UserName', 'Text', 'LinkToTweet'])
            
            # Write data
            for row in rows:
                writer.writerow(row)
                
        print(f"Successfully dumped {len(rows)} tweets to {csv_path}")
        return True
        
    except Exception as e:
        print(f"Error dumping tweets to CSV: {e}")
        return False

def main():
    """Main function to run the dump script."""
    # Load configuration
    config = load_config()
    db_path = config['database']['path']
    
    # Default CSV path
    csv_path = "data/tweets_dump.csv"
    
    # Allow command line override
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
        
    if len(sys.argv) > 2:
        db_path = sys.argv[2]
    
    print(f"Dumping tweets from {db_path} to {csv_path}")
    
    if dump_tweets_to_csv(db_path, csv_path):
        print("Dump completed successfully!")
        return 0
    else:
        print("Dump failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())