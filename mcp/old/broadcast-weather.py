import json, requests
import struct
import sys

config = json.load(open('config.json'))

# Get id from http://datapoint.metoffice.gov.uk/public/data/val/wxfcs/all/json/350493?res=3hourly&key=xxxxxxx
url = 'http://datapoint.metoffice.gov.uk/public/data/val/wxfcs/all/json/350493' #Bletchley

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

times = [
	{'name': 'now', 'index': 0},
	{'name': 'in3Hours', 'index': 1},
	{'name': 'in6Hours', 'index': 2},
	{'name': 'in12Hours', 'index': 4},
	{'name': 'in24Hours', 'index': 8},
	{'name': 'in48Hours', 'index': 16},
];

packedForecasts = b"";
for time in times:
	forecast = forecasts[time['index']];
	weatherType = int(forecast['W'])
	temperature = int(forecast['T'])
	windSpeed = int(forecast['S'])
	feelsLikeTemperature = int(forecast['F'])
	screenRelativeHumidity = int(forecast['H'])
	precipitationProbability = int(forecast['Pp'])
	packedForecasts += struct.pack('> B b b B B B', weatherType, temperature, feelsLikeTemperature, windSpeed, screenRelativeHumidity, precipitationProbability);

sys.stdout.write(packedForecasts)
