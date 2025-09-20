# IFTTT Twitter Webhook Server

A simple Python webhook server built with Flask that receives and processes Twitter post notifications from IFTTT.

## Project Structure

```
iftttwh/
├── config/                 # Configuration files
│   ├── config.json         # Main configuration file
│   └── .env.example        # Example environment variables
├── data/                   # Data files
│   ├── Tweets - Sheet1.csv          # Initial data CSV file
│   └── tweets.db           # SQLite database
├── logs/                   # Log files
├── migrations/             # Database migration scripts
│   ├── 000_init.sql         # Initial database schema
│   ├── 001_restore_tweets.sql # Restore tweets data
│   ├── apply_migration.py   # Python migration script
│   └── README.md           # Migration documentation
├── requirements/           # Python requirements
│   ├── base.txt            # Base requirements
│   └── dev.txt             # Development requirements
├── src/                    # Source code
│   ├── __init__.py
│   ├── main.py             # Entry point
│   └── iftttwh/            # Main package
│       ├── __init__.py
│       └── app.py          # Main application
├── tests/                  # Test files
│   ├── __init__.py
│   └── test_webhook.py     # Webhook tests
├── .env.example            # Example environment variables
├── .gitignore              # Git ignore file
├── docker-compose.yml      # Docker Compose configuration
├── Dockerfile              # Docker configuration
├── Makefile                # Makefile for common tasks
├── webhook_server.service  # Systemd service file
├── pyproject.toml          # Python project configuration
├── setup.py                # Setup script
├── migrate.sh             # Database migration script
└── README.md               # This file
```

## Features

- Receives HTTP POST requests from IFTTT webhooks
- Parses Twitter post data in the expected JSON format
- Saves tweet data to a local SQLite3 database
- Parses and stores the CreatedAt field as a datetime object
- Retrieves tweets sorted by createdAt timestamp (newest first)
- Logs incoming payloads to a separate debug file for troubleshooting
- Optional signature verification for security
- Logging of incoming requests
- Health check endpoint
- API endpoint to retrieve latest tweets
- API endpoint to search tweets by text (with special 'from:' handling)
- API endpoint for semantic search using ChromaDB embeddings
- Database-level duplicate prevention using UNIQUE constraints
- Database migration scripts for schema upgrades

## Expected Payload Format

The server expects JSON payloads from IFTTT in this format:

```json
{
    "UserName": "{{UserName}}",
    "LinkToTweet": "{{LinkToTweet}}",
    "CreatedAt": "{{CreatedAt}}",
    "Text": "{{Text}}"
}
```

The CreatedAt field is expected to be in a format like "September 08, 2025 at 02:39PM", which will be parsed and stored as a datetime object in the database.

## Setup

1. Install the required dependencies:
   ```bash
   make install
   ```
   or
   ```bash
   pip install -e .
   ```

This will install all required dependencies including Flask and ChromaDB.

2. Configure the server by modifying `config/config.json`:
   ```json
   {
     "server": {
       "host": "0.0.0.0",
       "port": 5000,
       "debug": false
     },
     "security": {
       "secret_key": "your_secret_key_here",
       "require_signature": false
     },
     "logging": {
       "level": "INFO",
       "file": "logs/app.log"
     },
     "database": {
       "path": "data/tweets.db",
       "csv_path": "data/Tweets - Sheet1.csv"
     },
     "debug_logging": {
       "payload_log_file": "logs/payload.log"
     }
   }
   ```

   Alternatively, you can set environment variables:
   ```bash
   export WEBHOOK_SECRET="your_secret_key_here"  # For signature verification
   export PORT=5000  # Server port (default: 5000)
   export DEBUG=True  # Enable debug mode (default: False)
   ```

3. Run the server:
   ```bash
   make run
   ```
   or
   ```bash
   python src/main.py
   ```

## Database Initialization

When the server starts, it will check if the SQLite database (`data/tweets.db` by default) exists:

1. If the database exists, it will be used as-is
2. If the database doesn't exist, the server will:
   - Create a new database file
   - Check for a CSV file (`data/Tweets - Sheet1.csv` by default) containing initial data
   - If the CSV file exists, load the data into the database
   - If no CSV file exists, create an empty database

This allows you to pre-populate the database with initial data when deploying the server.

## Database Migrations

The server uses a migration system to manage database schema changes. When the server starts, it automatically applies any pending migrations.

To manually apply migrations:

```bash
python3 migrations/apply_migration.py
```

This will:
1. Check if the database exists
2. Apply any needed migrations
3. Add UNIQUE constraints to prevent future duplicates

The migration system uses a clean schema approach with the following migrations:
- `000_init.sql`: Initializes the database with a clean schema
- `001_restore_tweets.sql`: Placeholder for restoring tweets data

See [migrations/README.md](migrations/README.md) for more details.

## CSV File Format

If you want to pre-populate the database with initial data, create a CSV file with the following format (no header row):

```csv
CreatedAt,UserName,Text,LinkToTweet
```

Example:
```csv
"September 08, 2025 at 02:39PM",@FirstSquawk,S. Korean FM: Trade negotiations with U.S. face slight delay due to concerns over U.S.-Japan-style agreement,https://twitter.com/FirstSquawk/status/1964941617305100502
"September 08, 2025 at 02:56PM",@FirstSquawk,"China's oil demand to peak by 2027, with 2025 consumption up 100,000 bpd — government researcher",https://twitter.com/FirstSquawk/status/1964946041968656859
```

The server assumes the CSV file has no header row and that columns are in the fixed order:
1. CreatedAt
2. UserName
3. Text
4. LinkToTweet

Additional columns are ignored. The server will parse the CreatedAt field and store it as a datetime object in the database.

## Duplicate Prevention

The server includes database-level duplicate prevention using UNIQUE constraints. A tweet is considered a duplicate if it has the same:
- UserName
- LinkToTweet
- Text

When a duplicate is detected, the database will automatically reject it, preventing duplicate tweets from being saved. This works even with concurrent requests, eliminating race conditions that could previously cause duplicates.

## Payload Debug Logging

For debugging purposes, all incoming payloads to the `/ifttt/twitter` endpoint are logged to a separate file (`logs/payload.log` by default). This can be helpful for troubleshooting issues with IFTTT webhook payloads.

The debug log will contain the full JSON payload as received from IFTTT, formatted for readability.

## Endpoints

- `POST /ifttt/twitter` - IFTTT Twitter webhook endpoint
- `GET /tweets/latest` - Get latest tweets (accepts optional `limit` parameter)
- `GET /tweets/search` - Search tweets by text (with special 'from:' handling)
- `GET /tweets/semantic-search` - Search tweets semantically using text embeddings
- `GET /health` - Health check endpoint
- `GET /` - Server information endpoint

## IFTTT Integration

To use this webhook server with IFTTT:

1. Create an IFTTT applet with the "New tweet by you" trigger
2. Set the webhook URL to `http://your-server-address:5000/ifttt/twitter`
3. Configure the JSON payload with these fields:
   ```json
   {
     "UserName": "{{UserName}}",
     "LinkToTweet": "{{LinkToTweet}}",
     "CreatedAt": "{{CreatedAt}}",
     "Text": "{{Text}}"
   }
   ```

## Retrieving Tweets

To retrieve the latest tweets, make a GET request to `/tweets/latest`:

```bash
# Get latest 10 tweets (default)
curl http://localhost:5000/tweets/latest

# Get latest 5 tweets
curl http://localhost:5000/tweets/latest?limit=5

# Get latest 20 tweets (maximum limit is 100)
curl http://localhost:5000/tweets/latest?limit=20
```

The response will be in JSON format:
```json
{
  "tweets": [
    {
      "id": 1,
      "user_name": "@FirstSquawk",
      "link_to_tweet": "https://twitter.com/FirstSquawk/status/1964941617305100502",
      "created_at": "September 08, 2025 at 02:39PM",
      "created_at_parsed": "2025-09-08T14:39:00",
      "text": "S. Korean FM: Trade negotiations with U.S. face slight delay due to concerns over U.S.-Japan-style agreement",
      "received_at": "2025-09-08 15:39:24"
    }
  ],
  "count": 1,
  "limit": 10
}
```

Tweets are sorted by the createdAt timestamp in descending order (newest first), which provides a more logical ordering than sorting by insertion ID.

## Searching Tweets

To search for tweets, make a GET request to `/tweets/search` with a query parameter:

```bash
# Search for tweets containing "China" in either username or text
curl "http://localhost:5000/tweets/search?query=China"

# Search for tweets from a specific user using 'from:' prefix
curl "http://localhost:5000/tweets/search?query=from:FirstSquawk"

# Limit results (default is 10, max is 100)
curl "http://localhost:5000/tweets/search?query=China&limit=5"
```

The search endpoint has special handling for the 'from:' prefix:
- If the search query starts with 'from:', the remainder is used as a fuzzy username filter
- Otherwise, the search query is used to match both username and text fields

The response will be in JSON format:
```json
{
  "tweets": [
    {
      "id": 2,
      "user_name": "@FirstSquawk",
      "link_to_tweet": "https://twitter.com/FirstSquawk/status/1964946041968656859",
      "created_at": "September 08, 2025 at 02:56PM",
      "created_at_parsed": "2025-09-08T14:56:00",
      "text": "China's oil demand to peak by 2027, with 2025 consumption up 100,000 bpd — government researcher",
      "received_at": "2025-09-08 15:39:24"
    }
  ],
  "count": 1,
  "limit": 10,
  "search_params": {
    "query": "China"
  }
}
```

Searches use partial matching (LIKE queries) and will match the search query in either the username or text fields (or just the username when using 'from:'). Results are sorted by the createdAt timestamp in descending order (newest first).

## Semantic Search

The server now includes semantic search capabilities using ChromaDB. This allows you to find tweets that are semantically similar to your query, rather than just matching keywords.

To perform a semantic search, make a GET request to `/tweets/semantic-search` with a query parameter:

```bash
# Search for tweets semantically related to "oil prices"
curl "http://localhost:5000/tweets/semantic-search?query=oil prices"

# Limit results (default is 10, max is 100)
curl "http://localhost:5000/tweets/semantic-search?query=oil prices&limit=5"
```

The semantic search endpoint returns tweets sorted by semantic similarity to your query, with the most similar tweets first. 

Example response:
```json
{
  "tweets": [
    {
      "id": 2,
      "user_name": "@FirstSquawk",
      "link_to_tweet": "https://twitter.com/FirstSquawk/status/1964946041968656859",
      "created_at": "September 08, 2025 at 02:56PM",
      "created_at_parsed": "2025-09-08T14:56:00",
      "text": "China's oil demand to peak by 2027, with 2025 consumption up 100,000 bpd — government researcher",
      "received_at": "2025-09-08 15:39:24"
    }
  ],
  "count": 1,
  "limit": 10,
  "search_params": {
    "query": "oil prices"
  }
}
```

Note that semantic search requires ChromaDB to be installed. ChromaDB uses the `all-MiniLM-L6-v2` model for generating embeddings, which provides efficient similarity search capabilities for semantic search functionality.

## Security

To enable signature verification:
1. Set the `secret_key` in `config/config.json` or the `WEBHOOK_SECRET` environment variable
2. Set `require_signature` to `true` in `config/config.json`
3. The server will automatically verify the signature of incoming requests

If no secret is configured, signature verification will be skipped.

## Logging

All requests are logged to both the console and the file specified in `config/config.json` (default: `logs/app.log`).

Additionally, all incoming payloads to the `/ifttt/twitter` endpoint are logged to a separate debug file (`logs/payload.log` by default) for troubleshooting purposes.

## Testing

You can test the webhook endpoint using the included test script:

```bash
make test
```
or
```bash
python -m pytest tests/ -v
```

Or using curl:

```bash
curl -X POST http://localhost:5000/ifttt/twitter \
  -H "Content-Type: application/json" \
  -d '{
    "UserName": "testuser",
    "LinkToTweet": "https://twitter.com/testuser/status/123456789",
    "CreatedAt": "September 08, 2025 at 02:39PM",
    "Text": "This is a test tweet from IFTTT"
  }'
```

## Database

Tweet data is stored in a local SQLite3 database (`data/tweets.db` by default). The database is automatically created on first run and contains two tables with the following structure:

```sql
CREATE TABLE tweets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_name TEXT,
  link_to_tweet TEXT,
  created_at TEXT,
  created_at_parsed TIMESTAMP,
  text TEXT,
  received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_name, link_to_tweet, text)
);

CREATE INDEX idx_tweets_created_at_parsed ON tweets(created_at_parsed);
CREATE INDEX idx_tweets_user_name ON tweets(user_name);
CREATE INDEX idx_tweets_text ON tweets(text);
CREATE INDEX idx_tweets_link_to_tweet ON tweets(link_to_tweet);
CREATE INDEX idx_tweets_created_at ON tweets(created_at);
```

The `created_at_parsed` field contains the parsed datetime version of the `created_at` field, which makes it easier to perform date-based queries. The UNIQUE constraint on `user_name`, `link_to_tweet`, and `text` prevents duplicate tweets from being saved, even with concurrent requests.

Semantic embeddings are stored using ChromaDB in the `data/chroma_db` directory. ChromaDB provides efficient similarity search capabilities for semantic search functionality.

## Common Tasks

The project includes a Makefile with common tasks:

```bash
make install     # Install dependencies
make run         # Run the application
make test        # Run tests
make clean       # Clean up temporary files
make lint        # Run code linter
make format      # Format code with black
make docker      # Build Docker image
make migrate    # Apply database migrations
make dump-csv   # Dump tweets database to CSV
make restore-csv # Restore tweets from CSV to database
```

### Database Backup and Restore

You can backup and restore the database using the provided scripts. See [docs/database_backup_restore.md](docs/database_backup_restore.md) for detailed instructions.

## Deployment

### Docker

You can run the webhook server using Docker:

```bash
# Build the image
make docker
# or
docker build -t ifttt-twitter-webhook .

# Run the container
docker run -d -p 5000:5000 --name ifttt-twitter-webhook ifttt-twitter-webhook
```

Or using docker-compose:
```bash
# Start the application
docker-compose up -d

# Stop the application
docker-compose down

# View logs
docker-compose logs -f
```

The Docker image is optimized for CPU-only operation and does not include any NVIDIA CUDA dependencies, making it suitable for lightweight VPS deployments.

### Systemd Service

### Systemd Service

A systemd service file is included for Linux systems. To install:

1. Copy the service file to `/etc/systemd/system/`:
   ```bash
   sudo cp webhook_server.service /etc/systemd/system/
   ```

2. Edit the service file to match your configuration:
   ```bash
   sudo nano /etc/systemd/system/webhook_server.service
   ```

3. Enable and start the service:
   ```bash
   sudo systemctl enable webhook_server
   sudo systemctl start webhook_server
   ```