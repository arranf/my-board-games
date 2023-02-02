from cmath import exp
import io
import re
import time

import colorgram
import requests
import meilisearch

# Allow colorgram to read truncated files
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

class Indexer:

    def __init__(self, app_address, apikey, index_name):

        client = meilisearch.Client(app_address, apikey)
        index = client.index(index_name)
        
        index.update_settings({
            'filterableAttributes': [
                'players.level1',
                'players.level2',
                'players.level3',
                'playing_time',
                'weight',
                'personal_rating',
                'personal_rank',
                'rating',
                'tags'
            ],
            'searchableAttributes': [
                'name',
                'description',
                'tagline'
            ],
            "sortableAttributes": ["name", "lastmodified", "rank", "personal_rank", "rating", "personal_rating"]
        })
        self.index = index

    @staticmethod
    def todict(obj):
        if isinstance(obj, str):
            return obj

        elif isinstance(obj, dict):
            return dict((key, Indexer.todict(val)) for key, val in obj.items())

        elif hasattr(obj, '__iter__'):
            return [Indexer.todict(val) for val in obj]

        elif hasattr(obj, '__dict__'):
            return Indexer.todict(vars(obj))

        return obj

    def _facet_for_num_player(self, num, type_):
        num_no_plus = num.replace("+", "")
        facet_types = {
            "best": {
                "level1": num_no_plus,
                "level2": f"{num_no_plus} > Best with {num}",
            },
            "recommended": {
                "level1": num_no_plus,
                "level2": f"{num_no_plus} > Recommended with {num}",
            },
            "expansion": {
                "level1": num_no_plus,
                "level2": f"{num_no_plus} > Expansion allows {num}",
            },
        }

        return facet_types[type_]

    def _smart_truncate(self, content, length=700, suffix='...'):
        if len(content) <= length:
            return content
        else:
            return ' '.join(content[:length + 1].split(' ')[0:-1]) + suffix

    def _pick_long_paragraph(self, content):
        content = content.strip()
        if "\n\n" not in content:
            return content

        paragraphs = content.split("\n\n")
        for paragraph in paragraphs[:3]:
            paragraph = paragraph.strip()
            if len(paragraph) > 80:
                return paragraph

        return content

    def _prepare_description(self, description):
        # Try to find a long paragraph from the beginning of the description
        description = self._pick_long_paragraph(description)

        # Remove unnessesary spacing
        description = re.sub(r"\s+", " ", description)

        # Cut at 700 characters, but not in the middle of a sentence
        description = self._smart_truncate(description)

        return description

    @staticmethod
    def _remove_game_name_prefix(expansion_name, game_name):
        def remove_prefix(text, prefix):
            if text.startswith(prefix):
                return text[len(prefix):]
            return text

        tweaked_expansion_name = expansion_name

        ### Expansion name: Arkham Horror: The Card Game – The Dunwich Legacy: Campaign Expansion
        ### Game name: Arkham Horror: The Card Game (Revised Edition)
        ### -- > The Dunwich Legacy: Campaign Expansion
        if "Arkham Horror: The Card Game –" in expansion_name:
            tweaked_expansion_name = remove_prefix(expansion_name, "Arkham Horror: The Card Game –")
        
        # Expansion name: Long Shot: The Dice Game – Horse Set 4 Mini-Expansion
        # Game name: Long Shot: The Dice Game 
        # --> Horse Set 4 Mini-Expansion
        elif game_name + "– " in expansion_name:
            tweaked_expansion_name = remove_prefix(expansion_name, game_name + " – ")

        # Marvel Champions: The Card Game – Ant-Man Hero Pack
        elif game_name + " – " in expansion_name:
            tweaked_expansion_name = remove_prefix(expansion_name, game_name + " – ")

        # Expansion name: Catan: Cities & Knights
        # Game name: Catan
        # --> Cities & Knights
        elif game_name + ": " in expansion_name:
            tweaked_expansion_name = remove_prefix(expansion_name, game_name + ": ")

        # Expansion name: Shadows of Brimstone: Outlaw Promo Cards
        # Game name: Shadows of Brimstone: City of the Ancients
        # --> Outlaw Promo Cards
        elif ":" in game_name:
            game_name_prefix = game_name[0:game_name.index(":")]
            if game_name_prefix + ": " in expansion_name:
                tweaked_expansion_name = tweaked_expansion_name.replace(game_name_prefix + ": ", "")
        
        
        # Netrunner
        if "(fan expansion for Android: Netrunner)" in tweaked_expansion_name:
            tweaked_expansion_name = tweaked_expansion_name.replace("(fan expansion for Android: Netrunner)", "")
        elif "(Fan expansion for Android: Netrunner)" in tweaked_expansion_name:
            tweaked_expansion_name = tweaked_expansion_name.replace("(Fan expansion for Android: Netrunner)", "")
        elif "(fan expansion for Netrunner)" in tweaked_expansion_name:
            tweaked_expansion_name = tweaked_expansion_name.replace("(fan expansion for Netrunner)", "")
        elif "(Fan expansion for Netrunner)" in tweaked_expansion_name:
            tweaked_expansion_name = tweaked_expansion_name.replace("(Fan expansion for Netrunner)", "")
        # Guards of Atlantis
        elif "Tabletop MOBA –" in tweaked_expansion_name:
            tweaked_expansion_name = tweaked_expansion_name.replace("Tabletop MOBA –", "")


        # Mini-Expansion
        if "Mini-Expansion" in tweaked_expansion_name:
            tweaked_expansion_name = tweaked_expansion_name.replace("Mini-Expansion", "")
        elif "Mini Expansion" in tweaked_expansion_name:
            tweaked_expansion_name = tweaked_expansion_name.replace("Mini Expansion", "")
        # Expansion
        elif tweaked_expansion_name.endswith("Expansion"):
            tweaked_expansion_name = tweaked_expansion_name.replace("Expansion", "")

        return tweaked_expansion_name.strip()

    def fetch_image(self, url, tries=0):
        try:
            response = requests.get(url)
        except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError):
            if tries < 3:
                time.sleep(2)
                return self.fetch_image(url, tries=tries + 1)

        if response.status_code == 200:
            return response.content

        return None

    def add_objects(self, collection):
        games = [Indexer.todict(game) for game in collection]
        for i, game in enumerate(games):
            if i != 0 and i % 10 == 0:
                print(f"Evaluated {i} of {len(games)} games...")

            if game["image"]:
                image_data = self.fetch_image(game["image"])
                if image_data:
                    image = Image.open(io.BytesIO(image_data)).convert('RGBA')

                    try_colors = 10
                    colors = colorgram.extract(image, try_colors)
                    for i in range(min(try_colors, len(colors))):
                        color_r, color_g, color_b = colors[i].rgb.r, colors[i].rgb.g, colors[i].rgb.b

                        # Don't return very light or dark colors
                        luma = (
                            0.2126 * color_r / 255.0 +
                            0.7152 * color_g / 255.0 +
                            0.0722 * color_b / 255.0
                        )
                        if (
                            luma > 0.2 and  # Not too dark
                            luma < 0.8     # Not too light
                        ):
                            break

                    else:
                        # As a fallback, use the first color
                        color_r, color_g, color_b = colors[0].rgb.r, colors[0].rgb.g, colors[0].rgb.b

                    game["color"] = f"{color_r}, {color_g}, {color_b}"

            game["objectID"] = f"bgg{game['id']}"

            # Turn players tuple into a hierarchical facet
            game["players"] = [
                self._facet_for_num_player(num, type_)
                for num, type_ in game["players"]
            ]

            # Remove unnessesary data from expansions
            attribute_map = {
                "id": lambda x: x,
                "name": lambda x: self._remove_game_name_prefix(x, game["name"]),
                "players": lambda x: x or None,
            }
            game["expansions"] = [
                {
                    attribute: func(expansion[attribute])
                    for attribute, func in attribute_map.items()
                    if func(expansion[attribute])
                }
                for expansion in game["expansions"]
            ]

            # Make sure description is not too long
            game["description"] = self._prepare_description(game["description"])

        self.index.add_documents(games)


    def delete_objects_not_in(self, collection):
        docs = self.index.get_documents({'limit':1000, 'fields': 'id'})
        collection_ids = [x.id for x in collection]
        ids_to_delete = [x["id"] for x in docs["results"] if x["id"] not in collection_ids]
        if len(ids_to_delete) > 0:
            print("Ids to delete", ids_to_delete)
            self.index.delete_documents(ids_to_delete)
