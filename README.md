# IFTTT Twitter Webhook Server

A simple Python webhook server built with Flask that receives and processes Twitter post notifications from IFTTT.

## Project Structure

```
iftttwh/
├── config/                 # Configuration files
│   ├── config.json         # Main configuration file
│   └── .env.example        # Example environment variables
├── data/                   # Data files
│   ├── tweets.csv          # Initial data CSV file
│   └── tweets.db           # SQLite database
├── logs/                   # Log files
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
├── Dockerfile              # Docker configuration
├── Makefile                # Makefile for common tasks
├── webhook_server.service  # Systemd service file
├── pyproject.toml          # Python project configuration
├── setup.py                # Setup script
└── README.md               # This file
```

## Features

- Receives HTTP POST requests from IFTTT webhooks
- Parses Twitter post data in the expected JSON format
- Saves tweet data to a local SQLite3 database
- Parses and stores the CreatedAt field as a datetime object
- Loads initial data from CSV file if database doesn't exist
- Retrieves tweets sorted by createdAt timestamp (newest first)
- Logs incoming payloads to a separate debug file for troubleshooting
- Optional signature verification for security
- Logging of incoming requests
- Health check endpoint
- API endpoint to retrieve latest tweets

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
   pip install -r requirements/base.txt
   ```

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
       "csv_path": "data/tweets.csv"
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
   - Check for a CSV file (`data/tweets.csv` by default) containing initial data
   - If the CSV file exists, load the data into the database
   - If no CSV file exists, create an empty database

This allows you to pre-populate the database with initial data when deploying the server.

## CSV File Format

If you want to pre-populate the database with initial data, create a CSV file with the following columns:

```csv
CreatedAt,UserName,Text,LinkToTweet
```

Example:
```csv
CreatedAt,UserName,Text,LinkToTweet
"September 08, 2025 at 02:39PM",@FirstSquawk,S. Korean FM: Trade negotiations with U.S. face slight delay due to concerns over U.S.-Japan-style agreement,https://twitter.com/FirstSquawk/status/1964941617305100502
"September 08, 2025 at 02:56PM",@FirstSquawk,"China's oil demand to peak by 2027, with 2025 consumption up 100,000 bpd — government researcher",https://twitter.com/FirstSquawk/status/1964946041968656859
```

The server will automatically map these column names to the database fields. Additional columns like `TweetEmbedCode` are optional and will be set to empty strings if not present.

## Payload Debug Logging

For debugging purposes, all incoming payloads to the `/ifttt/twitter` endpoint are logged to a separate file (`logs/payload.log` by default). This can be helpful for troubleshooting issues with IFTTT webhook payloads.

The debug log will contain the full JSON payload as received from IFTTT, formatted for readability.

## Endpoints

- `POST /ifttt/twitter` - IFTTT Twitter webhook endpoint
- `GET /tweets/latest` - Get latest tweets (accepts optional `limit` parameter)
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

Tweet data is stored in a local SQLite3 database (`data/tweets.db` by default). The database is automatically created on first run and contains a single table with the following structure:

```sql
CREATE TABLE tweets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_name TEXT,
  link_to_tweet TEXT,
  created_at TEXT,
  created_at_parsed TIMESTAMP,
  text TEXT,
  received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

The `created_at_parsed` field contains the parsed datetime version of the `created_at` field, which makes it easier to perform date-based queries.

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
```

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