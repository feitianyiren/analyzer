from datetime import datetime, timedelta
from threading import Thread

from analyzer.backtest.tick_feeder import TickFeeder, QuoteFeeder
from analyzer.backtest.trading_center import TradingCenter
from analyzer.backtest.trading_engine import TradingEngine
from analyzer.backtest.backtester import BackTester
from analyzerdam.DAMFactory import DAMFactory

from analyzer.backtest.constant import (
    CONF_ANALYZER_SECTION,
)


class TickFeederThread(Thread):
    """
        This is used to retrieve realtime info
        and broadcast to all trading engines
    """

    def __init__(self, config, pubsub, securities, start=None, end=None):
        Thread.__init__(self)
        self.config = config
        if config.get(CONF_ANALYZER_SECTION, 'feed_type') == 'quote':
            klass = QuoteFeeder
        if config.get(CONF_ANALYZER_SECTION, 'feed_type') == 'tick':
            klass = TickFeeder

        self.tick_feeder = klass(
            publisher=pubsub,
            securities=securities,
            dam=self._create_dam(""),  # no need to set symbol because it's batch operation
        )
        self.last_execution = datetime.now()

    def _create_dam(self, symbol):
        dam_name = self.config.get(CONF_ANALYZER_SECTION, 'dam')
        dam = DAMFactory.createDAM(dam_name, self.config)
        dam.symbol = symbol

        return dam

    def run(self):
        while True:
            import ipdb
            ipdb.set_trace()
            self.last_execution = datetime.now()
            self.tick_feeder.execute(self.last_execution, datetime.now() + timedelta(minutes=10))
            import time
            time.sleep(2000)


class TradingCenterThread(Thread):

    def __init__(self, session, pubsub):
        Thread.__init__(self)
        self.trading_center = TradingCenter(session, pubsub)

    def run(self):
        while True:
            self.trading_center.consume()


class TradingEngineThread(Thread):

    def __init__(self, pubsub, securities, strategy):
        Thread.__init__(self)
        self.trading_engine = TradingEngine(pubsub, strategy)
        for security in securities:
            self.trading_engine.listen(security)

    def run(self):
        while True:
            self.trading_engine.consume()


class MetricThread(Thread):

    def __init__(self, session, pubsub):
        Thread.__init__(self)


class BackTesterThread(Thread):
    """
        This thread will retrieve info from the
        store and it will broadcast it
        to all trading engines.
        Trading Center must ignore this
        since is not realtime

    """

    def __init__(self, store, pubsub, securities, start, end):
        Thread.__init__(self)
        self.backtester = BackTester(store, pubsub, securities, start, end)

    def run(self):
        while True:
            self.backtester.consume()
