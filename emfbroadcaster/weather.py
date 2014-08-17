#!/usr/bin/env python
import logging
import json
import requests
import struct
import sys
import binascii
import tinypacks
import datetime
import calendar
import time

config = json.load(open('../etc/config.json'))
secret_config = json.load(open('../etc/secret_config.json'))

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('weather');

params = dict(
    res='3hourly',
    key=secret_config['metOfficeApiKey']
)

logger.info("Fetching timestamps...")
url = 'http://datapoint.metoffice.gov.uk/public/data/val/wxfcs/all/json/capabilities'
resp = requests.get(url=url, params=params)
timestamps_json = json.loads(resp.text);
timestamps_text = timestamps_json['Resource']['TimeSteps']['TS']
timestamps = []
logger.info("%d timestamps found", len(timestamps))

start_index = 0;
for timestamp_text in timestamps_text:
    timestamp = calendar.timegm(datetime.datetime.strptime(timestamp_text, "%Y-%m-%dT%H:%M:%SZ").timetuple())
    if timestamp < time.time():
        start_index += 1
    timestamps.append(timestamp)

logger.info("Start with index: %d", start_index)

logger.info("Fetching current weather conditions...")

# Get id from http://datapoint.metoffice.gov.uk/public/data/val/wxfcs/all/json/350493?res=3hourly&key=xxxxxxx
url = 'http://datapoint.metoffice.gov.uk/public/data/val/wxfcs/all/json/{0}'.format(config['metLocationId'])

resp = requests.get(url=url, params=params)
data = json.loads(resp.text);

daysWithForecast = data['SiteRep']['DV']['Location']['Period'];

forecasts = []

for day in daysWithForecast:
    forecasts += day['Rep']

logger.info("Found %d 3-hourly forecasts", len(forecasts))

times = [
    {'name': 'now', 'index': start_index},
    {'name': 'in3Hours', 'index': start_index + 1},
    {'name': 'in6Hours', 'index': start_index + 2},
    {'name': 'in12Hours', 'index': start_index + 4},
    {'name': 'in24Hours', 'index': start_index + 8},
    {'name': 'in48Hours', 'index': start_index + 16},
];

jsonToBePacked = [];
packedForecasts = b"";
for timeElement in times:
    forecast = forecasts[timeElement['index']]
    timestamp = timestamps[timeElement['index']]
    weatherType = int(forecast['W'])
    temperature = int(forecast['T'])
    windSpeed = int(forecast['S'])
    feelsLikeTemperature = int(forecast['F'])
    screenRelativeHumidity = int(forecast['H'])
    precipitationProbability = int(forecast['Pp'])
    logger.info("timestamp: %d - %s UTC", timestamp, datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'));
    logger.info("temperature: %d", temperature);
    logger.info("weatherType: %d", weatherType);
    packedForecasts += tinypacks.pack(timestamp);
    packedForecasts += tinypacks.pack(weatherType);
    packedForecasts += tinypacks.pack(temperature);
    packedForecasts += tinypacks.pack(feelsLikeTemperature);
    packedForecasts += tinypacks.pack(windSpeed);
    packedForecasts += tinypacks.pack(screenRelativeHumidity);
    packedForecasts += tinypacks.pack(precipitationProbability);


logger.info("Content length: %d", len(packedForecasts))

# Update content
logger.info("Sending content...")
params = dict(
    res='3hourly',
    key=secret_config['metOfficeApiKey']
)
url = "http://localhost:8888/send?rid=40962"
response = requests.post(url=url, params=params, data=packedForecasts)

logger.info("Response from MCP: %s", response)

logger.info("All done")