import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import grpc
import argparse
import threading
import time

import xchange.protos.exchange_pb2_grpc as exchange_grpc

import xchange.protos.competitor_registry_pb2 as comp_reg
import xchange.protos.order_book_pb2 as order_book
import xchange.protos.competitor_pb2 as competitor

import xchange.protos.round_manager_pb2_grpc as round_manager_grpc

import xchange.protos.data_feed_pb2 as order_book
import xchange.protos.competitor_pb2 as competitor
import xchange.protos.round_manager_pb2 as round_manager

from xchange.client import Client

from xchange.client_util import OrderSide, OrderType
from xchange.case_manager import CaseManager

import pandas as pd
import random, time

class FlowBot(CaseManager):
    def __init__(self, *args, **kwargs):
        Client.__init__(self)

        # self.ignore_exchange = True
        self.num_assets = 10
        self.num_updates = 0
        self.strikes = range(70, 160, 10)
        c = ["{}C".format(x) for x in self.strikes]
        p = ["{}P".format(x) for x in self.strikes]
        self.asset_list = []
        for x in [chr(ord("A") + i) for i in range(self.num_assets)]:
            self.asset_list.append(x)
            self.asset_list += ["{}{}".format(x, y) for y in c]
            self.asset_list += ["{}{}".format(x, y) for y in p]


    def handle_connected(self):
        CaseManager.handle_connected(self)

        def random_orders():
            while True:
                updates = self.num_updates
                for i in range(random.randint(0, 5)):
                    
                    asset = random.choice(self.asset_list)
                    side = random.choice([OrderSide.BID, OrderSide.ASK])
                    size = random.randint(1, 50)

                    self.place_order(OrderType.MARKET, side, size, asset)
                while updates == self.num_updates:
                    time.sleep(0.1)
                    pass

        threading.Thread(target=random_orders).start()


    def handle_exchange_update(self, exchange_update_response):
        if exchange_update_response.HasField('market_update'):
            self.num_updates += 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the exchange client')
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=str, default="9090")
    parser.add_argument("--username", type=str)
    parser.add_argument("--password", type=str)

    args = parser.parse_args()
    client = FlowBot()
    client.start(args.host, args.port, args.username, args.password)
    # client.ignore_exchange = False
