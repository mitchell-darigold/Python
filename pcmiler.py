import requests


# CalcMiles documentation: https://developer.trimblemaps.com/restful-apis/routing/route-reports/calc-miles/
# Geocoding documentation: https://developer.trimblemaps.com/restful-apis/location/geocoding-api/geocoding/

BASE_URL = 'https://pcmiler.alk.com/apis/rest/v1.0/service.svc'

GEO_CODING_API = '/locations'

MILES_API = '/route/routeReports'

API_KEY = 'ACF849667AFC3F4C81781244A3388250'


class PcMiler:
	'''
	'''


	def __init__(self):
		self.headers = {'authorization': API_KEY}

		self.geo_coding_url = f'{BASE_URL}{GEO_CODING_API}'

		self.miles_url = f'{BASE_URL}{MILES_API}'


	def get_miles_by_lat_lon(self, src_lat, src_lon, dest_lat, dest_lon):
		params = f'stops={src_lon}%2C{src_lat}%3B{dest_lon}%2C{dest_lat}&reports=CalcMiles'

		url = f'{self.miles_url}?{params}'
		
		req = requests.get(url, headers=self.headers)
		
		if req.status_code == 200:
			return req.json()[0]['TMiles']


	def get_miles_by_zip(self, src_zip, dest_zip):
		src_coords = self._get_coords_by_zip(src_zip)
		dest_coords = self._get_coords_by_zip(dest_zip)

		if src_coords and dest_coords:
			return self.get_miles_by_lat_lon(
				src_coords['Lat'], src_coords['Lon'], 
				dest_coords['Lat'], dest_coords['Lon']
				)


	def get_miles_by_city_state_country(self, src_city, src_state, src_country, dest_city, dest_state, dest_country):
		src_coords = self._get_coords_by_city_state_country(
			src_city, src_state, src_country
			)
		dest_coords = self._get_coords_by_city_state_country(
			dest_city, dest_state, dest_country
			)
		
		if src_coords and dest_coords:
			return self.get_miles_by_lat_lon(
				src_coords['Lat'], src_coords['Lon'], 
				dest_coords['Lat'], dest_coords['Lon']
				)


	def _get_coords_by_zip(self, zip):
		params = f'postcode={zip}'

		return self._get_coords(params)


	def _get_coords_by_city_state_country(self, city, state, country):
		city = city.replace(' ', '%20')

		params = f'city={city}&state={state}&country={country}'

		return self._get_coords(params)


	def _get_coords(self, params):
		url = f'{self.geo_coding_url}?{params}'
		
		req = requests.get(url, headers=self.headers)
		
		if req.status_code == 200:
			return req.json()[0]['Coords']


if __name__ == '__main__':
	# for testing (Boise Market Street, Boise, ID -> Costco, Salt Lake City, UT)
	src_lat = '43.5831'
	src_lon = '-119.99'
	dest_lat = '39.3953'
	dest_lon = '-119.727'

	src_zip = '83705'
	dest_zip = '84115'

	pc_miler = PcMiler()

	coords_miles = pc_miler.get_miles_by_lat_lon(src_lat, src_lon, dest_lat, dest_lon)

	zip_miles = pc_miler.get_miles_by_zip(src_zip, dest_zip)

	city_miles = pc_miler.get_miles_by_city_state_country('Boise', 'ID', 'US', 'Salt Lake City', 'UT', 'US')

	print('by coords', coords_miles)
	print('by zip', zip_miles)
	print('by city state country', city_miles)


