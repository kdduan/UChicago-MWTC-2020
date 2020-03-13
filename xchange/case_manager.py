#!/usr/bin/env python
# case_manager.py - A parent class for all case managers
# pylint: disable=E1101

import argparse
import threading
import traceback
import json
import sys
from typing import Tuple, Any, Dict


import xchange.protos.round_manager_pb2_grpc as round_manager_grpc
import xchange.protos.exchange_pb2_grpc as exchange_grpc

import xchange.protos.competitor_registry_pb2 as comp_reg
import xchange.protos.exchange_pb2 as exchange
import xchange.protos.data_feed_pb2 as data_feed
import xchange.protos.order_book_pb2 as order_book
import xchange.protos.competitor_pb2 as competitor
import xchange.protos.round_manager_pb2 as round_manager

from xchange.round_manager import RoundManager
import xchange.client_util as cu


class CaseManager(RoundManager):
    """Round Manager base class"""

    def __init__(self):
        RoundManager.__init__(self)

    def handle_exchange_update(self, exchange_update_response):
        """Handle updates coming from the exchange"""
        # TODO when you subclass this bot, you should implement this
        pass

    def handle_connected(self):
        """Handle bot connecting"""
        self.start_case()

        # TODO when you subclass this bot, you should implement this

    def send_bs_update(self, update) -> bool:
        """
        Send an update containing Black-Scholes parameters to the competitor

        Parameters:
            update (Dict[String, round_manager.BSParameters]): The parameters for Black-Scholes calculations for
              some subset of assets

        Returns:
            (bool) Whether this request was successful
        """
        resp = self._rm_stub.BSUpdate(round_manager.BSUpdateRequest(
            competitor=self.creds,
            parameters=update
        ))

        return resp.status == round_manager.BSUpdateResponse.Status.SUCCESS

    def end_round(self, end_prices: Dict[str, str] = {}, keep_competitors: bool = False):
        """
        Request to end the round

        Parameters:
            end_prices (Dict[str, str]): The price to mark to at the end of the round, if any
            keep_competitors (bool): Whether to keep the competitors connected after this round ends
        """
        resp = self._rm_stub.EndRound(round_manager.EndRoundRequest(
            competitor=self.creds,
            round_end_prices=end_prices,
            keep_competitors=keep_competitors
        ))

        if resp.status == round_manager.EndRoundResponse.Status.SUCCESS:
            exit(0)

        return resp

    def start_case(self):
        """
        Request for a case to start. The event will kick off the bots
        """
        #self._rm_stub.StartCase(round_manager.StartCaseRequest(
        #    competitor=self.creds
        #))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Run the do-nothing competitor bot')

    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=str, default="9090")
    parser.add_argument("--username", type=str, required=True)
    parser.add_argument("--password", type=str, required=True)

    args = parser.parse_args()
    
    client = RoundManager()
    client.start(args.host, args.port, args.username, args.password)
