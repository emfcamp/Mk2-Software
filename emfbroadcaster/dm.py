#!/usr/bin/env python
import logging
import json
import requests
import tinypacks

config = json.load(open('../etc/config.json'))

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('dm')

## TODO: make this settable via CLI options:
msg = "This is a DM!"
rgb1 = (0, 0, 255)
rgb2 = (0, 255, 0)
sound = 0
badge = 6
##

packed = b""
packed += tinypacks.pack(rgb1[0])
packed += tinypacks.pack(rgb1[1])
packed += tinypacks.pack(rgb1[2])
packed += tinypacks.pack(rgb2[0])
packed += tinypacks.pack(rgb2[1])
packed += tinypacks.pack(rgb2[2])
packed += tinypacks.pack(sound)
packed += tinypacks.pack(msg)

logger.info("Sending content...")
url = config['dmMsgEndpoint']
response = requests.post(url=url, params={'badge': 6}, data=packed)

if (response.status_code == 200):
    logger.info("OK")
else:
    logger.info("Response from MCP: %s", response)
    logger.warn("There was a problem.")
