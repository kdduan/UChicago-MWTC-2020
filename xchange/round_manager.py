#!/usr/bin/env python
# round_manager.py - A parent class for all round managers
# pylint: disable=E1101

import argparse
import threading

import traceback

import grpc

import xchange.protos.round_manager_pb2_grpc as round_manager_grpc
import xchange.protos.exchange_pb2_grpc as exchange_grpc

import xchange.protos.competitor_registry_pb2 as comp_reg
import xchange.protos.exchange_pb2 as exchange
import xchange.protos.data_feed_pb2 as data_feed
import xchange.protos.order_book_pb2 as order_book
import xchange.protos.competitor_pb2 as competitor
import xchange.protos.round_manager_pb2 as round_manager

import json

import sys
from typing import Tuple, Any, Dict

from xchange.client import Client
import xchange.client_util as cu

class RoundManager(Client):
    """Round Manager base class"""

    def __init__(self):
        Client.__init__(self)

        self._rm_stub = None
        self.creds = None

    def handle_exchange_update(self, exchange_update_response):
        """Handle updates coming from the exchange"""
        # TODO when you subclass this bot, you should implement this
        pass

    def handle_connected(self):
        """Handle bot connecting"""
        # TODO when you subclass this bot, you should implement this
        pass

    def start(self, host: str, port: str, username: str, password: str):
        """
        Connects to the exchange and starts streaming exchange updates once the round starts (assuming this is registered as an RM, which it should be)
        
        Parameters:
            host (string): The address of the exchange server
            port (string): The port of the server to access
            username (string): The username to be used for registration
            password (string): The password to be used for registration
        """

        self._connect(host, port)

        self._rm_stub = round_manager_grpc.RoundManagerServiceStub(self._channel)

        self.creds = competitor.CompetitorCredentials(
            username=username,
            password=password
        )

        # call the round_started event
        self.handle_connected()
        
        print("Case has begun. Starting to handle exchange updates...")

        self._stream_updates()


    def broadcast_competition_event(self, message: Any):
        """
        Send an object via competition event to all competitors

        Parameters:
            message (Any): The message to send (will be converted to JSON)
        """

        req = round_manager.BroadcastCompetitionEventRequest(
            competitor=self.creds,
            message=json.dumps(message)
        )

        resp = self._rm_stub.BroadcastCompetitionEvent(req)

        return resp

    def end_round(self, roundEndPrices: Dict[str, str]):
        """
        End a round

        Parameters:
            roundEndPrices (Dict[str, str]) the prices to mark to @ end of round
        """
        
        req = round_manager.EndRoundRequest(
            competitor=self.creds,
            roundEndPrices=roundEndPrices
        )

        resp = self._rm_stub.EndRound(req)

        if resp.status == round_manager.EndRoundResponse.Status.SUCCESS:
            exit(0)

        # NOTE: This shouldn't actually ever be reached, as the server will terminate the roundmanager automatically
        return resp

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Run the do-nothing competitor bot')

    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=str, default="9090")
    parser.add_argument("--username", type=str, required=True)
    parser.add_argument("--password", type=str, required=True)

    args = parser.parse_args()
    
    client = RoundManager()
    client.start(args.host, args.port, args.username, args.password)
