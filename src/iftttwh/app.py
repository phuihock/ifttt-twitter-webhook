from flask import Flask, request, jsonify
import json
import hashlib
import hmac
import os
from datetime import datetime
import logging
import sqlite3
import re
from dateutil import parser as date_parser
import csv
import os.path

# Load configuration
def load_config():
    """Load configuration from config.json file."""
    try:
        with open('config/config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Default configuration for Twitter webhook
        return {
            "server": {
                "host": "0.0.0.0",
                "port": 5000,
                "debug": False
            },
            "security": {
                "secret_key": os.environ.get('WEBHOOK_SECRET', 'default_secret_key'),
                "require_signature": False
            },
            "logging": {
                "level": "INFO",
                "file": "logs/app.log"
            },
            "database": {
                "path": "data/tweets.db",
                "csv_path": "data/tweets.csv"
            },
            "debug_logging": {
                "payload_log_file": "logs/payload.log"
            }
        }

config = load_config()

# Configure logging
log_level = getattr(logging, config['logging']['level'].upper(), logging.INFO)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(config['logging']['file']),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configure payload debug logging
payload_logger = logging.getLogger('payload_debug')
payload_logger.setLevel(logging.DEBUG)
payload_log_handler = logging.FileHandler(config['debug_logging']['payload_log_file'])
payload_log_handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
payload_logger.addHandler(payload_log_handler)
payload_logger.propagate = False  # Don't propagate to other loggers

app = Flask(__name__)

# Get secret key from config or environment variables
SECRET_KEY = config['security']['secret_key']
REQUIRE_SIGNATURE = config['security']['require_signature']
DB_PATH = config['database']['path']
CSV_PATH = config['database']['csv_path']

def parse_created_at(created_at_str):
    """Parse the CreatedAt field from IFTTT into a datetime object."""
    if not created_at_str or created_at_str == '':
        return None
    
    try:
        # Handle the format: "September 08, 2025 at 02:39PM"
        # We need to replace " at " with " " to make it parseable
        formatted_str = created_at_str.replace(" at ", " ")
        parsed_datetime = date_parser.parse(formatted_str)
        return parsed_datetime.isoformat()
    except Exception as e:
        logger.error(f"Failed to parse CreatedAt field '{created_at_str}': {e}")
        return None

def init_db():
    """Initialize the SQLite database for storing tweets."""
    try:
        # Check if database exists
        db_exists = os.path.exists(DB_PATH)
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        if not db_exists:
            # Database doesn't exist, create it
            logger.info("Database does not exist, creating new database")
            c.execute('''CREATE TABLE tweets
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          user_name TEXT,
                          link_to_tweet TEXT,
                          created_at TEXT,
                          created_at_parsed TIMESTAMP,
                          text TEXT,
                          received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            
            # Check if CSV file exists and load data
            if os.path.exists(CSV_PATH):
                logger.info(f"Loading initial data from {CSV_PATH}")
                load_csv_data(conn, CSV_PATH)
            else:
                logger.info("No CSV file found, creating empty database")
        else:
            # Database exists, check schema
            logger.info("Database exists, checking schema")
            
            # Check if the tweets table exists
            c.execute('''SELECT name FROM sqlite_master WHERE type='table' AND name='tweets' ''')
            table_exists = c.fetchone()
            
            if not table_exists:
                # Create the table with the new schema (without tweet_embed_code)
                c.execute('''CREATE TABLE tweets
                             (id INTEGER PRIMARY KEY AUTOINCREMENT,
                              user_name TEXT,
                              link_to_tweet TEXT,
                              created_at TEXT,
                              created_at_parsed TIMESTAMP,
                              text TEXT,
                              received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            else:
                # Check if the created_at_parsed column exists
                c.execute('''PRAGMA table_info(tweets)''')
                columns = [column[1] for column in c.fetchall()]
                
                if 'created_at_parsed' not in columns:
                    # Add the created_at_parsed column
                    c.execute('''ALTER TABLE tweets ADD COLUMN created_at_parsed TIMESTAMP''')
                
                # Check if tweet_embed_code column exists and remove it if it does
                if 'tweet_embed_code' in columns:
                    logger.info("Removing tweet_embed_code column from database")
                    # SQLite doesn't support DROP COLUMN directly, so we need to:
                    # 1. Create a new table without the tweet_embed_code column
                    # 2. Copy data from the old table to the new table
                    # 3. Drop the old table
                    # 4. Rename the new table to the original name
                    
                    # Create new table without tweet_embed_code
                    c.execute('''CREATE TABLE tweets_new
                                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                  user_name TEXT,
                                  link_to_tweet TEXT,
                                  created_at TEXT,
                                  created_at_parsed TIMESTAMP,
                                  text TEXT,
                                  received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
                    
                    # Copy data from old table to new table
                    c.execute('''INSERT INTO tweets_new 
                                 (id, user_name, link_to_tweet, created_at, created_at_parsed, text, received_at)
                                 SELECT id, user_name, link_to_tweet, created_at, created_at_parsed, text, received_at
                                 FROM tweets''')
                    
                    # Drop old table
                    c.execute('''DROP TABLE tweets''')
                    
                    # Rename new table to original name
                    c.execute('''ALTER TABLE tweets_new RENAME TO tweets''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

def load_csv_data(conn, csv_path):
    """Load data from CSV file into the database."""
    try:
        c = conn.cursor()
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            # Use the first line to determine the dialect and fieldnames
            sample = csvfile.read(1024)
            csvfile.seek(0)
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample)
            reader = csv.DictReader(csvfile, dialect=dialect)
            
            count = 0
            for row in reader:
                # Map CSV column names to database column names
                # CSV has: CreatedAt, UserName, Text, LinkToTweet
                # Database expects: user_name, link_to_tweet, created_at, text
                user_name = row.get('UserName', row.get('user_name', ''))
                link_to_tweet = row.get('LinkToTweet', row.get('link_to_tweet', ''))
                created_at = row.get('CreatedAt', row.get('created_at', ''))
                text = row.get('Text', row.get('text', ''))
                
                # Parse the CreatedAt field
                created_at_parsed = parse_created_at(created_at)
                
                c.execute('''INSERT INTO tweets 
                             (user_name, link_to_tweet, created_at, created_at_parsed, text)
                             VALUES (?, ?, ?, ?, ?)''',
                          (user_name,
                           link_to_tweet,
                           created_at,
                           created_at_parsed,
                           text))
                count += 1
        
        conn.commit()
        logger.info(f"Loaded {count} records from {csv_path}")
    except Exception as e:
        logger.error(f"Failed to load CSV data: {e}")

def save_tweet_to_db(tweet_data):
    """Save tweet data to SQLite database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Parse the CreatedAt field
        created_at_str = tweet_data.get('CreatedAt', '')
        created_at_parsed = parse_created_at(created_at_str)
        
        c.execute('''INSERT INTO tweets 
                     (user_name, link_to_tweet, created_at, created_at_parsed, text)
                     VALUES (?, ?, ?, ?, ?)''',
                  (tweet_data.get('UserName', ''),
                   tweet_data.get('LinkToTweet', ''),
                   created_at_str,  # Keep original string
                   created_at_parsed,  # Parsed datetime
                   tweet_data.get('Text', '')))
        conn.commit()
        conn.close()
        logger.info("Tweet saved to database successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to save tweet to database: {e}")
        return False

def get_latest_tweets(limit=10):
    """Get the latest n tweets from the database, sorted by createdAt."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Order by created_at_parsed descending to get latest tweets first
        # Use created_at as fallback if created_at_parsed is NULL
        c.execute('''SELECT id, user_name, link_to_tweet, created_at, created_at_parsed, text, received_at
                     FROM tweets 
                     ORDER BY created_at_parsed DESC, created_at DESC 
                     LIMIT ?''', (limit,))
        rows = c.fetchall()
        conn.close()
        
        # Convert rows to list of dictionaries
        tweets = []
        for row in rows:
            tweets.append({
                'id': row[0],
                'user_name': row[1],
                'link_to_tweet': row[2],
                'created_at': row[3],
                'created_at_parsed': row[4],
                'text': row[5],
                'received_at': row[6]
            })
        
        return tweets
    except Exception as e:
        logger.error(f"Failed to fetch tweets from database: {e}")
        return []

def verify_signature(payload_body, secret_token, signature_header):
    """Verify that the payload was sent from IFTTT by validating SHA256.
    
    Args:
        payload_body: original request body to verify (bytes)
        secret_token: webhook secret token (str)
        signature_header: value of 'X-Signature' header (str)
    Returns:
        bool: True if the signature is valid, False otherwise
    """
    if not signature_header:
        return False
    expected_signature = hmac.new(
        secret_token.encode('utf-8'),
        payload_body,
        hashlib.sha256
    ).hexdigest()
    expected_signature = "sha256=" + expected_signature
    return hmac.compare_digest(expected_signature, signature_header)

@app.route('/ifttt/twitter', methods=['POST'])
def handle_ifttt_twitter_webhook():
    """Handle IFTTT Twitter webhook POST requests."""
    # Get request data
    signature_header = request.headers.get('X-Signature')
    payload = request.get_data()
    
    # Log the raw payload for debugging
    try:
        payload_json = request.get_json()
        payload_logger.debug(f"Received payload: {json.dumps(payload_json, indent=2)}")
        logger.debug("Payload logged to debug file")
    except Exception as e:
        payload_str = payload.decode('utf-8', errors='replace')
        payload_logger.debug(f"Received payload (raw): {payload_str}")
        logger.debug(f"Payload logged to debug file (raw): {e}")
    
    # Verify signature if required
    if REQUIRE_SIGNATURE:
        if not verify_signature(payload, SECRET_KEY, signature_header):
            logger.warning("Signature verification failed")
            payload_logger.debug("Signature verification failed")
            return jsonify({'error': 'Invalid signature'}), 401
    
    # Parse JSON payload
    try:
        data = request.get_json()
        if data is None:
            logger.error("Invalid JSON in IFTTT Twitter webhook request")
            payload_logger.debug("Invalid JSON in request")
            return jsonify({'error': 'Invalid JSON'}), 400
    except Exception as e:
        logger.error(f"Error parsing JSON: {str(e)}")
        payload_logger.debug(f"Error parsing JSON: {str(e)}")
        return jsonify({'error': 'Error parsing JSON'}), 400
    
    # Extract Twitter post information
    user_name = data.get('UserName', 'unknown')
    link_to_tweet = data.get('LinkToTweet', '')
    created_at = data.get('CreatedAt', '')
    text = data.get('Text', '')
    
    # Log the event
    logger.info(f"Received Twitter post from {user_name}")
    logger.info(f"Tweet: {text}")
    logger.info(f"Created at: {created_at}")
    logger.info(f"Link: {link_to_tweet}")
    
    # Save to database
    if save_tweet_to_db(data):
        logger.info("Tweet data saved to database")
        payload_logger.debug("Tweet data saved to database successfully")
    else:
        logger.error("Failed to save tweet data to database")
        payload_logger.debug("Failed to save tweet data to database")
        return jsonify({'error': 'Failed to save tweet data'}), 500
    
    # Process the Twitter post
    # Here you could add custom logic such as:
    # - Sending notifications
    # - Triggering other actions
    
    return jsonify({
        'message': f'Successfully processed Twitter post from {user_name}',
        'user_name': user_name,
        'created_at': created_at,
        'link_to_tweet': link_to_tweet
    })

@app.route('/tweets/latest', methods=['GET'])
def get_latest_tweets_route():
    """Get the latest n tweets from the database, sorted by createdAt."""
    # Get limit parameter from query string, default to 10
    try:
        limit = int(request.args.get('limit', 10))
        # Ensure limit is between 1 and 100
        limit = max(1, min(limit, 100))
    except (TypeError, ValueError):
        limit = 10
    
    # Fetch tweets from database
    tweets = get_latest_tweets(limit)
    
    if tweets is None:
        return jsonify({'error': 'Failed to fetch tweets'}), 500
    
    return jsonify({
        'tweets': tweets,
        'count': len(tweets),
        'limit': limit
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/', methods=['GET'])
def home():
    """Home endpoint with server information."""
    return jsonify({
        'message': 'IFTTT Twitter Webhook Server is running',
        'endpoints': {
            'ifttt_twitter': '/ifttt/twitter (POST)',
            'latest_tweets': '/tweets/latest (GET)',
            'health': '/health (GET)',
            'home': '/ (GET)'
        },
        'timestamp': datetime.now().isoformat()
    })

def main():
    """Main function to run the application."""
    # Initialize database
    init_db()
    
    port = config['server']['port']
    host = config['server']['host']
    debug = config['server']['debug']
    logger.info(f"Starting IFTTT Twitter webhook server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()