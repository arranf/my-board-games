import json

from mybgg.downloader import Downloader
from mybgg.indexer import Indexer


def main(args):
    SETTINGS = json.load(open("./config.json", "rb"))

    downloader = Downloader(
        project_name=SETTINGS["project"]["name"],
        cache_bgg=args.cache_bgg,
        debug=args.debug,
    )
    collection = downloader.collection(
        user_name=SETTINGS["boardgamegeek"]["user_name"],
        password=args.password,
        additional_info=SETTINGS["additional"],
        extra_params=SETTINGS["boardgamegeek"]["extra_params"],
        exclude=SETTINGS["excluded"]
    )
    
    num_games = len(collection)
    num_expansions = sum([len(game.expansions) for game in collection])
    print(f"Imported {num_games} games and {num_expansions} expansions from boardgamegeek.")
    ratings = list(map(lambda bg: bg.rating, collection))
    none_rating_count = sum(x is None for x in ratings)
    if none_rating_count > num_games / 2.0:
        assert False, "Too many games have no rating, is BGG working correctly?"

    if not len(collection):
        assert False, "No games imported, is the boardgamegeek part of config.json correctly set?"

    if not args.no_indexing:
        indexer = Indexer(
            app_address=SETTINGS["meilisearch"]["app_address"],
            apikey=args.apikey,
            index_name=SETTINGS["meilisearch"]["index_name"],
        )
        indexer.add_objects(collection)
        indexer.delete_objects_not_in(collection)

        print(f"Indexed {num_games} games and {num_expansions} expansions in meilisearch, and removed everything else.")
    else:
        print("Skipped indexing.")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Download and index some boardgames')
    parser.add_argument(
        '--apikey',
        type=str,
        required=True,
        help='The admin api key for your meilisearch site'
    )
    parser.add_argument(
        '--password',
        type=str,
        required=True,
        help='Your BGG password'
    )
    parser.add_argument(
        '--no_indexing',
        action='store_true',
        help=(
            "Skip indexing in meilisearch. This is useful during development"
            ", when you want to fetch data from BGG over and over again, "
            "and don't want to use up your indexing quota with meilisearch."
        )
    )
    parser.add_argument(
        '--cache_bgg',
        action='store_true',
        help=(
            "Enable a cache for all BGG calls. This makes script run very "
            "fast the second time it's run."
        )
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help="Print debug information, such as requests made and responses received."
    )

    args = parser.parse_args()

    main(args)
