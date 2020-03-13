import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import grpc

import argparse
import threading
import time

import xchange.protos.exchange_pb2_grpc as exchange_grpc

import xchange.protos.competitor_registry_pb2 as comp_reg
import xchange.protos.competitor_pb2 as competitor

import xchange.protos.round_manager_pb2_grpc as round_manager_grpc

import xchange.protos.data_feed_pb2 as data_feed
import xchange.protos.competitor_pb2 as competitor
import xchange.protos.round_manager_pb2 as round_manager

from xchange.client import Client

from xchange.client_util import OrderSide, OrderType
from xchange.case_manager import CaseManager

import pandas as pd
import random


class StockBot(CaseManager):
    def __init__(self, *args, **kwargs):
        Client.__init__(self)

        self.ignore_exchange = True
        self.num_assets = 10
        self.update_frequency = 8

        self.total_price_updates = 450
        self.annual_price_updates = 1800

        self.annual_ticks = self.annual_price_updates * self.update_frequency
        self.total_ticks = self.total_price_updates * self.update_frequency

        self.df = pd.read_csv(
            "data/normalized_price_paths/trading_0.csv", index_col=0)
        self.df.index = [chr(ord("A") + i) for i in range(self.df.shape[0])]
        self.df = self.df.iloc[:self.num_assets]
        self.oids = {}

        self.num_updates = 0

        self.strikes = range(70, 160, 10)

        self.asset_list = [
            "{}{}{}".format(und, strike, side)
            for und in self.df.index
            for strike in self.strikes
            for side in "CP"
        ] + list(self.df.index)

    def handle_connected(self):
        CaseManager.handle_connected(self)

        col = self.df.iloc[:, 0]
        for x in col.index:
            self.oids[x] = {}
            val = col.loc[x]
            bid = max(0, round(val - .005, 2))
            ask = bid + .01
            self.oids[x]["bid"] = self.place_order(
                OrderType.LIMIT, OrderSide.BID, 400000, x, "%.2f" % bid)[1].order_id
            self.oids[x]["ask"] = self.place_order(
                OrderType.LIMIT, OrderSide.ASK, 400000, x, "%.2f" % ask)[1].order_id
            self.oids[x]["mid_px"] = val

        self.num_updates += 1
        self.ignore_exchange = False

    def get_time_to_go(self):
        return (self.total_ticks - self.num_updates) / self.annual_ticks

    def send_rtq(self):
        r, T, q,  = 0, self.get_time_to_go(), 0
        bsParams = {}
        for asset in self.asset_list:
            bsParams[asset] = round_manager.BSUpdateRequest.BSParameters(
                T=T, q=q, r=r)

        self.send_bs_update(bsParams)

    def end_round(self):
        settlement = self.df.iloc[:, -1]
        last_prices = {}
        for asset in self.asset_list:
            if len(asset) == 1:
                last_prices[asset] = "%2f" % float(settlement.loc[asset])
            elif asset[-1] == "C":
                last_prices[asset] = "%.2f" % max(
                    float(settlement.loc[asset[0]]) - float(asset[1:-1]), 0)
            else:
                last_prices[asset] = "%.2f" % max(
                    float(asset[1:-1]) - float(settlement.loc[asset[0]]), 0)

        CaseManager.end_round(self, last_prices)

    def handle_market_update(self, exchange_update_response):
        update = exchange_update_response.market_update
        self.num_updates += 1
        self.send_rtq()
        if self.num_updates % self.update_frequency == 0:
            current_step = self.num_updates // self.update_frequency

            if current_step < self.total_price_updates - 25:
                col = self.df.iloc[:, current_step]
            else:
                self.end_round()
                return

            print(list(col.index))

            for x in col.index:
                val = col.loc[x]
                bid = max(0, round(val-.005, 2))
                ask = bid + .01
                print("BID: {}, ASK: {}".format(bid, ask))
                if val < self.oids[x]["mid_px"]:
                    self.oids[x]["bid"] = self.modify_order(
                        self.oids[x]["bid"], OrderType.LIMIT, OrderSide.BID, 400000, x, "%.2f" % bid)[1].order_id
                    self.oids[x]["ask"] = self.modify_order(
                        self.oids[x]["ask"], OrderType.LIMIT, OrderSide.ASK, 400000, x, "%.2f" % ask)[1].order_id
                else:
                    self.oids[x]["ask"] = self.modify_order(
                        self.oids[x]["ask"], OrderType.LIMIT, OrderSide.ASK, 400000, x, "%.2f" % ask)[1].order_id
                    self.oids[x]["bid"] = self.modify_order(
                        self.oids[x]["bid"], OrderType.LIMIT, OrderSide.BID, 400000, x, "%.2f" % bid)[1].order_id
                self.oids[x]["mid_px"] = val
                asset_update = update.book_updates[x]

    def handle_exchange_update(self, exchange_update_response):
        if self.ignore_exchange:
            return
        if exchange_update_response.HasField('market_update'):
            self.handle_market_update(exchange_update_response)
        elif exchange_update_response.HasField('order_status_response'):
            if (exchange_update_response.order_status_response.status == data_feed.OrderStatusResponse.Status.FAILURE_OTHER):
                print("failure: {}".format(exchange_update_response.order_status_response))

        elif exchange_update_response.HasField('fill_update'):
            print("fill_update: {}".format(exchange_update_response.fill_update))

        elif exchange_update_response.HasField('liquidation_event'):
            print("foo")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the exchange client')
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=str, default="9090")
    parser.add_argument("--username", type=str)
    parser.add_argument("--password", type=str)

    args = parser.parse_args()

    client = StockBot()
    client.start(args.host, args.port, args.username, args.password)
