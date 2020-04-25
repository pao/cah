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
        self, black=[], white=[], name="", tag="", default=False, cardcast_id=None
    ):
        self.name = name
        self.tag = tag
        self.default = default
        self.cardcast_id = cardcast_id
        self.white = white
        self.black = black

    def __getitem__(self, *args, **kwargs):
        return self.__dict__.__getitem__(*args, **kwargs)

    def as_dict(self):
        return {
            "name": self.name,
            "tag": self.tag,
            "default": self.default,
            "cardcast_id": self.cardcast_id,
            "white": self.white,
            "black": self.black,
        }


class LocalFileSet(Cardset):
    def __init__(self, filename):
        log.msg("Loading {}".format(filename))
        with open(filename) as f:
            cardset = yaml.load(f)
        log.msg("{} loaded".format(filename))
        # skip file if empty
        if cardset:
            Cardset.__init__(self, **cardset)
        else:
            log.msg("{} had no content...".format(filename))
            Cardset.__init__(self)


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

    def save(self, save_path):
        filename = os.path.join(save_path, "cardcast-{}.yml".format(self.tag))
        with open(filename, "w") as f:
            f.write(
                yaml.safe_dump(
                    self.as_dict(),
                    encoding="utf-8",
                    allow_unicode=True,
                    default_flow_style=False,
                )
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
        self.all_sets = {}
        self.refresh_files(data_path)
        self.active_tags = set(tag for tag, c in self.all_sets.items() if c["default"])
        log.msg("initially active: ", self.active_tags)

    def add_set(self, cardset):
        self.all_sets[cardset["tag"]] = cardset

    def refresh_files(self, data_path):
        available_files = glob.glob(os.path.join(data_path, "*.yml"))
        for filename in available_files:
            self.add_set(LocalFileSet(filename))

    def get_available_sets(self):
        available_sets = []
        for tag, this_set in self.all_sets.items():
            available_sets.append(
                {
                    "name": this_set["name"],
                    "tag": tag,
                    "enabled": tag in self.active_tags,
                    "num_black": len(this_set["black"]),
                    "num_white": len(this_set["white"]),
                }
            )
        return available_sets

    def get_active_cards(self):
        black_cards = []
        white_cards = []
        for tag in self.active_tags:
            log.msg("Adding tag {} to current cards".format(tag))
            if tag not in self.all_sets.keys():
                log.msg("Couldn't find tag {} in available sets, skipping")
                continue
            cardset = self.all_sets[tag]
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
