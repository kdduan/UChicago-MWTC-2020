#!/usr/bin/env python
# client.py - A parent class for x-Change clients
# pylint: disable=E1101,W0614

import argparse
import threading
import traceback
import grpc
import sys
from typing import Tuple, Any
import xchange.client_util as cu

from xchange.protos.exchange_pb2_grpc import ExchangeServiceStub
from xchange.protos.competitor_registry_pb2 import *
from xchange.protos.exchange_pb2 import *
from xchange.protos.data_feed_pb2 import *
from xchange.protos.order_book_pb2 import *
from xchange.protos.competitor_pb2 import *

class Client():
    """x-Change client base class"""

    def __init__(self):
        # Set up null values
        self._exch_stub = None
        self._channel = None

    def place_order(self,
                    order_type: cu.OrderType,
                    order_side: cu.OrderSide,
                    qty: int,
                    asset_code: str,
                    px: str = "") -> Tuple[bool, PlaceOrderResponse]:
        """
        Place an order on the exchange
        
        Parameters:
            order_type (cu.OrderType): The type of order this is
            order_side (cu.OrderSize): The side of the order
            qty (int): The # of lots of the asset to buy
            asset_code (str): The code of the asset
            px (str): The price to buy/sell at

        Returns:
            Tuple[bool, order_book.PlaceOrderResponse] Whether the placement was successful and the full response
        """

        self._confirm_registered()

        side_proto = cu.proto_of_order_size(order_side)
        type_proto = cu.proto_of_order_type(order_type)

        req = PlaceOrderRequest(
            competitor=self.creds,
            order=Order(
                type=type_proto,
                side=side_proto,
                asset=asset_code,
                quantity=qty,
                price=px
            ))

        resp = self._exch_stub.PlaceOrder(req)
        return resp.status == PlaceOrderResponse.Status.SUCCESS, resp

    def modify_order(self,
                     order_id: str,
                     order_type: cu.OrderType,
                     order_side: cu.OrderSide,
                     qty: int,
                     asset_code: str,
                     px: str = "") -> Tuple[bool, ModifyOrderResponse]:
        """
        Modify an order that you've already placed (equivalent to atomic cancel + place)
        
        Parameters:
            order_id (str): The ID of the order to replace
            order_type (cu.OrderType): The type of order this is
            order_side (cu.OrderSize): The side of the order
            qty (int): The # of lots of the asset to buy
            asset_code (str): The code of the asset
            px (str): The price to buy/sell at

        Returns:
            Tuple[bool, order_book.ModifyOrderResponse] Whether the modify was successful and the full response
        """

        self._confirm_registered()

        side_proto = cu.proto_of_order_size(order_side)
        type_proto = cu.proto_of_order_type(order_type)

        req = ModifyOrderRequest(
            competitor=self.creds,
            order_id=order_id,
            new_order=Order(
                type=type_proto,
                side=side_proto,
                asset=asset_code,
                quantity=qty,
                price=px
            )
        )

        resp = self._exch_stub.ModifyOrder(req)
        return resp.status == ModifyOrderResponse.Status.SUCCESS, resp

    def cancel_order(self, order_id: str, asset_code: str) -> Tuple[bool, CancelOrderResponse]:
        """
        Cancel an order
        
        Parameters:
            order_id (str): The ID of the order to cancel
            asset_code (str): The code of the asset associated with this order

        Returns:
            Tuple[bool, order_book.CancelOrderResponse] Whether the cancel was successful and the full response
        """

        self._confirm_registered()

        req = CancelOrderRequest(competitor=self.creds, order_id=order_id, asset=asset_code)

        resp = self._exch_stub.CancelOrder(req)
        return resp.status == CancelOrderResponse.Status.SUCCESS, resp

    def handle_exchange_update(self, exchange_update):
        raise NotImplementedError("Must override handle_exchange_update in client subclass")

    def _connect(self, host: str, port: str):
        """
        Connects to the server if not already done and registers if necessary

        Parameters:
            host (str): The address of the exchange server
            port (str): The port of the server to access
        """

        # Initialize gRPC channel
        if not self._channel:
            self._channel = grpc.insecure_channel(
                '{}:{}'.format(host, port))
        
        if not self._exch_stub:
            self._exch_stub = ExchangeServiceStub(self._channel)

    def _register(self,
                  username: str,
                  password: str) -> Tuple[CompetitorCredentials, Any]:
        """
        Registers a competitor on the exchange
        
        Parameters:
            username (str): The username to be used for registration
            password (str): The password to be used for registration

        Returns:
            competitor.CompetitorCredentials, comp_reg.RegisterCompetitorResponse.Status: The generated credentials and the status of the request
        """

        # Constructs the credentials object and sends it to the exchange for registration
        competitor = CompetitorCredentials(
            username=username,
            password=password
        )

        return competitor, self._exch_stub.RegisterCompetitor(RegisterCompetitorRequest(
            competitor=competitor
        )).status

    def _stream_updates(self):
        """Stream upates from the exchange"""

        # Request a data feed
        req = StreamExchangeUpdatesRequest(competitor=self.creds)
        update_stream = self._exch_stub.StreamExchangeUpdates(req)

        # Start a new thread to process updates from the exchange
        threading.Thread(
            target=self._update_stream_handler,
            args=(update_stream,)
        ).start()

    def _update_stream_handler(self, exchange_updates):
        """Handle updates from an update stream, printing errors without dying"""

        for update in exchange_updates:
            try:
                self.handle_exchange_update(update)
            except Exception:
                traceback.print_exc()

    def _confirm_registered(self):
        """Confirm that this bot has at some point successfully connected to the server"""

        if self.creds is None:
            raise Exception(
                "Must successfully register before performing exchange operations")

