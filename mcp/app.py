#!/usr/bin/env python
import json
import logging
from lib import *
import lib

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Load config file
config = json.load(open('config.json'))

# Inject dependencies
dataQueue = lib.DataQueue()
messageReplenisher = lib.MessageReplenisher(config, dataQueue)
mcpTcpServer = lib.McpTcpServer(config, dataQueue);
mainChannelSender = lib.MainChannelSender(config, mcpTcpServer, dataQueue)
discoveryChannelTimer = lib.DiscoveryChannelTimer(config, mcpTcpServer);
main = lib.Main(config, mcpTcpServer)

# Start
messageReplenisher.start()
discoveryChannelTimer.start()
mainChannelSender.start()
main.start()