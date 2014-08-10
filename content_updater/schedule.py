#!/usr/bin/env python
import psycopg2
import logging
import json
import requests
import struct
import sys
import binascii
import time
import tinypacks

config = json.load(open('config.json'))

scheduleJson = json.load(open('../emw-talks.json'))

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('weather');

logger.info("Updating schedule");

stageIds = {
    "Stage Alpha": 1,
    "Stage Beta": 2,
    "Workshop": 3
}

typeIds = {
    "talk": 1,
    "lightning": 2,
    "workshop": 3
}

talks = []
for stage in scheduleJson['stages']:
    stageName = stage['name']
    stageId = stageIds[stageName]
    for event in stage['events']:
        typeId = typeIds[event['type']]
        startTimestamp = int(round(time.mktime(time.strptime(event['start'], "%Y-%m-%d %H:%M:%S"))));
        endTimestamp = int(round(time.mktime(time.strptime(event['end'], "%Y-%m-%d %H:%M:%S"))));

        speaker = "";
        if 'speaker' in event:
            speaker = event['speaker']

        talks.append({
            "stageId": stageId,
            "typeId": typeId,
            "start": startTimestamp,
            "end": endTimestamp,
            "speaker": speaker,
            "title": event['title'],
           # event['description'] Thiss is quite a lot of data. Leaving it out for now
        })

packed = tinypacks.pack(len(talks));
for talk in talks:
    packed += tinypacks.pack(talk['stageId']);
    packed += tinypacks.pack(talk['typeId']);
    packed += tinypacks.pack(talk['start']);
    packed += tinypacks.pack(talk['end']);
    packed += tinypacks.pack(talk['speaker']);
    packed += tinypacks.pack(talk['title']);

print binascii.hexlify(packed)
logger.info("Content length: %d", len(packed))

# Connect do db
logger.info("Connection to DB...")
conn = psycopg2.connect(config['dbConnectionString'])
cursor = conn.cursor()

# Update content
logger.info("Upating content...")
contentAsHexString = binascii.hexlify(packed)
cursor.execute("UPDATE content SET content = decode(%(content)s, 'hex') WHERE name = 'SCHEDULE_FRIDAY';", {'content': contentAsHexString});
conn.commit()
cursor.close()
conn.close()

logger.info("All done")