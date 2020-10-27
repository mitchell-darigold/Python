from collections import defaultdict
from datetime import datetime, timedelta
from model import Model

import constants as const
import utilities as util


REPORT_NAME = 'Stop Level Report'

ACCS_COL = 'Accessorials'
ACTUAL_ARRIVE_COL = 'ActualArrival'
ACTUAL_DEPART_COL = 'ActualDeparture'
BUS_UNIT_COL = 'BusinessDivision'
DEST_CITY_COL = 'City'
DEST_COL = 'LocationName'
DEST_ID = 'LocationID'
DEST_STATE_COL = 'ProvinceCode'
DEST_ZIP_COL = 'PostalCode'
DIST_FROM_PREV_COL = 'DistanceFromPreviousStop'
END_TIME_COL = 'EndTime' 
GROSS_WT_COL = 'GrossWeight'
IS_SPOT_COST_COL = 'SpotCosted'
ORD_TYPE_COL = 'OrderType'
MODE_COL = 'TransportMode'
NET_WT_COL = 'NetWeight'
ORD_IDS_COL = 'SOS'
PLAN_ARRIVE_COL = 'PlannedArrival'
PLAN_DEPART_COL = 'PlannedDeparture'
SHIP_UNIT_CNT_COL = 'ShipUnitCount'
SRC_CITY_COL = 'SourceLocationCity'
SRC_STATE_COL = 'SourceLocationState'
SRC_ZIP_COL = 'SourceLocationZip'
START_TIME_COL = 'StartTime' 
STOP_NUM_COL = 'StopNum'
STOP_TYPE_COL = 'StopType'
TOT_COST_COL = 'TotalActualCost'
TRACTOR_ID_COL = 'TractorId'

PLAN_TO_ROW = 1
HEADER_ROW = 2
FIRST_DATA_ROW = 3


class StopLevel:
	'''
	'''


	def __init__(self, df, name):
		self.df = df
		self.name = name


	def main(self):
		rows = []

		export_date = self.df.at[const.EXPORT_DATE_ROW, REPORT_NAME]

		plan_to = util.convert_to_datetime(
			self.df.at[PLAN_TO_ROW, REPORT_NAME]
			)

		column_names = self.df.iloc[[HEADER_ROW]].values[0]
		self.df.columns = util.clean_column_names(column_names)
		
		# drops the rows before the data starts
		self.df.drop([i for i in range(FIRST_DATA_ROW)], inplace=True)

		stop_nums_by_ship = defaultdict(list)

		actual_arrivals = []
		actual_departures = []
		driver_ids = []
		ship_ids = []
		stop_nums = []
		
		for row in self.df.itertuples(index=False):
			actual_arrive = getattr(row, ACTUAL_ARRIVE_COL)
			actual_depart = getattr(row, ACTUAL_DEPART_COL)
			driver_id = getattr(row, const.DRIVER_ID_COL)
			ship_id = getattr(row, const.SHIP_ID_COL)
			stop_num = getattr(row, STOP_NUM_COL)

			actual_arrive = util.convert_to_datetime(actual_arrive)
			actual_depart = util.convert_to_datetime(actual_depart)
			driver_id = util.remove_dgi(driver_id)
			ship_id = util.remove_dgi(ship_id)
			stop_num = int(stop_num)

			actual_arrivals.append(actual_arrive)
			actual_departures.append(actual_depart)
			driver_ids.append(driver_id)
			ship_ids.append(ship_id)
			stop_nums.append(stop_num)

			stop_nums_by_ship[ship_id].append(stop_num)
		
		for i, row in enumerate(self.df.itertuples(index=False)):
			accept_cost = getattr(row, const.ACCEPT_TNDR_COST_COL)
			accs_cost = getattr(row, ACCS_COL)
			appt_deliv = getattr(row, const.APPT_DELIV_COL)
			appt_pickup = getattr(row, const.APPT_PICKUP_COL)
			appt_end = getattr(row, const.APPT_END_COL)
			appt_start = getattr(row, const.APPT_START_COL)
			carrier = getattr(row, const.SERV_PROV_COL)
			dest_name = getattr(row, DEST_COL)
			dest_id = getattr(row, DEST_ID)
			dest_city = getattr(row, DEST_CITY_COL)
			dest_state = getattr(row, DEST_STATE_COL)
			dest_zip = getattr(row, DEST_ZIP_COL)
			dist_from_prev = getattr(row, DIST_FROM_PREV_COL)
			end_time = getattr(row, END_TIME_COL)
			eqp_grp = getattr(row, const.EQP_COL)
			fuel_cost = getattr(row, const.FUEL_COL)
			gross_wt = getattr(row, GROSS_WT_COL)
			is_spot_costed = getattr(row, IS_SPOT_COST_COL)
			line_haul = getattr(row, const.LN_HAUL_COL)
			load_dist = getattr(row, const.LOAD_DIST_COL)
			mode = getattr(row, MODE_COL)
			net_wt = getattr(row, NET_WT_COL)
			ord_ids = getattr(row, ORD_IDS_COL)
			plan_arrive = getattr(row, PLAN_ARRIVE_COL)
			plan_depart = getattr(row, PLAN_DEPART_COL)
			ship_gl_cost = getattr(row, const.SHIP_GL_COST)
			ship_id = getattr(row, const.SHIP_ID_COL)
			ship_unit_cnt = getattr(row, SHIP_UNIT_CNT_COL)
			src_city = getattr(row, SRC_CITY_COL)
			src_state = getattr(row, SRC_STATE_COL)
			src_id = getattr(row, const.SRC_WHSE_ID_COL)
			src_name = getattr(row, const.SRC_COL)
			src_zip = getattr(row, SRC_ZIP_COL)
			start_time = getattr(row, START_TIME_COL)
			stop_type = getattr(row, STOP_TYPE_COL)
			tender_status = getattr(row, const.TENDER_STAT_COL)
			tot_cost = getattr(row, TOT_COST_COL)
			tot_dist = getattr(row, const.TOT_DIST_COL)
			unload_dist = getattr(row, const.UNLOAD_DIST_COL)
			wt_util = getattr(row, const.WT_UTIL_COL)

			carrier = util.remove_underscore(util.remove_dgi(carrier))
			dest_city = dest_city.title()
			dest_name = dest_name.title()
			src_name = src_name.title()
			src_city = src_city.title()

			bus_unit = self.business_unit(row)
			carrier_type = util.carrier_type(carrier)
			dest_city_state = f'{dest_city}, {dest_state}'
			dest_id = util.remove_dgi(dest_id)
			driver_name = self.driver_full_name(row)
			eqp_grp = util.remove_dgi(eqp_grp).title()
			line_haul = self.convert_to_float(line_haul)
			mode = util.remove_dgi(mode)
			net_wt = self.convert_to_float(net_wt)
			ord_type = self.order_type(row)
			plan_arrive = util.convert_to_datetime(plan_arrive)
			plan_depart = util.convert_to_datetime(plan_depart)
			start_time = util.convert_to_datetime(start_time)
			src_city_state = f'{src_city}, {src_state}'
			src_id = util.remove_dgi(src_id)
			tot_dist = self.convert_to_float(tot_dist)

			if ord_ids == 'NIL':
				ord_ids = ''

			src_is_plant = 1 if 'Plant' in src_name else 0

			actual_arrive = actual_arrivals[i]
			actual_depart = actual_departures[i]
			driver_id = driver_ids[i]
			stop_num = stop_nums[i]
			ship_id = ship_ids[i]

			ship_stop_nums = stop_nums_by_ship[ship_id]
			ship_stop_count = len(ship_stop_nums)
			is_multi_stop = 1 if ship_stop_count > 2 else 0
			is_last_stop = 1 if stop_num == max(ship_stop_nums) else 0

			otp = util.on_time(plan_depart, actual_depart) if stop_type == 'P' else None
			otd = util.on_time(plan_arrive, actual_arrive) if stop_type == 'D' else None
			
			if (carrier_type == '3PL' and is_spot_costed == 'Y') or fuel_cost == '':
				fuel_cost = tot_dist * .3
				line_haul -= fuel_cost

			# if isinstance(start_time, datetime):
			# 	start_date = start_time.replace(hour=0, minute=0, second=0)
			# else:
			# 	start_date = ''
			start_date = start_time.replace(hour=0, minute=0, second=0)
			
			lane = f'{src_city_state} - {dest_city_state} : {mode} - {eqp_grp}'
			
			rows.append([
				self.name,
				export_date,
				plan_to,
				tender_status,
				ord_type,
				mode,
				eqp_grp,
				carrier,
				carrier_type, 
				bus_unit,
				ship_id,
				ord_ids,
				is_multi_stop,
				ship_stop_count,
				is_last_stop,
				stop_num,
				stop_type,
				is_spot_costed,
				driver_id,
				driver_name,
				appt_start,
				appt_end,
				start_date,
				start_time,
				end_time,
				appt_pickup,
				appt_deliv,
				plan_arrive,
				plan_depart,
				actual_arrive,
				actual_depart,
				otp,
				otd,
				src_id,
				src_name,
				src_city,
				src_state,
				src_city_state,
				src_zip,
				src_is_plant,
				dest_id,
				dest_name,
				dest_city,
				dest_state,
				dest_city_state,
				dest_zip,
				lane,
				ship_unit_cnt,
				gross_wt,
				net_wt,
				wt_util,
				dist_from_prev,
				unload_dist,
				load_dist,
				tot_dist,
				accs_cost,
				fuel_cost,
				line_haul,
				accept_cost,
				tot_cost,
				ship_gl_cost
				])
		
		return rows


	def convert_to_float(self, value):
		return float(value) if value else 0


	def driver_full_name(self, row):
		first_name = getattr(row, const.DRIVER_FNAME_COL).title()
		last_name = getattr(row, const.DRIVER_LNAME_COL).title()
		return f'{first_name}, {last_name}' if first_name and last_name else ''


	def business_unit(self, row):
		'''
			Returns the first occurrence of the business division, either 
			CP or ID. Raw data contains multiple instances separated by a ";".
		'''
		bus_unit = getattr(row, BUS_UNIT_COL)
		return bus_unit[:2] if isinstance(bus_unit, str) else ''


	def order_type(self, row):
		ord_type = getattr(row, ORD_TYPE_COL)
		if isinstance(ord_type, str):
			if 'TRANSFER' in ord_type:
				ord_type = 'Transfer'
			elif 'PURCHASE' in ord_type:
				ord_type = 'Purchase'
			else:
				ord_type = 'Sales'
		else:
			ord_type = ''
		return ord_type




