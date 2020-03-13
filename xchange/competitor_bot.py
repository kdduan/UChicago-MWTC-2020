#!/usr/bin/env python
# competitor_bot.py - A parent class for all competitor bots
# pylint: disable=E1101

import argparse
import threading

import traceback

import grpc
import xchange.protos.exchange_pb2_grpc as exchange_grpc
import xchange.protos.competitor_registry_pb2 as comp_reg
import xchange.protos.exchange_pb2 as exchange
import xchange.protos.data_feed_pb2 as data_feed
import xchange.protos.order_book_pb2 as order_book
import xchange.protos.competitor_pb2 as competitor

import sys
from typing import Tuple

from xchange.client import Client
import xchange.client_util as cu

class CompetitorBot(Client):
    """A bot that will trade in the 2020 Midwest Trading Competition"""

    def __init__(self):
        Client.__init__(self)

        self.creds = None

    def handle_exchange_update(self, exchange_update_response):
        """Handle updates coming from the exchange"""
        # TODO when you subclass this bot, you should implement this
        pass

    def handle_round_started(self):
        """Handle a round being started. Is only called if registration was successful"""
        # TODO when you subclass this bot, you should implement this
        pass

    def start(self, host: str, port: str, username: str, password: str):
        """
        Registers the client with the exchange as a competitor (if not registered already),
        waits for the case to start, and starts streaming exchange updates once the round starts
        
        Parameters:
            host (string): The address of the exchange server
            port (string): The port of the server to access
            username (string): The username to be used for registration
            password (string): The password to be used for registration
        """

        self._connect(host, port)

        credentials, reg_status = self._register(username, password)

        # If the registrations was successful, update the bot's credentials
        if reg_status != comp_reg.RegisterCompetitorResponse.FAILURE:
            print("Registration successful.")
            self.creds = credentials

            # Await the start of the next case
            self._exch_stub.AwaitCaseStart(comp_reg.AwaitCaseStartRequest())

            # call the round_started event
            self.handle_round_started()
            
            print("Case has begun. Starting to handle exchange updates...")

            self._stream_updates()

        else:
            print("Registration did not succeed with specified credentials.")
            sys.exit(-1)

    def _confirm_registered(self):
        """Confirm that this bot has at some point successfully connected to the server"""

        if self.creds is None:
            raise Exception(
                "Must successfully register before performing exchange operations")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Run the do-nothing competitor bot')

    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=str, default="9090")
    parser.add_argument("--username", type=str, required=True)
    parser.add_argument("--password", type=str, required=True)

    args = parser.parse_args()
    
    client = CompetitorBot()
    client.start(args.host, args.port, args.username, args.password)
