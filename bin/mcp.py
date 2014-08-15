#!/usr/bin/env python
import json
import logging
import emfmcp


# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Load config file
config = json.load(open('etc/config.json'))

# Inject dependencies
dataQueue = emfmcp.DataQueue()
messageReplenisher = emfmcp.MessageReplenisher(config, dataQueue)
mcpTcpServer = emfmcp.McpTcpServer(config, dataQueue)
mainChannelSender = emfmcp.MainChannelSender(config, mcpTcpServer, dataQueue)
discoveryChannelTimer = emfmcp.DiscoveryChannelTimer(config, mcpTcpServer)
main = emfmcp.Main(config, mcpTcpServer)

# Start
##messageReplenisher.start()
discoveryChannelTimer.start()
mainChannelSender.start()
main.start()
