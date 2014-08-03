import logging
import signal
import tornado
import struct
import binascii
import time
import unicodedata
import psycopg2

class MessageReplenisher:
    def __init__(self, config, dataQueue):
        self.config = config
        self.dataQueue = dataQueue
        self.dataQueue.add_drain_handler(self.queue_has_drained)
        self.logger = logging.getLogger('messageReplenisher')

    def start(self):
        self.logger.info("Connection to DB...")
        self.conn = psycopg2.connect(self.config['dbConnectionString'])
        self.cursor = self.conn.cursor()

    #def end():
    #    self.cursor.close()
    #    self.conn.close()

    def queue_has_drained(self, connectionId):
        self.cursor.execute("SELECT content FROM content WHERE name = 'WEATHER_FORECAST';");
        (payload, ) = self.cursor.fetchone()
        self.dataQueue.add_message(connectionId, 40962, payload)
        

