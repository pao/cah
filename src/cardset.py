from __future__ import print_function

import glob
import json
import os
import yaml

import requests

from twisted.python import log


def num_white_cards(text):
    return max(1, text.count("{}"))


def enumerate_cards(cards):
    for ident, card in enumerate(cards):
        card["card_id"] = ident


class Cardset(object):
    def __init__(
        self, black=[], white=[], name="", tag="", default=False, cardcast_id=""
    ):
        self.default = default
        self.white = white
        self.black = black
        self.name = name
        self.tag = tag
        self.cardcast_id = cardcast_id

    def __getitem__(self, *args, **kwargs):
        return self.__dict__.__getitem__(*args, **kwargs)


class LocalFileSet(Cardset):
    def __init__(self, filename):
        log.msg("Loading {}".format(filename))
        with open(filename) as f:
            cardset = yaml.load(f)
        log.msg("{} loaded".format(filename))
        Cardset.__init__(self, **cardset)


class CardcastSet(Cardset):
    def __init__(self, playcode):
        log.msg("getting deck {} from Cardcast".format(playcode))
        deck_uri = "https://api.cardcastgame.com/v1/decks/{}".format(playcode)
        deck_info = json.loads(requests.get(deck_uri).text)
        cards = json.loads(requests.get("/".join([deck_uri, "cards"])).text)
        log.msg(
            "loaded {} from Cardcast: name '{}'".format(playcode, deck_info["name"])
        )

        Cardset.__init__(
            self,
            black=CardcastSet.reformat_black(cards["calls"]),
            white=CardcastSet.reformat_white(cards["responses"]),
            name="{} ({})".format(deck_info["name"], playcode),
            tag=playcode,
            cardcast_id=playcode,
        )

    @staticmethod
    def reformat_black(cards):
        output = []
        for card in cards:
            output.append("{}".join(card["text"]))
        return output

    @staticmethod
    def reformat_white(cards):
        output = []
        for card in cards:
            output.append("".join([card["text"][0].capitalize(), "."]))
        return output


class DeckManager(object):
    def __init__(self, data_path):
        self.active_files = []
        self.all_sets = []
        self.refresh_files(data_path)
        self.active_tags = set(c["tag"] for c in self.all_sets if c["default"])
        log.msg("initially active: ", self.active_tags)

    def add_set(self, cardset):
        self.all_sets.append(cardset)

    def refresh_files(self, data_path):
        available_files = glob.glob(os.path.join(data_path, "*.yml"))
        for filename in available_files:
            self.add_set(LocalFileSet(filename))

    def get_available_sets(self):
        available_sets = []
        for this_set in self.all_sets:
            available_sets.append(
                {
                    "name": this_set["name"],
                    "tag": this_set["tag"],
                    "enabled": this_set["tag"] in self.active_tags,
                }
            )
        return available_sets

    def get_active_cards(self):
        black_cards = []
        white_cards = []
        for tag in self.active_tags:
            log.msg("Adding tag {} to current cards".format(tag))
            for cardset in self.all_sets:
                if cardset["tag"] == tag:
                    break
            for c in cardset["black"]:
                black_cards.append(
                    {
                        "tag": cardset["tag"],
                        "text": c,
                        "num_white_cards": num_white_cards(c),
                    }
                )
            for c in cardset["white"]:
                white_cards.append(
                    {"tag": cardset["tag"], "text": c,}
                )
        enumerate_cards(black_cards)
        enumerate_cards(white_cards)
        return {"black_cards": black_cards, "white_cards": white_cards}
