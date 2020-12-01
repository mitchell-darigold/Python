from collections import defaultdict
from datetime import datetime, timedelta
from model import Model
import pandas as pd
import sqlite3 as sql

import constants as const
from pcmiler import PcMiler
import utilities as util


REPORT_NAME = 'Order Level Report'

ACCS_COL = 'Accesorials'
#ACTUAL_DELIV_DATE_COL = 'ActualDeliveryDate'
#ACTUAL_SHIP_DATE_COL = 'ActualShipDate'
#ACTUAL_DELIV_DATE_DEPART_COL = 'ActualDelivDateDepart'
#ACTUAL_SHIP_DATE_DEPART_COL = 'ActualShipDateDepart'
PICKUP_ARRIVE = 'PickupArrive'
PICKUP_DEPART = 'PickupDepart'
DELIVERY_ARRIVE = 'DeliveryArrive'
DELIVERY_DEPART = 'DeliveryDepart'

BUS_UNIT_COL = 'BusinessUnit'
CANCEL_STATUS_COL = 'CancelStatus'
DEST_CITY_COL = 'DestCity'
DEST_COL = 'DestLocationName'
DEST_ID_COL = 'DestLocationID'
DEST_STATE_COL = 'DestProvinceCode'
DEST_COUNTRY_COL = 'DestCountry'
DEST_LAT_COL = 'DestLat'
DEST_LON_COL = 'DestLon'
DEST_ZIP_COL = 'DestPostalCode'
END_TIME_COL = 'ShipmentEndTime'
GL_CODE_COL = 'GLCode'
ITEM_COL = 'ItemDescription'
INTL_FLAG_COL = 'InternationalFlag'
IS_SPOT_COSTED_COL = 'SpotCosted'
MODE_COL = 'Mode'
ORD_ID_COL = 'OrderReleaseID'
ORD_LINE_ID_COL = 'OrderReleaseLineID'
INS_DATE_COL = 'OrderInsertDate'
ORD_TYPE_COL = 'OrderReleaseType'
PLAN_DELIV_DATE_COL = 'PlannedDeliveryDate'
PLAN_SHIP_DATE_COL = 'PlannedShipDate'
PROD_GRP_COL = 'ProductGroup'
SRC_CITY_COL = 'SourceCity'
SRC_COUNTRY_COL = 'SourceCountry'
SRC_LAT_COL = 'SourceLat'
SRC_LON_COL = 'SourceLon'
SRC_STATE_COL = 'SourceProvinceCode'
SRC_ZIP_COL = 'SourcePostalCode'
START_TIME_COL = 'ShipmentStartTime'
TOT_COST_COL = 'TotalActualShipmentCost'
WT_COL = 'Weight'
WT_UOM_COL = 'WeightUOM'
STOP_NUM_COL = 'StopNum'
PLANNED_DELIVERY_ARRIVE = 'PlannedDeliveryArrive'
PLANNED_DELIVERY_DEPART = 'PlannedDeliveryDepart'
SHIP_ARRIVE = 'ShipArrive'
SHIP_DEPART = 'ShipDepart'
PLANNED_SHIP_ARRIVE = 'PlannedShipArrive'
PLANNED_SHIP_DEPART = 'PlannedShipDepart'
PLANNED_PICKUP_DEPART = 'PlannedPickupDepart'
SHIP_DESTCODE = 'ShipDestCode'
SHIP_DESTNAME = 'ShipDestName'
SHIP_DESTCITY = 'ShipDestCity'
SHIP_DESTSTATE = 'ShipDestState'
SHIP_DESTZIP = 'ShipDestZip'
SHIP_DESTCOUNTRY = 'ShipDestCountry'
SHIP_DESTLAT = 'ShipDestLat'
SHIP_DESTLON = 'ShipDestLon'

'''
	Columns from source files not utilized
		LeadTimeFlag
		LocationChangeFlag
		PackagedItemID
		ShipWithGroup
		TrailerID
		VoucherGlCost
'''

PLAN_DAY_ROW = 1
PLAN_YR_ROW = 2
HEADER_ROW = 7
FIRST_DATA_ROW = HEADER_ROW + 1

class OrderLevel:
	'''
	'''


	def __init__(self, df, name):
		self.df = df
		self.name = name
		
		self.pc_miler = PcMiler()

		self.miles = {}

		self.alloc_factor_by_ship = defaultdict(float)

		self.miles_by_ship_dest = defaultdict(float)

		self.ship_stop_count = defaultdict(int)


	def _set_measures_by_ship_dest(self):
		con = sql.connect(':memory:')

		table = 'data'

		self.df.to_sql(table, con)

		ship_dest_query = f'''
			SELECT DISTINCT
				{const.SHIP_ID_COL},
				{DEST_ID_COL},
				{SRC_LAT_COL},
				{SRC_LON_COL},
				{SRC_ZIP_COL},
				{SRC_CITY_COL},
				{SRC_STATE_COL},
				{SRC_COUNTRY_COL},
				{DEST_LAT_COL},
				{DEST_LON_COL},
				{DEST_ZIP_COL},
				{DEST_CITY_COL},
				{DEST_STATE_COL},
				{DEST_COUNTRY_COL},
				SUM({WT_COL}) dest_wt,
				{const.FUEL_COL},
				{const.LN_HAUL_COL},
				{TOT_COST_COL}

			FROM {table}

			GROUP BY {const.SHIP_ID_COL}, {DEST_ID_COL}
			'''

		df = pd.read_sql(ship_dest_query, con)

		df['miles'] = df.apply(self._get_miles, axis=1)
		
		row_count = len(df)

		for i, row in enumerate(df.itertuples(index=False)):
			print(f'Processing row {i} of {row_count}...')

			ship_id = getattr(row, const.SHIP_ID_COL)
			dest_id = getattr(row, DEST_ID_COL)
			
			key = (ship_id, dest_id)
			
			dest_miles = getattr(row, 'miles')
			dest_wt = getattr(row, 'dest_wt')
			
			self.miles_by_ship_dest[key] = dest_miles
			
			dest_alloc_factor = dest_miles * dest_wt

			self.alloc_factor_by_ship[ship_id] += dest_alloc_factor

			self.ship_stop_count[ship_id] += 1
		
		con.close()

	def _get_miles(self, row):
		src_city = getattr(row, SRC_CITY_COL)
		src_state = getattr(row, SRC_STATE_COL)
		src_country = getattr(row, SRC_COUNTRY_COL)
		dest_city = getattr(row, DEST_CITY_COL)
		dest_state = getattr(row, DEST_STATE_COL)
		dest_country = getattr(row, DEST_COUNTRY_COL)
		
		lane = f'{src_city}{src_state}{src_country}{dest_city}{dest_state}{dest_country}'
		print(f'getting miles for {lane}...')
		if lane in self.miles:
			miles = self.miles[lane]
		else:
			miles = None

			search_by_zip = True
			search_by_city = True

			src_lat = getattr(row, SRC_LAT_COL)

			if src_lat:
				dest_lat = getattr(row, DEST_LAT_COL)

				if dest_lat:
					src_lon = getattr(row, SRC_LON_COL)
					dest_lon = getattr(row, DEST_LON_COL)

					miles = self.pc_miler.get_miles_by_lat_lon(src_lat, src_lon, dest_lat, dest_lon)
					

					if miles:
						search_by_zip = False
						search_by_city = False
						
			if search_by_zip:
				src_zip = getattr(row, SRC_ZIP_COL)

				if src_zip:
					dest_zip = getattr(row, DEST_ZIP_COL)

					miles = self.pc_miler.get_miles_by_zip(src_zip, dest_zip)
					

					if miles:
						search_by_city = False
						
			if search_by_city:
				miles = self.pc_miler.get_miles_by_city_state_country(
					src_city, src_state, src_country, dest_city, dest_state, dest_country
					)
					

			if miles is not None:
				self.miles[lane] = miles

		return miles


	def main(self):
		rows = []
		 
		export_date = self.df.at[const.EXPORT_DATE_ROW, REPORT_NAME]

		column_names = self.df.iloc[[HEADER_ROW]].values[0]
		self.df.columns = util.clean_column_names(column_names)

		# removes metadata rows
		self.df.drop([i for i in range(FIRST_DATA_ROW)], inplace=True)
		
		self._set_measures_by_ship_dest()

		for row in self.df.itertuples(index=False):
			delivery_arrive = getattr(row, DELIVERY_ARRIVE)
			pickup_arrive = getattr(row, PICKUP_ARRIVE)
			delivery_depart = getattr(row, DELIVERY_DEPART)
			pickup_depart = getattr(row, PICKUP_DEPART)
			carrier = getattr(row, const.SERV_PROV_COL)
			dest_city = getattr(row, DEST_CITY_COL)
			dest_id = getattr(row, DEST_ID_COL)
			dest_name = getattr(row, DEST_COL)
			dest_state = getattr(row, DEST_STATE_COL)
			equip = getattr(row, const.EQP_COL)
			fuel = getattr(row, const.FUEL_COL)
			is_spot_cost = getattr(row, IS_SPOT_COSTED_COL)
			line_haul = getattr(row, const.LN_HAUL_COL)
			product = getattr(row, ITEM_COL)
			ord_type = getattr(row, ORD_TYPE_COL)
			plan_deliv = getattr(row, PLAN_DELIV_DATE_COL)
			plan_ship = getattr(row, PLAN_SHIP_DATE_COL)
			ship_id = getattr(row, const.SHIP_ID_COL)
			src_city = getattr(row, SRC_CITY_COL)
			src_name = getattr(row, const.SRC_COL)
			src_state = getattr(row, SRC_STATE_COL)
			tot_cost = getattr(row, TOT_COST_COL)
			tot_dist = getattr(row, const.TOT_DIST_COL)
			weight = getattr(row, WT_COL)
			stopnumber = getattr(row, STOP_NUM_COL)

			planned_delivery_arrive = getattr(row, PLANNED_DELIVERY_ARRIVE)
			planned_delivery_depart = getattr(row, PLANNED_DELIVERY_DEPART)
			ship_arrive = getattr(row, SHIP_ARRIVE)
			ship_depart = getattr(row, SHIP_DEPART)
			planned_ship_arrive = getattr(row, PLANNED_SHIP_ARRIVE)
			planned_ship_depart = getattr(row, PLANNED_SHIP_DEPART)
			planned_pickup_depart = getattr(row, PLANNED_PICKUP_DEPART)
			ship_destcode = getattr(row, SHIP_DESTCODE)
			ship_destname = getattr(row, SHIP_DESTNAME)
			ship_destcity = getattr(row, SHIP_DESTCITY)
			ship_deststate = getattr(row, SHIP_DESTSTATE)
			ship_destzip = getattr(row, SHIP_DESTZIP)
			ship_destcountry = getattr(row, SHIP_DESTCOUNTRY)
			ship_destlat = getattr(row, SHIP_DESTLAT)
			ship_destlon = getattr(row, SHIP_DESTLON)

			carrier_type = util.carrier_type(carrier)
			
			dest_city = dest_city.title()
			dest_name = dest_name.title()
			equip = equip.title()
			ord_type = ord_type.split('_')[0].title()
			product = util.remove_underscore(product, ': ').title()
			src_name = src_name.title()
			src_city = src_city.title()
			weight = util.convert_to_float(weight)

			dest_city_state = f'{dest_city}, {dest_state}'
			src_city_state = f'{src_city}, {src_state}'

			plan_ship = util.convert_to_datetime(plan_ship)
			plan_deliv = util.convert_to_datetime(plan_deliv)
			pickup_arrive = util.convert_to_datetime(pickup_arrive)
			delivery_arrive = util.convert_to_datetime(delivery_arrive)
			delivery_depart = util.convert_to_datetime(delivery_depart)
			pickup_depart = util.convert_to_datetime(pickup_depart)

			planned_delivery_arrive = util.convert_to_datetime(planned_delivery_arrive)
			planned_delivery_depart = util.convert_to_datetime(planned_delivery_depart)
			ship_arrive = util.convert_to_datetime(ship_arrive)
			ship_depart = util.convert_to_datetime(ship_depart)
			planned_ship_arrive = util.convert_to_datetime(planned_ship_arrive)
			planned_ship_depart = util.convert_to_datetime(planned_ship_depart)
			planned_pickup_depart = util.convert_to_datetime(planned_pickup_depart)

			fuel = util.convert_to_float(fuel)
			line_haul = util.convert_to_float(line_haul)
			tot_cost = util.convert_to_float(tot_cost)
			tot_dist = util.convert_to_float(tot_dist)

			otp = util.on_time(plan_ship, pickup_arrive)
			otd = util.on_time(plan_deliv, delivery_arrive)

			plan_ship_wk = plan_ship - timedelta(days=plan_ship.weekday())

			shipped = 'Y' if isinstance(pickup_arrive, datetime) else 'N'

			key = (ship_id, dest_id)

			miles = self.miles_by_ship_dest[key]

			alloc_factor = miles * weight

			ship_factor = self.alloc_factor_by_ship[ship_id]

			alloc_mult = alloc_factor / ship_factor if ship_factor else 0

			if (carrier_type == '3PL' and is_spot_cost == 'Y') or not fuel:
				fuel = tot_dist * const.FUEL_COST
				line_haul -= fuel
			
			alloc_fuel = alloc_mult * fuel if fuel else None
			alloc_linehaul_cost = alloc_mult * line_haul if line_haul else None
			alloc_tot_cost = alloc_mult * tot_cost if tot_cost else None
			
			rows.append([
				self.name,
				export_date,
				shipped,
				getattr(row, const.TENDER_STAT_COL),
				getattr(row, CANCEL_STATUS_COL),
				ord_type,
				getattr(row, MODE_COL),
				equip,
				carrier,
				carrier_type,
				getattr(row, BUS_UNIT_COL),
				getattr(row, INS_DATE_COL),
				getattr(row, GL_CODE_COL),
				ship_id,
				getattr(row, ORD_ID_COL),
				getattr(row, ORD_LINE_ID_COL),
				getattr(row, PROD_GRP_COL),
				product,
				is_spot_cost,
				getattr(row, const.DRIVER_ID_COL),
				getattr(row, START_TIME_COL),
				getattr(row, END_TIME_COL),
				plan_ship_wk,
				plan_ship,
				pickup_arrive,
				otp,
				plan_deliv,
				delivery_arrive,
				otd,
				getattr(row, const.SRC_WHSE_ID_COL),
				src_name,
				src_city,
				src_state,
				src_city_state,
				getattr(row, SRC_COUNTRY_COL),
				getattr(row, SRC_ZIP_COL),
				getattr(row, SRC_LAT_COL), 
				getattr(row, SRC_LON_COL),
				dest_id,
				dest_name,
				dest_city,
				dest_state,
				dest_city_state,
				getattr(row, DEST_COUNTRY_COL),
				getattr(row, DEST_ZIP_COL),
				getattr(row, DEST_LAT_COL),
				getattr(row, DEST_LON_COL),
				getattr(row, INTL_FLAG_COL),
				weight,
				getattr(row, const.WT_UTIL_COL),
				getattr(row, WT_UOM_COL),
				self.miles_by_ship_dest[key],
				getattr(row, const.UNLOAD_DIST_COL),
				getattr(row, const.LOAD_DIST_COL),
				tot_dist,
				getattr(row, ACCS_COL),
				fuel,
				line_haul,
				getattr(row, const.ACCEPT_TNDR_COST_COL),
				tot_cost,
				getattr(row, const.SHIP_GL_COST),
				alloc_fuel,
				alloc_linehaul_cost,
				alloc_tot_cost,
				self.ship_stop_count[ship_id],
				#this is assuming I add the columns at the end of the table
				delivery_depart,
				pickup_depart,
				stopnumber,
				planned_delivery_arrive,
				planned_delivery_depart,
				ship_arrive,
				ship_depart,
				planned_ship_arrive,
				planned_ship_depart,
				planned_pickup_depart,
				ship_destcode,
				ship_destname,
				ship_destcity,
				ship_deststate,
				ship_destzip,
				ship_destcountry,
				ship_destlat,
				ship_destlon
				])
			
		return rows