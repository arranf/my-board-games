from decimal import Decimal
import html


class BoardGame:
    def __init__(self, game_data, personal_rating="", image="", thumbnail = "", lastmodified='', collectionstatus=[], numplays=0, previous_players=[], expansions=[], additional_info=None, tags=[]):
        self.id = game_data["id"]
        self.name = game_data["name"]
        self.description = html.unescape(game_data["description"])
        self.categories = game_data["categories"]
        self.mechanics = game_data["mechanics"]
        self.players = self.calc_num_players(game_data, expansions, additional_info)
        self.weight = self.calc_weight(game_data)
        self.playing_time = self.calc_playing_time(game_data)
        self.rank = self.calc_rank(game_data)
        self.usersrated = self.calc_usersrated(game_data)
        self.numowned = self.calc_numowned(game_data)
        self.rating = self.calc_rating(game_data)
        self.personal_rating = self.calc_personal_rating(personal_rating)
        self.lastmodified = lastmodified
        self.numplays = numplays
        self.image = image
        self.thumbnail = thumbnail
        self.collectionstatus = collectionstatus
        self.previous_players = previous_players
        self.expansions = expansions
        self.tags = tags

        self.personal_rank = None
        self.tagline = None
        self.rgb = None

        if additional_info is None:
            return
        self.rgb = additional_info.get('rgb')
        self.tagline = additional_info.get('tagline')
        image = additional_info.get('image')
        if image is not None:
            self.image = image
        personal_rank = additional_info.get('rank')
        if personal_rank is not None:
            self.personal_rank = int(personal_rank)

    def calc_num_players(self, game_data, expansions, additional_info):
        num_players = dict(game_data["suggested_numplayers"].copy())

        # Add number of players from expansions
        for expansion in expansions:
            for expansion_num, _ in expansion.players:
                if expansion_num not in num_players:
                    num_players[expansion_num] = "expansion"


        # If additional info, ovverride player counts
        if additional_info and additional_info.get("players") is not None:
            for player_count, recommendation in additional_info["players"].items():
                num_players[player_count] = recommendation

        # Remove not_recommended player counts, possibly added by overrides
        for player_count, recommendation in list(num_players.items()):
            if recommendation == "not_recommended" or player_count == "0":
                num_players.pop(player_count)

        num_players = [(k, v) for k, v in num_players.items()]

        num_players = sorted(num_players, key=lambda x: int(x[0].replace("+", "")))
        return num_players

    def calc_playing_time(self, game_data):
        playing_time_mapping = {
            30: '< 30min',
            60: '30min - 1h',
            120: '1-2h',
            180: '2-3h',
            240: '3-4h',
        }
        for playing_time_max, playing_time in playing_time_mapping.items():
            if playing_time_max > int(game_data["playing_time"]):
                return playing_time

        return '> 4h'

    def calc_rank(self, game_data):
        if not game_data["rank"] or game_data["rank"] == "Not Ranked":
            return None

        return int(game_data["rank"])

    def calc_usersrated(self, game_data):
        if not game_data["usersrated"]:
            return 0

        return int(game_data["usersrated"])

    def calc_numowned(self, game_data):
        if not game_data["numowned"]:
            return 0

        return int(game_data["numowned"])

    def calc_rating(self, game_data):
        if not game_data["rating"]:
            return None

        return float(game_data["rating"])
    
    def calc_personal_rating(self, personal_rating):
        if not personal_rating or personal_rating == "N/A":
            return None

        return float(personal_rating)

    # TODO: Improve this
    def calc_weight(self, game_data):
        weight_mapping = {
            0: "Light",
            1: "Light",
            2: "Light Medium",
            3: "Medium",
            4: "Medium Heavy",
            5: "Heavy",
        }
        return weight_mapping[round(Decimal(game_data["weight"] or 0))]
