#!/usr/bin/env python
# pylint: disable=E1101

from enum import Enum

import xchange.protos.exchange_pb2_grpc as exchange_grpc
import xchange.protos.competitor_registry_pb2 as comp_reg
import xchange.protos.exchange_pb2 as exchange
import xchange.protos.data_feed_pb2 as data_feed
import xchange.protos.order_book_pb2 as order_book
import xchange.protos.competitor_pb2 as competitor

OrderType = Enum('OrderSide', 'MARKET LIMIT IOC')
OrderSide = Enum('OrderSide', 'BID ASK')

def proto_of_order_type(order_type: OrderType):
    return order_book.Order.OrderType.Value({
        OrderType.MARKET: 'MARKET',
        OrderType.LIMIT: 'LIMIT',
        OrderType.IOC: 'IOC'
    }[order_type])

def proto_of_order_size(order_side: OrderSide):
    return order_book.Order.OrderSide.Value({
        OrderSide.BID: 'BID',
        OrderSide.ASK: 'ASK'
    }[order_side])
