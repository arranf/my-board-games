from mybgg.bgg_client import BGGClient
from mybgg.bgg_client import CacheBackendSqlite
from mybgg.models import BoardGame


class Downloader():
    def __init__(self, project_name, cache_bgg, debug=False):
        if cache_bgg:
            self.client = BGGClient(
                cache=CacheBackendSqlite(
                    path=f"{project_name}-cache.sqlite",
                    ttl=60 * 60 * 24,
                ),
                debug=debug,
            )
        else:
            self.client = BGGClient(
                debug=debug,
            )

    def collection(self, user_name, password, additional_info, extra_params):
        self.client.login(user_name=user_name, password=password)
        collection_data = []
        plays_data = []

        if isinstance(extra_params, list):
            for params in extra_params:
                collection_data += self.client.collection(
                    user_name=user_name,
                    **params,
                )
        else:
            collection_data = self.client.collection(
                user_name=user_name,
                **extra_params,
            )

        plays_data = self.client.plays(
            user_name=user_name,
        )

        game_list_data = self.client.game_list([game_in_collection["id"] for game_in_collection in collection_data])
        game_id_to_personal_rating = {game["id"]: game["personal_rating"] for game in collection_data}
        game_id_to_tags = {game["id"]: game["tags"] for game in collection_data}
        game_id_to_image = {game["id"]: game["image_version"] or game["image"] for game in collection_data}
        game_id_to_thumbnail = {game["id"]: game["thumbnail"] for game in collection_data}
        game_id_to_numplays = {game["id"]: game["numplays"] for game in collection_data}
        game_id_to_lastmodified = {game["id"]: game["lastmodified"] for game in collection_data}

        game_id_to_players = {game["id"]: [] for game in collection_data}
        for play in plays_data:
            if play["game"]["gameid"] in game_id_to_players:
                game_id_to_players[play["game"]["gameid"]].extend(play["players"])
                game_id_to_players[play["game"]["gameid"]] = list(set(game_id_to_players[play["game"]["gameid"]]))

        # Handle custom mapping of games as expansions
        if additional_info is not None:
            for game_data in game_list_data:
                additional_game_info = additional_info.get(str(game_data["id"]))
                if additional_game_info is not None and "base_game_id" in additional_game_info:
                     game_data["type"] = "boardgameexpansion"
                     game_data["expansions"] = [{"inbound": True, "id": additional_game_info["base_game_id"]}]

        games_data = list(filter(lambda x: x["type"] == "boardgame", game_list_data))
        expansions_data = list(filter(lambda x: x["type"] == "boardgameexpansion", game_list_data))

        game_id_to_expansion = {game["id"]: [] for game in games_data}
        for expansion_data in expansions_data:
            for expansion in expansion_data["expansions"]:
                if expansion["inbound"] and expansion["id"] in game_id_to_expansion:
                    game_id_to_expansion[expansion["id"]].append(expansion_data)

        games = [
            BoardGame(
                game_data,
                personal_rating=game_id_to_personal_rating[game_data["id"]],
                image=game_id_to_image[game_data["id"]],
                thumbnail=game_id_to_thumbnail[game_data["id"]],
                tags=game_id_to_tags[game_data["id"]],
                numplays=game_id_to_numplays[game_data["id"]],
                lastmodified = game_id_to_lastmodified[game_data["id"] or '2012-12-25'],
                previous_players=game_id_to_players[game_data["id"]],
                expansions=[
                    BoardGame(expansion_data)
                    for expansion_data in game_id_to_expansion[game_data["id"]]
                ],
                additional_info=None if additional_info is None else additional_info.get(str(game_data["id"]))
            )
            for game_data in games_data
        ]
        return games
