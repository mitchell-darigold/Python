from datetime import datetime, timedelta
import pandas as pd
import sqlite3 as sql

import constants as const


CUST_DWELL_TYPE = 'CUST'
EOD_DWELL_TYPE = 'EOD'
SOD_DWELL_TYPE = 'SOD'

PLANT_DWELL_TYPES = [SOD_DWELL_TYPE, EOD_DWELL_TYPE]


class DwellTime:
	'''
	'''


	def __init__(self):
		self.con = None

		# dwell time dataframe
		self.dtime_df = None

		# employee time detail dataframe
		self.emptd_df = None

		# stop level dataframe
		self.sl_df = None

		self.dtime_df_cols = []

		self.blank_emp_vals = []
		self.blank_sl_vals = []

		self.apply_date_ind = None
		self.plant_ind = None
		self.driver_ind = None


	def main(self):
		self.con = sql.connect(
			const.DB_PATH, detect_types=sql.PARSE_DECLTYPES
			)

		self.set_emp_time_detail()

		if self.emptd_df is not None:
			self.set_blank_emp_time_detail_vals()
			self.remove_duplicate_overtime_punches()
			self.set_stop_level()

			if self.sl_df is not None:
				self.set_blank_stop_level_values()
				self.set_dwell_time_df_cols()
				self.set_apply_date_index()
				self.set_plant_name_index()
				self.set_driver_name_index()
				self.set_dwell_time_df()
				self.add_customer_dwell()
				
				self.dtime_df['ApplyDate'] = self.dtime_df['ApplyDate'].astype(str)
				self.dtime_df['PunchIn'] = self.dtime_df['PunchIn'].astype(str)
				self.dtime_df['PunchOut'] = self.dtime_df['PunchOut'].astype(str)

				self.dtime_df.to_sql('DwellTime', self.con, if_exists='replace')
		self.con.close()


	def set_emp_time_detail(self):
		query = f'''
			SELECT 
				WhseCode,
				Name PlantName, 
				OtmId, 
				DriverId KronosId,
				FullName DriverName, 
				ApplyDate,
				PunchIn,
				PunchOut,
				Paycode

			FROM 
				{const.EMP_TIME_DETAIL} e,
				{const.PLANTS} p

			WHERE
				e.WhseCode = p.Id
			'''
		self.emptd_df = pd.read_sql(query, self.con)


	def set_blank_emp_time_detail_vals(self):
		self.blank_emp_vals = [None] * len(list(self.emptd_df))


	def remove_duplicate_overtime_punches(self):
		'''
			Creates a new dataframe without duplicate punches for 
			paycode OT1 where one already exists for paycode REG
		'''
		# 2-tuples with otm ID and apply date for punches with "REG" paycode
		reg_dates = set()
		for row in self.emptd_df.itertuples(index=False):
			pay_code = getattr(row, 'Paycode')
			if pay_code == 'REG':
				apply_date = getattr(row, 'ApplyDate')
				otm_id = getattr(row, 'OtmId') 

				reg_dates.add((otm_id, apply_date))
		
		# rows without duplicate punches for "OT1" paycodes
		rows = []
		for row in self.emptd_df.itertuples(index=False):
			pay_code = getattr(row, 'Paycode')

			is_dup = False
			if pay_code == 'OT1':
				otm_id = getattr(row, 'OtmId')
				apply_date = getattr(row, 'ApplyDate')

				is_dup = (otm_id, apply_date) in reg_dates

			if not is_dup:
				rows.append(row)

		self.emptd_df = pd.DataFrame(rows, columns=list(self.emptd_df))


	def set_stop_level(self):
		query = f'''
			SELECT 
				TenderStatus,
				OrderType,
				Mode,
				EqpGrp,
			 	BusUnit,
			 	ShipmentId Shipment,
			 	ShipStopCount,
			 	IsShipLastStop,
			 	StopNum,
			 	StopType,
			 	Carrier,
			 	DriverId,
			 	DriverName SlDriverName,
			 	PlanTo,
			 	SUBSTR(StartTime, 0, 11) StartDate,
			 	ActualDepart,
			 	ActualArrive,
			 	DestName,
			 	DestCity,
			 	DestState,
			 	DestCode,
			 	SrcCode,
			 	SrcName,
			 	SrcCity,
			 	SrcState,
			 	NetWt

			FROM {const.STOP_LEVEL}

			WHERE CarrierType = 'Fleet'
			'''
		self.sl_df = pd.read_sql(query, self.con)


	def set_blank_stop_level_values(self):
		self.blank_sl_vals = [None] * len(list(self.sl_df))


	def set_dwell_time_df_cols(self):
		cols = list(self.emptd_df) + list(self.sl_df)

		cols.extend([
			'DwellTime',
			'DwellType',
			'ExcReason'
			])
		
		self.dtime_df_cols = cols


	def set_apply_date_index(self):
		self.apply_date_ind = self.dtime_df_cols.index('ApplyDate')


	def set_plant_name_index(self):
		self.plant_ind = self.dtime_df_cols.index('PlantName')


	def set_driver_name_index(self):
		self.driver_ind = self.dtime_df_cols.index('DriverName')


	def set_dwell_time_df(self):
		rows = []

		first_stops_by_driver = {}
		last_stops_by_driver = {}

		driver_ids = set()

		for row in self.emptd_df.itertuples(index=False):
			driver_id = getattr(row, 'OtmId')
			p_in = getattr(row, 'PunchIn')
			p_out = getattr(row, 'PunchOut')

			row = list(row)
			
			if driver_id:
				if driver_id not in driver_ids:
					driver_ids.add(driver_id)

					df = self.sl_df.loc[self.sl_df['DriverId'] == driver_id]

					if not df.empty:
						first_stops = df.loc[df['StopNum'] == 1]

						if not first_stops.empty:
							first_stops_by_driver[driver_id] = first_stops

						last_stops = df.loc[df['IsShipLastStop'] == 1]

						if not last_stops.empty:
							last_stops_by_driver[driver_id] = last_stops

				if not pd.isnull(p_in) and not pd.isnull(p_out):
					# 	if driver_id in first_stops_by_driver:
					nxt_day = p_in + timedelta(days=1)
					nxt_day = nxt_day.replace(hour=0, minute=0, second=0)

					fstps = first_stops_by_driver[driver_id]

					day_deps = fstps.loc[
						(fstps['ActualDepart'] > p_in) & (fstps['ActualDepart'] < nxt_day)
						]

					if day_deps.empty:
						exc_reason = 'No Actual Departures for Punch-In day'
					
						self.insert_plant_exc_row(rows, row, SOD_DWELL_TYPE, exc_reason)
					else:
						day_deps.sort_values(by='ActualDepart', inplace=True)

						first_depart = day_deps.iloc[0]
						sl_vals = list(first_depart)
						actual_depart = getattr(first_depart, 'ActualDepart')
						dwell_time = self.dwell_time_min(p_in, actual_depart)

						new_row = row + sl_vals
						new_row.extend([dwell_time, SOD_DWELL_TYPE, None])
						rows.append(new_row)

					p_out_day = p_out.replace(hour=0, minute=0, second=0)

					lstps = last_stops_by_driver[driver_id]

					day_arrs = lstps.loc[
						(lstps['ActualArrive'] > p_out_day) & (lstps['ActualArrive'] < p_out)
						]

					if day_arrs.empty:
						exc_reason = 'No Actual Arrivals for Punch-Out day'
					
						self.insert_plant_exc_row(rows, row, EOD_DWELL_TYPE, exc_reason)
					else:
						day_arrs.sort_values(by='ActualArrive', ascending=True, inplace=True)

						last_arrive = day_arrs.iloc[0]
						sl_vals = list(last_arrive)
						actual_arrive = getattr(last_arrive, 'ActualArrive')
						dwell_time = self.dwell_time_min(actual_arrive, p_out)
						
						new_row = row + sl_vals
						new_row.extend([dwell_time, EOD_DWELL_TYPE, None])
						rows.append(new_row)

		self.dtime_df = pd.DataFrame(rows, columns=self.dtime_df_cols)


	def insert_sod_and_eod_exc_row(self, rows, row, reason):
		for dwell_type in PLANT_DWELL_TYPES:
			self.insert_plant_exc_row(rows, row, dwell_type, reason)


	def insert_plant_exc_row(self, rows, row, dwell_type, reason):
		new_row = row + self.blank_sl_vals

		new_row.extend([
			None,
			dwell_type,
			reason
			])

		rows.append(new_row)


	def dwell_time_min(self, arrive, depart):
		# timedelta
		td = depart - arrive
		days, hrs, mins = td.days, td.seconds // 3600, td.seconds // 60 % 60
		
		# returns minutes
		return days * 1440 + hrs * 60 + mins


	def add_customer_dwell(self):
		rows = []
	
		for row in self.sl_df.loc[self.sl_df['StopType'] == 'D'].itertuples(index=False):
			actual_arrive = getattr(row, 'ActualArrive')
			actual_depart = getattr(row, 'ActualDepart')
			driver = getattr(row, 'SlDriverName')
			start_date = getattr(row, 'StartDate')
			
			plant_name = self.extract_plant_name(row)

			actual_arrive_is_null = pd.isnull(actual_arrive)
			actual_depart_is_null = pd.isnull(actual_depart)

			dwell_time = None

			if actual_arrive_is_null or actual_depart_is_null:
				exc_reason = 'Missing '

				if actual_arrive_is_null and actual_depart_is_null:
					exc_reason += 'Actual Arrive, Actual Depart'
				elif actual_arrive_is_null:
					exc_reason += 'Actual Arrive'
				else:
					exc_reason += 'Actual Depart'
			else:
				if actual_arrive == actual_depart:
					exc_reason = 'Actual Depart same as Actual Arrive'
				else:
					dwell_time = self.dwell_time_min(actual_arrive, actual_depart)
					exc_reason = None
			
			new_row = self.blank_emp_vals + list(row)

			new_row[self.driver_ind] = driver
			new_row[self.apply_date_ind] = start_date
			new_row[self.plant_ind] = plant_name

			new_row.extend([
				dwell_time,
				CUST_DWELL_TYPE,
				exc_reason
				])

			rows.append(new_row)
		
		df = pd.DataFrame(rows, columns=self.dtime_df_cols)
		self.dtime_df = pd.concat([self.dtime_df, df])


	def extract_plant_name(self, row):
		carrier = getattr(row, 'Carrier')
		name = carrier.split()[0]
		return name.title()


if __name__ == '__main__':
	dwell_time = DwellTime()
	dwell_time.main()
