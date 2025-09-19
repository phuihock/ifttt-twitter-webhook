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

# Import required libraries for ChromaDB (now a prerequisite)
import chromadb
from chromadb.utils import embedding_functions

# Initialize ChromaDB client (now a prerequisite)
CHROMA_CLIENT = chromadb.PersistentClient(path="data/chroma_db")
SENTENCE_TRANSFORMER_EF = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
CHROMA_COLLECTION = CHROMA_CLIENT.get_or_create_collection(
    name="tweets",
    embedding_function=SENTENCE_TRANSFORMER_EF
)
CHROMADB_ENABLED = True


# Load configuration
def load_config():
    """Load configuration from config.json file."""
    try:
        with open("config/config.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # Default configuration for Twitter webhook
        return {
            "server": {"host": "0.0.0.0", "port": 5000, "debug": False},
            "security": {
                "secret_key": os.environ.get("WEBHOOK_SECRET", "default_secret_key"),
                "require_signature": False,
            },
            "logging": {"level": "INFO", "file": "logs/app.log"},
            "database": {
                "path": "data/tweets.db",
                "csv_path": "data/Tweets - Sheet1.csv",
            },
            "debug_logging": {"payload_log_file": "logs/payload.log"},
        }


config = load_config()

# Configure logging
log_level = getattr(logging, config["logging"]["level"].upper(), logging.INFO)
logging.basicConfig(
    level=log_level,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(config["logging"]["file"]), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Configure payload debug logging
payload_logger = logging.getLogger("payload_debug")
payload_logger.setLevel(logging.DEBUG)
payload_log_handler = logging.FileHandler(config["debug_logging"]["payload_log_file"])
payload_log_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
payload_logger.addHandler(payload_log_handler)
payload_logger.propagate = False  # Don't propagate to other loggers

# Log semantic search status after logger is defined
logger.info("ChromaDB semantic search is enabled")

if CHROMADB_ENABLED:
    logger.info("ChromaDB semantic search is enabled")

app = Flask(__name__)

# Get secret key from config or environment variables
SECRET_KEY = config["security"]["secret_key"]
REQUIRE_SIGNATURE = config["security"]["require_signature"]
DB_PATH = config["database"]["path"]
CSV_PATH = config["database"]["csv_path"]


def parse_created_at(created_at_str):
    """Parse the CreatedAt field from IFTTT into a datetime object."""
    if not created_at_str or created_at_str == "":
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
    """Initialize the database using the migration system."""
    try:
        # Import and run the migration system
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
        from migrations.apply_migration import MigrationManager
        
        # Create migration manager and apply all pending migrations
        manager = MigrationManager(DB_PATH)
        if manager.apply_all_pending():
            logger.info("Database migrations applied successfully")
            
            # Load data from CSV if it exists
            if os.path.exists(CSV_PATH):
                logger.info(f"Loading initial data from {CSV_PATH}")
                conn = sqlite3.connect(DB_PATH)
                load_csv_data(conn, CSV_PATH)
                conn.close()
                
                # After loading data, populate ChromaDB if enabled
                if CHROMADB_ENABLED:
                    populate_chromadb()
            else:
                logger.info("No CSV file found, database is empty")
        else:
            logger.error("Failed to apply database migrations")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")


def load_csv_data(conn, csv_path):
    """Load data from CSV file into the database.

    Assumes CSV has a header row and columns in order:
    CreatedAt, UserName, Text, LinkToTweet
    """
    try:
        c = conn.cursor()
        with open(csv_path, "r", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            
            # Skip header row
            next(reader, None)
            
            count = 0
            for row in reader:
                # Skip empty rows
                if not row or len(row) < 4:
                    continue

                # Extract fields in the expected order:
                # CreatedAt, UserName, Text, LinkToTweet
                created_at = row[0] if len(row) > 0 else ""
                user_name = row[1] if len(row) > 1 else ""
                text = row[2] if len(row) > 2 else ""
                link_to_tweet = row[3] if len(row) > 3 else ""

                # Parse the CreatedAt field
                created_at_parsed = parse_created_at(created_at)

                try:
                    c.execute(
                        """INSERT INTO tweets
                                 (user_name, link_to_tweet, created_at, created_at_parsed, text)
                                 VALUES (?, ?, ?, ?, ?)""",
                        (user_name, link_to_tweet, created_at, created_at_parsed, text),
                    )
                    count += 1
                except sqlite3.IntegrityError:
                    # Duplicate found in CSV, skip it
                    logger.debug(
                        f"Skipping duplicate tweet from CSV: {user_name}, {text[:50]}..."
                    )
                    continue

        conn.commit()
        logger.info(f"Loaded {count} records from {csv_path}")
    except Exception as e:
        logger.error(f"Failed to load CSV data: {e}")


def save_tweet_to_db(tweet_data):
    """Save tweet data to SQLite database, using database-level duplicate prevention."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Extract data from tweet_data
        user_name = tweet_data.get("UserName", "")
        link_to_tweet = tweet_data.get("LinkToTweet", "")
        text = tweet_data.get("Text", "")

        # Parse the CreatedAt field
        created_at_str = tweet_data.get("CreatedAt", "")
        created_at_parsed = parse_created_at(created_at_str)

        # Try to insert the tweet - database will enforce uniqueness
        try:
            c.execute(
                """INSERT INTO tweets
                         (user_name, link_to_tweet, created_at, created_at_parsed, text)
                         VALUES (?, ?, ?, ?, ?)""",
                (
                    user_name,
                    link_to_tweet,
                    created_at_str,  # Keep original string
                    created_at_parsed,  # Parsed datetime
                    text,
                ),
            )
            tweet_id = c.lastrowid
            conn.commit()

            # Add to ChromaDB
            try:
                CHROMA_COLLECTION.add(
                    documents=[text],
                    metadatas=[{
                        "tweet_id": tweet_id,
                        "user_name": user_name,
                        "link_to_tweet": link_to_tweet,
                        "created_at": created_at_str,
                        "created_at_parsed": created_at_parsed
                    }],
                    ids=[str(tweet_id)]
                )
                logger.debug(f"Tweet added to ChromaDB collection: {tweet_id}")
            except Exception as e:
                logger.error(
                    f"Failed to add tweet to ChromaDB collection {tweet_id}: {e}"
                )

            conn.close()
            logger.info("Tweet saved to database successfully")
            return True
        except sqlite3.IntegrityError as e:
            # Duplicate detected by database constraint
            conn.close()
            logger.info(
                f"Duplicate tweet prevented by database constraint for user {user_name}"
            )
            return True  # Return True to indicate successful processing (even though we didn't save)
    except Exception as e:
        logger.error(f"Failed to save tweet to database: {e}")
        return False


def search_tweets(search_text=None, limit=10):
    """Search for tweets by search_text with special 'from:' handling.

    Args:
        search_text (str, optional): Text to search for. If it starts with 'from:',
                                    the remainder is used as a fuzzy UserName filter.
        limit (int): Maximum number of tweets to return (default: 10)

    Returns:
        list: List of tweet dictionaries
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Build query based on provided parameters
        query = """SELECT id, user_name, link_to_tweet, created_at, created_at_parsed, text, received_at
                   FROM tweets WHERE 1=1"""
        params = []

        if search_text:
            # Check if search_text starts with 'from:'
            if search_text.startswith("from:"):
                # Extract the username part and use it for fuzzy matching
                username_filter = search_text[5:]  # Remove 'from:' prefix
                query += " AND user_name LIKE ?"
                params.append(f"%{username_filter}%")
            else:
                # Regular search in both user_name and text fields
                query += " AND (user_name LIKE ? OR text LIKE ?)"
                params.append(f"%{search_text}%")
                params.append(f"%{search_text}%")

        query += " ORDER BY created_at_parsed DESC, created_at DESC LIMIT ?"
        params.append(limit)

        c.execute(query, params)
        rows = c.fetchall()
        conn.close()

        # Convert rows to list of dictionaries
        tweets = []
        for row in rows:
            tweets.append(
                {
                    "id": row[0],
                    "user_name": row[1],
                    "link_to_tweet": row[2],
                    "created_at": row[3],
                    "created_at_parsed": row[4],
                    "text": row[5],
                    "received_at": row[6],
                }
            )

        return tweets
    except Exception as e:
        logger.error(f"Failed to search tweets: {e}")
        return []


def get_latest_tweets(limit=10):
    """Get the latest n tweets from the database, sorted by createdAt."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Order by created_at_parsed descending to get latest tweets first
        # Use created_at as fallback if created_at_parsed is NULL
        c.execute(
            """SELECT id, user_name, link_to_tweet, created_at, created_at_parsed, text, received_at
                     FROM tweets
                     ORDER BY created_at_parsed DESC, created_at DESC
                     LIMIT ?""",
            (limit,),
        )
        rows = c.fetchall()
        conn.close()

        # Convert rows to list of dictionaries
        tweets = []
        for row in rows:
            tweets.append(
                {
                    "id": row[0],
                    "user_name": row[1],
                    "link_to_tweet": row[2],
                    "created_at": row[3],
                    "created_at_parsed": row[4],
                    "text": row[5],
                    "received_at": row[6],
                }
            )

        return tweets
    except Exception as e:
        logger.error(f"Failed to fetch tweets from database: {e}")
        return []


def populate_chromadb():
    """Populate ChromaDB with existing tweets from SQLite database."""
    try:
        logger.info("Populating ChromaDB with existing tweets...")
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get all tweets from database
        c.execute(
            """SELECT id, user_name, link_to_tweet, created_at, created_at_parsed, text
                     FROM tweets
                     ORDER BY created_at_parsed DESC, created_at DESC"""
        )
        rows = c.fetchall()
        conn.close()

        if not rows:
            logger.info("No tweets found to populate ChromaDB")
            return

        # Prepare data for ChromaDB
        documents = []
        metadatas = []
        ids = []
        
        for row in rows:
            tweet_id, user_name, link_to_tweet, created_at, created_at_parsed, text = row
            
            # Skip if text is empty
            if not text:
                continue
                
            documents.append(text)
            metadatas.append({
                "tweet_id": tweet_id,
                "user_name": user_name,
                "link_to_tweet": link_to_tweet,
                "created_at": created_at,
                "created_at_parsed": created_at_parsed
            })
            ids.append(str(tweet_id))

        # Add to ChromaDB in batches to avoid memory issues
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch_documents = documents[i:i+batch_size]
            batch_metadatas = metadatas[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]
            
            CHROMA_COLLECTION.add(
                documents=batch_documents,
                metadatas=batch_metadatas,
                ids=batch_ids
            )
            
        logger.info(f"Successfully populated ChromaDB with {len(documents)} tweets")
    except Exception as e:
        logger.error(f"Failed to populate ChromaDB: {e}")


def semantic_search_tweets(query_text, limit=10):
    """Search for tweets using semantic similarity with ChromaDB.
    
    Args:
        query_text (str): Text to search for semantically
        limit (int): Maximum number of tweets to return (default: 10)
        
    Returns:
        list: List of tweet dictionaries with similarity scores
    """
    try:
        logger.debug(f"Performing semantic search with ChromaDB: {query_text}")
        results = CHROMA_COLLECTION.query(
            query_texts=[query_text],
            n_results=limit
        )
        
        # Convert results to the expected format
        tweets = []
        for i in range(len(results['ids'][0])):
            metadata = results['metadatas'][0][i]
            tweets.append({
                "id": metadata["tweet_id"],
                "user_name": metadata["user_name"],
                "link_to_tweet": metadata["link_to_tweet"],
                "created_at": metadata["created_at"],
                "created_at_parsed": metadata["created_at_parsed"],
                "text": results['documents'][0][i],
                "similarity": results['distances'][0][i] if 'distances' in results else None
            })
        
        return tweets
    except Exception as e:
        logger.error(f"Failed to perform semantic search with ChromaDB: {e}")
        return []


def verify_signature(payload_body, secret_token, signature_header):
    """Verify that the payload was sent from IFTTT by validating SHA256.

    Args:
        payload_body: original request body to verify (bytes)
        secret_token: webhook secret token (str)
        signature_header: value of X-Signature header (str)
    Returns:
        bool: True if the signature is valid, False otherwise
    """
    if not signature_header:
        return False
    expected_signature = hmac.new(
        secret_token.encode("utf-8"), payload_body, hashlib.sha256
    ).hexdigest()
    expected_signature = "sha256=" + expected_signature
    return hmac.compare_digest(expected_signature, signature_header)


@app.route("/ifttt/twitter", methods=["POST"])
def handle_ifttt_twitter_webhook():
    # Handle IFTTT Twitter webhook POST requests
    # Get request data
    signature_header = request.headers.get("X-Signature")
    payload = request.get_data()
def get_latest_tweets_route():
    # Get the latest n tweets from the database, sorted by createdAt
    # Get limit parameter from query string, default to 10
    try:
        limit = int(request.args.get("limit", 10))
        # Ensure limit is between 1 and 100
        limit = max(1, min(limit, 100))
    except (TypeError, ValueError):
        limit = 10

    # Fetch tweets from database
    tweets = get_latest_tweets(limit)

    if tweets is None:
        return jsonify({"error": "Failed to fetch tweets"}), 500

    return jsonify({"tweets": tweets, "count": len(tweets), "limit": limit})


@app.route("/tweets/search", methods=["GET"])
def search_tweets_route():
    # Search for tweets by query with special from: handling
    # Get parameters from query string
    search_text = request.args.get("query")

    # Get limit parameter from query string, default to 10
    try:
        limit = int(request.args.get("limit", 10))
        # Ensure limit is between 1 and 100
        limit = max(1, min(limit, 100))
    except (TypeError, ValueError):
        limit = 10

    # Validate that search text parameter is provided
    if not search_text:
        return jsonify({"error": "Search query parameter is required"}), 400

    # Search tweets
    tweets = search_tweets(search_text=search_text, limit=limit)

    if tweets is None:
        return jsonify({"error": "Failed to search tweets"}), 500

    return jsonify(
        {
            "tweets": tweets,
            "count": len(tweets),
            "limit": limit,
            "search_params": {"query": search_text},
        }
    )


@app.route("/tweets/semantic-search", methods=["GET"])
def semantic_search_tweets_route():
    # Search for tweets using semantic similarity
    # Get parameters from query string
    query_text = request.args.get("query")

    # Get limit parameter from query string, default to 10
    try:
        limit = int(request.args.get("limit", 10))
        # Ensure limit is between 1 and 100
        limit = max(1, min(limit, 100))
    except (TypeError, ValueError):
        limit = 10

    # Validate that query text parameter is provided
    if not query_text:
        return jsonify({"error": "Query parameter is required"}), 400

    # Search tweets semantically
    tweets = semantic_search_tweets(query_text=query_text, limit=limit)

    return jsonify(
        {
            "tweets": tweets,
            "count": len(tweets),
            "limit": limit,
            "search_params": {"query": query_text},
        }
    )


@app.route("/health", methods=["GET"])
def health_check():
    # Health check endpoint
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


@app.route("/", methods=["GET"])
def home():
    # Home endpoint with server information
    return jsonify(
        {
            "message": "IFTTT Twitter Webhook Server is running",
            "endpoints": {
                "ifttt_twitter": "/ifttt/twitter (POST)",
                "latest_tweets": "/tweets/latest (GET)",
                "search_tweets": "/tweets/search (GET)",
                "semantic_search_tweets": "/tweets/semantic-search (GET)",
                "health": "/health (GET)",
                "home": "/ (GET)",
            },
            "timestamp": datetime.now().isoformat(),
        }
    )
    main()


def main():
    # Main function to run the application
    # Initialize database
    init_db()

    port = config["server"]["port"]
    host = config["server"]["host"]
    debug = config["server"]["debug"]
    logger.info(f"Starting IFTTT Twitter webhook server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
