from __future__ import print_function

import glob
import json
import os
from ruamel.yaml import YAML

import requests

from twisted.python import log


def num_white_cards(text):
    return max(1, text.count("{}"))


def enumerate_cards(cards):
    for ident, card in enumerate(cards):
        card["card_id"] = ident


class Cardset(object):
    def __init__(
        self,
        black=[],
        white=[],
        name="",
        tag="",
        default=False,
        cardcast_id=None,
        hidden=False,
    ):
        self.name = name
        self.tag = tag
        self.default = default
        self.cardcast_id = cardcast_id
        self.white = white
        self.black = black
        self.hidden = hidden

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
            "hidden": self.hidden,
        }

    @classmethod
    def from_local_file(cls, filename):
        log.msg("Loading {}".format(filename))
        yaml = YAML(typ="rt")
        with open(filename) as f:
            cardset = yaml.load(f)
        log.msg("{} loaded".format(filename))
        # skip file if empty
        if cardset:
            return cls(**cardset)
        else:
            log.msg("{} had no content...".format(filename))
            return cls()

    @classmethod
    def from_cardcast(cls, playcode):
        playcode = playcode.upper()
        log.msg("getting deck {} from Cardcast".format(playcode))
        deck_uri = "https://api.cardcastgame.com/v1/decks/{}".format(playcode)
        deck_info = json.loads(requests.get(deck_uri).text)
        cards = json.loads(requests.get("/".join([deck_uri, "cards"])).text)
        log.msg(
            "loaded {} from Cardcast: name '{}'".format(playcode, deck_info["name"])
        )

        return cls(
            black=cls.reformat_black(cards["calls"]),
            white=cls.reformat_white(cards["responses"]),
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

    def get_filename(self, save_path):
        return os.path.join(
            save_path,
            "{}{}.yml".format("cardcast-" if self.cardcast_id else "", self.tag),
        )

    def save(self, save_path):
        yaml = YAML()
        yaml.default_flow_style = False
        with open(self.get_filename(save_path), "w") as f:
            yaml.dump(self.as_dict(), f)

    def delete(self, save_path):
        log.msg("Deleting file {}".format(self.get_filename(save_path)))
        os.unlink(self.get_filename(save_path))
        # try:
        #    os.unlink(self.get_filename())
        # except:
        #    pass


class DeckManager(object):
    def __init__(self, data_path):
        self.active_files = []
        self.all_sets = {}
        self.refresh_files(data_path)
        self.active_tags = set(
            tag for tag, c in self.all_sets.items() if c["default"] and not c["hidden"]
        )
        log.msg("initially active: ", self.active_tags)

    def add_set(self, cardset):
        self.all_sets[cardset["tag"]] = cardset

    def refresh_files(self, data_path):
        available_files = glob.glob(os.path.join(data_path, "*.yml"))
        for filename in available_files:
            self.add_set(Cardset.from_local_file(filename))

    def remove_set(self, tag, save_path):
        self.all_sets[tag].delete(save_path)
        del self.all_sets[tag]

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
                    "is_cardcast": this_set["cardcast_id"] is not None,
                    "default": this_set["default"],
                    "hidden": this_set["hidden"],
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
