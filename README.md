# My Board Games

## Setup

```sh
pip install -r scripts/requirements.txt
python scripts/download_and_index.py --apikey YOUR_MEILISEARCH_ADMIN_API_KEY`
```

## Running (debug)

Remember to use `\` to escape special characters in your password
`python scripts/download_and_index.py --no_indexing --apikey fake --password yourpassword`

## Updating Rankings

1. Save the ranking file as `rank.csv`
2. Ensure the headings _don't_ have spaces in them!
3. Run `./scrips/update-config-from-csv.js`

## Config

`config.json` stores a map of game ids to description, personal rank, and optionally a "base game". Adding a "base game" makes the game an expansion of that game.
