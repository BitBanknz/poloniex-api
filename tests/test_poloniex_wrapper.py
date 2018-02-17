import unittest

poloniex_key = "KEY_HERE"
poloniex_secret = "KEY_HERE"

from poloniex.poloniex_wrapper import poloniex
from requests_futures.sessions import FuturesSession

session = FuturesSession(max_workers=10)

poloniex = poloniex(poloniex_key, poloniex_secret, session)


class TestPoloniexWrapper(unittest.TestCase):
    @unittest.skip
    def test_cancell_all(self):
        poloniex.cancellAllOrders()

    def test_margin_tradable_balance(self):
        balances = poloniex.returnMarginTradableBalances()
        json = balances.result().json()
        print(json)
        self.assertIn('BTC', json['BTC_ETH'])
        self.assertIn('ETH', json['BTC_ETH'])

    def test_available_tradable_balance(self):
        balances = poloniex.returnAvailableAccountBalances()
        json = balances.result().json()
        print(json)
        self.assertIn('XMR', json['exchange'])
        self.assertIn('ETH', json['exchange'])

    def test_balance(self):
        balances = poloniex.returnBalances()
        json = balances.result().json()
        print(json)
        self.assertIn('BTC', json)
        self.assertIn('ETH', json)

    def test_complete_tradable_balance(self):
        balances = poloniex.returnAllCompleteBalances()
        json = balances.result().json()
        print(json)

    def test_getMarginPosition(self):
        balances = poloniex.getMarginPosition()
        json = balances.result().json()
        print(json)
        self.assertIn('pl', json['BTC_ETH'])
        self.assertIn('basePrice', json['BTC_ETH'])


if __name__ == '__main__':
    unittest.main()
