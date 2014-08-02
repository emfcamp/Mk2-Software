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
mcpTcpServer = lib.McpTcpServer(config);
discoveryChannelTimer = lib.DiscoveryChannelTimer(config, mcpTcpServer);
main = lib.Main(config, mcpTcpServer)

# Start
discoveryChannelTimer.start()
main.start()