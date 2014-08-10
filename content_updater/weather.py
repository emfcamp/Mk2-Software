#!/usr/bin/env python
import psycopg2
import logging
import json
import requests
import struct
import sys
import binascii
import tinypacks
import time

config = json.load(open('config.json'))

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('weather');

logger.info("Fetching current weather conditions...")

# Get id from http://datapoint.metoffice.gov.uk/public/data/val/wxfcs/all/json/350493?res=3hourly&key=xxxxxxx
url = 'http://datapoint.metoffice.gov.uk/public/data/val/wxfcs/all/json/{0}'.format(config['metLocationId'])

params = dict(
    res='3hourly',
    key=config['metOfficeApiKey']
)

resp = requests.get(url=url, params=params)
data = json.loads(resp.text);

daysWithForecast = data['SiteRep']['DV']['Location']['Period'];

forecasts = []

for day in daysWithForecast:
    forecasts += day['Rep']

logger.info("Found %d 3-hourly forecasts", len(forecasts))

times = [
    {'name': 'now', 'index': 0},
    {'name': 'in3Hours', 'index': 1},
    {'name': 'in6Hours', 'index': 2},
    {'name': 'in12Hours', 'index': 4},
    {'name': 'in24Hours', 'index': 8},
    {'name': 'in48Hours', 'index': 16},
];

jsonToBePacked = [];
packedForecasts = b"";
for timeElement in times:
    forecast = forecasts[timeElement['index']];
    timestamp = int(round(time.time())) # ToDo: Use real time from the API
    weatherType = int(forecast['W'])
    temperature = int(forecast['T'])
    windSpeed = int(forecast['S'])
    feelsLikeTemperature = int(forecast['F'])
    screenRelativeHumidity = int(forecast['H'])
    precipitationProbability = int(forecast['Pp'])
    logger.info("timestamp: %d", timestamp);
    logger.info("temperature: %d", temperature);
    logger.info("weatherType: %d", weatherType);
    packedForecasts += tinypacks.pack(timestamp);
    packedForecasts += tinypacks.pack(weatherType);
    packedForecasts += tinypacks.pack(temperature);
    packedForecasts += tinypacks.pack(feelsLikeTemperature);
    packedForecasts += tinypacks.pack(windSpeed);
    packedForecasts += tinypacks.pack(screenRelativeHumidity);
    packedForecasts += tinypacks.pack(precipitationProbability);

#print jsonToBePacked
##packedForecasts = tinypacks.pack(jsonToBePacked)

#result = tinypacks.unpack(packedForecasts)
print binascii.hexlify(packedForecasts)

logger.info("Content length: %d", len(packedForecasts))

# Connect do db
logger.info("Connection to DB...")
conn = psycopg2.connect(config['dbConnectionString'])
cursor = conn.cursor()

# Update content
logger.info("Upating content...")
contentAsHexString = binascii.hexlify(packedForecasts)
cursor.execute("UPDATE content SET content = decode(%(content)s, 'hex') WHERE name = 'WEATHER_FORECAST';", {'content': contentAsHexString});
conn.commit()
cursor.close()
conn.close()

logger.info("All done")