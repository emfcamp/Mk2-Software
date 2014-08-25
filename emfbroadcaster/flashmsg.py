#!/usr/bin/env python
import logging
import json
import requests
import tinypacks
import sys

config = json.load(open('../etc/config.json'))

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('flashmsg')

## TODO: make this settable via CLI options:
msg = sys.argv[1]
rgb1 = (0, 0, 255)
rgb2 = (0, 255, 0)
sound = 0
typebyte = 1
##

packed = b""
packed += tinypacks.pack(rgb1[0])
packed += tinypacks.pack(rgb1[1])
packed += tinypacks.pack(rgb1[2])
packed += tinypacks.pack(rgb2[0])
packed += tinypacks.pack(rgb2[1])
packed += tinypacks.pack(rgb2[2])
packed += tinypacks.pack(sound)
packed += tinypacks.pack(typebyte)
packed += tinypacks.pack(msg)

logger.info("Sending content...")
url = config['flashMsgEndpoint']
response = requests.post(url=url, params={}, data=packed)

if (response.status_code == 200):
    logger.info("OK")
else:
    logger.info("Response from MCP: %s", response)
    logger.warn("There was a problem.")
