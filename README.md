# MyBGG

## Setup

```sh
pip install -r scripts/requirements.txt
python scripts/download_and_index.py --apikey YOUR_ALGOLIA_ADMIN_API_KEY`
```

## Updating Rankings

1. Save the ranking file as `rank.csv` 
2. Ensure the headings _don't_ have spaces in them!
3. Run `./scrips/update-config-from-csv.js`
