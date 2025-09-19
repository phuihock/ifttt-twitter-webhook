# Database Backup and Restore

This document describes how to backup and restore the tweets database using the provided scripts.

## Dump Tweets to CSV

The `dump_tweets_to_csv.py` script exports all tweets from the SQLite database to a CSV file.

### Usage

```bash
# Using make
make dump-csv

# Direct execution
python3 dump_tweets_to_csv.py

# With custom output file
python3 dump_tweets_to_csv.py /path/to/output.csv

# With custom database and output file
python3 dump_tweets_to_csv.py /path/to/output.csv /path/to/database.db
```

### Output Format

The CSV file will have the following columns:
- `CreatedAt`: The original timestamp from Twitter
- `UserName`: The Twitter username
- `Text`: The tweet text
- `LinkToTweet`: The URL to the original tweet

## Restore Tweets from CSV

The `restore_tweets_from_csv.py` script imports tweets from a CSV file to the SQLite database.

### Usage

```bash
# Using make
make restore-csv

# Direct execution
python3 restore_tweets_from_csv.py

# With custom input file
python3 restore_tweets_from_csv.py /path/to/input.csv

# With custom CSV file and database
python3 restore_tweets_from_csv.py /path/to/input.csv /path/to/database.db
```

### Input Format

The script expects a CSV file with the following columns:
- `CreatedAt`
- `UserName`
- `Text`
- `LinkToTweet`

The first row should be a header row with these column names.

## Use Cases

1. **Backup**: Regularly dump tweets to CSV for safekeeping
2. **Migration**: Move tweets between different installations
3. **Reinitialization**: Start with a clean database and restore from backup
4. **Data Analysis**: Export tweets for analysis in other tools
5. **Transfer**: Share tweets with other systems or users