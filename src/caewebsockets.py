import os
import sys

import json
import yaml
from autobahn.wamp import WampServerFactory, WampServerProtocol, exportRpc

from twisted.python import log

import requests

from game import Game
from cardset import CardcastSet
from roomsmanager import rooms, get_smallest_game_id, create_new_game, get_or_create_room

with open("config.yml") as f:
    config = yaml.load(f)
    config['admin_password'] = os.getenv('CAH_ADMIN_PASS', config['admin_password'])

class CahWampServerProtocol(WampServerProtocol):
    def __init__(self):
        self._username = ""
        self._game_id = -1
        self._game = None

    @exportRpc
    def join(self, username):
        result = self._game.add_user(username, self)
        if result:
            self._username = username
            self._game.sync_setup()
        return result

    @exportRpc
    def sync_me(self):
        self._game.sync_me()

    @exportRpc
    def start_game(self):
        return self._game.start_game()

    @exportRpc
    def choose_white(self, card_id):
        self._game.choose_white(self._username, card_id)

    @exportRpc
    def judge_group(self, group_id):
        self._game.judge_group(self._username, group_id)

    @exportRpc
    def kick_user(self, admin_pass, username):
        if admin_pass == config['admin_password']:
            self._game.remove_user(username)

    @exportRpc
    def update_afk(self, afk = None):
        if afk:
            afk = True
        else:
            afk = False
        self._game.update_afk(self._username, afk)

    @exportRpc
    def restart_timer(self):
        self._game.restart_timer()

    @exportRpc
    def get_rooms(self):
        return {
            "rooms": [{
                    "game_id": game_id,
                    "users":[{"username": u.username} for u in game.users]
                } for game_id, game in rooms.items()]
        }

    @exportRpc
    def create_game(self):
        game = create_new_game()
        self.join_game(game.game_id)
        return game.game_id

    @exportRpc
    def join_game(self, game_id):
        if game_id < 0:
            game_id = get_smallest_game_id()
        elif self._game:
            self._game.remove_user(self._username)
        self._game_id = game_id
        prefix = 'http://{}:{}/ws/{}{}#'
        self.registerForRpc(self, prefix.format(
            config['server_domain'],
            config['server_port'],
            game_id,
            '_rpc',
        ))
        self.registerForPubSub(prefix.format(
            config['server_domain'],
            config['server_port'],
            game_id,
            '',
        ), True)
        self._game = get_or_create_room(game_id)
        if self._username:
            self.join(self._username)
        return game_id

    @exportRpc
    def set_active_cardset(self, tag, state):
        if state:
            self._game.cardset.active_tags.add(tag)
        else:
            self._game.cardset.active_tags.discard(tag)
        log.msg("current active sets: {}".format(self._game.cardset.active_tags))
        self._game.sync_setup()

    @exportRpc
    def add_cardcast_set(self, playcode, persistent):
        new_set = CardcastSet(playcode.upper())
        self._game.cardset.add_set(new_set)
        if persistent:
            new_set.save(self._game.saved_decks_path)
        self._game.sync_setup()

    @exportRpc
    def set_winning_score(self, winning_score):
        self._game.winning_score = int(winning_score)
        self._game.sync_setup()

    @exportRpc
    def set_round_length(self, round_length):
        self._game.round_length = int(round_length)
        self._game.sync_setup()

    @exportRpc
    def set_timer_disabled(self, timer_disabled):
        self._game.timer_disabled = timer_disabled
        self._game.sync_setup()

    @exportRpc
    def set_hand_size(self, hand_size):
        self._game.hand_size = int(hand_size)
        self._game.sync_setup()

    def onSessionOpen(self):
        self.registerProcedureForRpc("http://{server_domain}:{server_port}/ws/#join_game".format(**config),
            self.join_game)

    def connectionLost(self, reason):
        if self._game:
            self._game.remove_user(self._username)
        try:
            super(self, reason)
        except:
            pass

class CahServerFactory(WampServerFactory):
    protocol = CahWampServerProtocol

    def __init__(self, url, publish_uri, **kwargs):
        WampServerFactory.__init__(self, url, **kwargs)
        Game.register_cah_wamp_client(self)
        Game.set_publish_uri(publish_uri)
        self.startFactory() #hack!
