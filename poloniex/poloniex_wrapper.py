import hashlib
import hmac
import time
import urllib.error
import urllib.error
import urllib.parse
import urllib.parse
import urllib.request
import urllib.request
from collections import defaultdict

import logging

logger = logging.getLogger(__name__)


def createTimeStamp(datestr, format="%Y-%m-%d %H:%M:%S"):
    return time.mktime(time.strptime(datestr, format))


class poloniex:
    def __init__(self, APIKey, Secret, futures_session):
        self.APIKey = APIKey
        self.Secret = Secret
        self.futures_session = futures_session

    def post_process(self, before):
        after = before

        # Add timestamps if there isnt one but is a datetime
        if ('return' in after):
            if (isinstance(after['return'], list)):
                for x in range(0, len(after['return'])):
                    if (isinstance(after['return'][x], dict)):
                        if ('datetime' in after['return'][x] and 'timestamp' not in after['return'][x]):
                            after['return'][x]['timestamp'] = float(createTimeStamp(after['return'][x]['datetime']))

        return after

    def api_query(self, command, req={}):

        if (command == "returnTicker" or command == "return24Volume"):
            ret = self.futures_session.get('https://poloniex.com/public?command=' + command, timeout=5, verify=False)
            return ret
        elif (command == "returnOrderBook"):
            ret = self.futures_session.get(
                'https://poloniex.com/public?command=' + command + '&depth=40&currencyPair=' + str(req['currencyPair']),
                timeout=5, verify=False)
            return ret
        elif (command == "returnMarketTradeHistory"):
            ret = self.futures_session.get(
                'https://poloniex.com/public?command=' + "returnTradeHistory" + '&currencyPair=' + str(
                    req['currencyPair']))
            return ret
        else:
            req['command'] = command
            req['nonce'] = int(time.time() * 1000)
            post_data = urllib.parse.urlencode(req)

            sign = hmac.new(str.encode(self.Secret), str.encode(post_data), hashlib.sha512).hexdigest()
            headers = {
                'Sign': sign,
                'Key': self.APIKey
            }

            ret = self.futures_session.post('https://poloniex.com/tradingApi', data=req, headers=headers)
            return ret

    def returnTicker(self):
        return self.api_query("returnTicker")

    def return24Volume(self):
        return self.api_query("return24Volume")

    def returnOrderBook(self, currencyPair):
        return self.api_query("returnOrderBook", {'currencyPair': currencyPair})

    def returnMarketTradeHistory(self, currencyPair):
        return self.api_query("returnMarketTradeHistory", {'currencyPair': currencyPair})

    # Returns all of your balances.
    # Outputs:
    # {"BTC":"0.59098578","LTC":"3.31117268", ... }
    def returnBalances(self):
        return self.api_query('returnBalances')

    # Returns all of your balances inc tradable.
    # Outputs:
    # {"LTC":{"available":"5.015","onOrders":"1.0025","btcValue":"0.078"},"NXT:{...} ... }
    def returnCompleteBalances(self):
        return self.api_query('returnCompleteBalances')
    # Returns all of your balances inc exchange lending.
    # Outputs:
    # {"LTC":{"available":"5.015","onOrders":"1.0025","btcValue":"0.078"},"NXT:{...} ... }
    def returnAllCompleteBalances(self):
        return self.api_query('returnCompleteBalances', {'account': 'all'})

    # tradable pair to how much you can buy/sell
    # e.g
    # {'BTC_STR': {'STR': '0.00000000', 'BTC': '0.00000000'}, 'BTC_DOGE': {'DOGE': '0.00000000', 'BTC': '0.00000000'}, 'BTC_XRP': {'BTC': '0.00000000', 'XRP': '0.00000000'}, 'BTC_LTC': {'LTC': '0.00000000', 'BTC': '0.00000000'}, 'BTC_ETH': {'BTC': '0.00000000', 'ETH': '0.00000000'}, 'BTC_DASH': {'BTC': '0.00000000', 'DASH': '0.00000000'}, 'BTC_FCT': {'BTC': '0.00000000', 'FCT': '0.00000000'}, 'BTC_MAID': {'MAID': '0.00000000', 'BTC': '0.00000000'}, 'BTC_XMR': {'BTC': '0.00000000', 'XMR': '0.00000000'}, 'BTC_CLAM': {'BTC': '0.00000000', 'CLAM': '0.00000000'}, 'BTC_BTS': {'BTC': '0.00000000', 'BTS': '0.00000000'}}
    def returnMarginTradableBalances(self):
        return self.api_query('returnTradableBalances')
    # margin positions
    # e.g
    # {"amount":"40.94717831","total":"-0.09671314",""basePrice":"0.00236190","liquidationPrice":-1,"pl":"-0.00058655", "lendingFees":"-0.00000038","type":"long"}
    def getMarginPosition(self):
        return self.api_query('getMarginPosition', {'currencyPair': 'all'})

    # Returns all of your balances inc tradable.
    # Outputs:
    # {"exchange":{"BTC":"1.19042859","BTM":"386.52379392","CHA":"0.50000000","DASH":"120.00000000","STR":"3205.32958001", "VNL":"9673.22570147"},"margin":{"BTC":"3.90015637","DASH":"250.00238240","XMR":"497.12028113"},"lending":{"DASH":"0.01174765","LTC":"11.99936230"}}
    def returnAvailableAccountBalances(self):
        return self.api_query('returnAvailableAccountBalances', {})

    # Returns your open orders for a given market, specified by the "currencyPair" POST parameter, e.g. "BTC_XCP"
    # Inputs:
    # currencyPair  The currency pair e.g. "BTC_XCP"
    # Outputs:
    # orderNumber   The order number
    # type          sell or buy
    # rate          Price the order is selling or buying at
    # Amount        Quantity of order
    # total         Total value of order (price * quantity)
    def returnOpenOrders(self, currencyPair):
        return self.api_query('returnOpenOrders', {"currencyPair": currencyPair})

    def cancellAllOrders(self):
        orders = self.returnOpenOrders('all').result().json()
        cancel_requests = []
        for pair, pairs_orders in orders.items():
            for order in pairs_orders:
                if 'orderNumber' in order:
                    cancel_requests.append(self.cancel(pair, order['orderNumber']))
                else:
                    logger.info(orders)
        for request in cancel_requests:
            success = request.result()
            if not success:
                logger.error('couldnt cancel order : {}'.format(success.json()))

    # Returns your trade history for a given market, specified by the "currencyPair" POST parameter
    # Inputs:
    # currencyPair  The currency pair e.g. "BTC_XCP"
    # Outputs:
    # date          Date in the form: "2014-02-19 03:44:59"
    # rate          Price the order is selling or buying at
    # amount        Quantity of order
    # total         Total value of order (price * quantity)
    # type          sell or buy
    def returnTradeHistory(self, currencyPair):
        return self.api_query('returnTradeHistory', {"currencyPair": currencyPair})

    buys_for_pair = defaultdict(list)
    sells_for_pair = defaultdict(list)

    ##{"orderNumber":31226040,"resultingTrades":[{"amount":"338.8732","date":"2014-10-18 23:03:21","rate":"0.00000173","total":"0.00058625","tradeID":"16164","type":"buy"}]}

    # Places a buy order in a given market. Required POST parameters are "currencyPair", "rate", and "amount". If successful, the method will return the order number.
    # Inputs:
    # currencyPair  The curreny pair
    # rate          price the order is buying at
    # amount        Amount of coins to buy
    # Outputs:
    # orderNumber   The order number
    def buy(self, currencyPair, rate, amount, postOnly='1'):
        request_data = {"currencyPair": currencyPair, "rate": rate, "amount": amount, "postOnly": postOnly}
        if rate * amount < .0001:
            logger.info('predict {} too low'.format(request_data))
            return
        order_result = self.api_query('buy', request_data).result()
        logger.info(order_result.status_code)
        result_json = order_result.json()
        if order_result.status_code == 200:
            self.buys_for_pair[currencyPair].append(result_json)
        logger.info(result_json)
        logger.info(request_data)

    # Places a sell order in a given market. Required POST parameters are "currencyPair", "rate", and "amount". If successful, the method will return the order number.
    # Inputs:
    # currencyPair  The curreny pair
    # rate          price the order is selling at
    # amount        Amount of coins to sell
    # Outputs:
    # orderNumber   The order number
    def sell(self, currencyPair, rate, amount, postOnly='1'):
        request_data = {"currencyPair": currencyPair, "rate": rate, "amount": amount, "postOnly": postOnly}
        if rate * amount < .0001:
            logger.info('predict {} too low'.format(request_data))
            return
        order_result = self.api_query('sell', {"currencyPair": currencyPair, "rate": rate, "amount": amount}).result()

        logger.info(order_result.status_code)
        order_result_json = order_result.json()
        logger.info(order_result_json)
        if order_result.status_code == 200:
            self.sells_for_pair[currencyPair].append(order_result_json)

        logger.info(request_data)

    # Places a buy order in a given market. Required POST parameters are "currencyPair", "rate", and "amount". If successful, the method will return the order number.
    # Inputs:
    # currencyPair  The curreny pair
    # rate          price the order is buying at
    # amount        Amount of coins to buy
    # Outputs:
    # orderNumber   The order number
    def marginBuy(self, currencyPair, rate, amount, postOnly='1'):
        request_data = {"currencyPair": currencyPair, "rate": rate, "amount": amount, "postOnly": postOnly}
        if rate * amount < .0001:
            logger.info('predict {} too low'.format(request_data))
            return
        order_result = self.api_query('marginBuy', request_data).result()
        logger.info(order_result.status_code)
        result_json = order_result.json()
        if order_result.status_code == 200:
            self.buys_for_pair[currencyPair].append(result_json)
        logger.info(result_json)
        logger.info(request_data)

    # Places a sell order in a given market. Required POST parameters are "currencyPair", "rate", and "amount". If successful, the method will return the order number.
    # Inputs:
    # currencyPair  The curreny pair
    # rate          price the order is selling at
    # amount        Amount of coins to sell
    # Outputs:
    # orderNumber   The order number
    def marginSell(self, currencyPair, rate, amount, postOnly='1'):
        request_data = {"currencyPair": currencyPair, "rate": rate, "amount": amount, "postOnly": postOnly}
        if rate * amount < .0001:
            logger.info('predict {} too low'.format(request_data))
            return
        order_result = self.api_query('marginSell', {"currencyPair": currencyPair, "rate": rate, "amount": amount}).result()

        logger.info(order_result.status_code)
        order_result_json = order_result.json()
        logger.info(order_result_json)
        if order_result.status_code == 200:
            self.sells_for_pair[currencyPair].append(order_result_json)

        logger.info(request_data)

    # Cancels an order you have placed in a given market. Required POST parameters are "currencyPair" and "orderNumber".
    # Inputs:
    # currencyPair  The curreny pair
    # orderNumber   The order number to cancel
    # Outputs:
    # succes        1 or 0
    def cancel(self, currencyPair, orderNumber):
        return self.api_query('cancelOrder', {"currencyPair": currencyPair, "orderNumber": orderNumber})

    # Immediately places a withdrawal for a given currency, with no email confirmation. In order to use this method, the withdrawal privilege must be enabled for your API key. Required POST parameters are "currency", "amount", and "address". Sample output: {"response":"Withdrew 2398 NXT."}
    # Inputs:
    # currency      The currency to withdraw
    # amount        The amount of this coin to withdraw
    # address       The withdrawal address
    # Outputs:
    # response      Text containing message about the withdrawal
    def withdraw(self, currency, amount, address):
        return self.api_query('withdraw', {"currency": currency, "amount": amount, "address": address})
