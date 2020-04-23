from __future__ import print_function

import glob
import os
import yaml

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


class DeckManager(object):
    def __init__(self, data_path):
        self.active_files = []
        self.all_sets = []
        self.refresh_files(data_path)
        self.active_tags = set(c["tag"] for c in self.all_sets if c["default"])
        log.msg("initially active: ", self.active_tags)

    def refresh_files(self, data_path):
        available_files = glob.glob(os.path.join(data_path, "*.yml"))
        for filename in available_files:
            log.msg("Loading {}".format(filename))
            with open(filename) as f:
                cardset = yaml.load(f)
            log.msg("{} loaded".format(filename))
            self.all_sets.append(Cardset(**cardset))

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
