from collections import defaultdict
from contextlib import suppress
from datetime import datetime, timedelta
import getpass
import os
import pandas as pd
from pathlib import Path
import re
import sqlite3 as sql
import time

import constants as const
from xlsxtocsv import XlsxToCsv


class Model:
	'''
	'''


	def __init__(self):
		self.tbl_name = ''

		self.col_names = []
		self.tbl_names = []

		self.data_dir = Path(const.DATA_DIR)

		self.ol_path = self.data_dir.joinpath(const.ORDER_LEVEL)
		self.sl_path = self.data_dir.joinpath(const.STOP_LEVEL)

		# default database path
		self.db_path = self.data_dir.joinpath(const.DB_NAME)

		# pattern to match dates with format ####-##-##
		self.date_format_pattern = re.compile(r'\d{4}-\d{2}-\d{2}')

		self.today = datetime.now()

		self.sample_date_format = self.today.strftime('%Y-%m-%d')
		

	def execute_select(self, query, args=(), fetchall=True):
		with sql.connect(
			self.db_path, uri=True, detect_types=sql.PARSE_DECLTYPES
			) as con:
			results = con.execute(query, args)
			
		return results.fetchall() if fetchall else results.fetchone()


	def execute_many(self, query, values):
		with sql.connect(self.db_path, detect_types=sql.PARSE_DECLTYPES) as con:
			con.executemany(query, values)


	def execute_sql(self, query, args=()):
		with sql.connect(self.db_path, detect_types=sql.PARSE_DECLTYPES) as con:
			con.execute(query, args)


	def fetch_table_names(self):
		query = '''
			SELECT name 
			FROM sqlite_master
			WHERE type = ?
			'''
		return self.execute_select(query, args=('table', ))


	def set_table_names(self):
		self.tbl_names = [
			x[0] for x in sorted(self.fetch_table_names())
			if x[0] in const.FILE_TABLES
			]


	def fetch_file_names(self):
		query = f'''
			SELECT DISTINCT {const.FILE_NAME_COL}
			FROM {self.tbl_name}
			'''
		
		return self.execute_select(query)


	def fetch_row_count(self):
		query = f'''
			SELECT COUNT(*)
			FROM {self.tbl_name}
			'''

		results = self.execute_select(query, fetchall=False)

		return results[0] if results else 0


	def fetch_table_columns(self, tbl_name=''):
		if tbl_name == '':
			tbl_name = self.tbl_name

		query = f'PRAGMA table_info({tbl_name})'
		table_info = self.execute_select(query)
		return [x[1] for x in table_info]


	def export_from_sql_query(self, query, output_path):
		df = None

		print('running query:\n', query)
		with sql.connect(self.db_path, uri=True, detect_types=sql.PARSE_DECLTYPES) as con:
			df = pd.read_sql(query, con)

		if df is not None:
			print(f'query returned {len(df)} results')
			if const.CSV in output_path:
				df.to_csv(output_path, index=False)
			else:
				df.to_excel(output_path, index=False)
			os.startfile(output_path)


	def xlsx_to_csv(self, input_file, output_file):
		converter = XlsxToCsv(input_file, output_file)
		converter.convert()


	def create_table(self, table, query):
		with sql.connect(self.db_path, detect_types=sql.PARSE_DECLTYPES) as con:
			con.execute(f'DROP TABLE IF EXISTS {table}')
			con.execute(query)


	def create_index(self, index, query):
		self.execute_sql(query)


	def table_name_from_query(self, query):
		return query.split('"')[1].split('"')[0]


	def index_name_from_query(self, query):
		return query.split('CREATE INDEX')[1].split('ON')[0].strip()


	def is_csv(self, path):
		return Path(path).suffix == const.CSV


	def insert_many_string(self):
		col_string = ','.join(self.col_names)
		param_string = ','.join(['?' for _ in range(len(self.col_names))])
		return f'INSERT OR REPLACE INTO {self.tbl_name} ({col_string}) VALUES ({param_string})'


	def process_emp_time_detail_rows(self, df, name):
		rows = []
		
		df.columns = [c.replace(' ', '') for c in list(df)]

		# dictionary containing otm ids and their associated kronos id
		ids = self.fetch_driver_id_cross_ref()
		
		for row in df.itertuples(index=False):
			apply_date = getattr(row, const.EMP_DATE_COL)
			first_name = getattr(row, const.EMP_FNAME_COL)
			hours = getattr(row, const.EMP_HRS_COL)
			last_name = getattr(row, const.EMP_LNAME_COL)
			paycode = getattr(row, const.EMP_PAYCODE_COL)
			punch_in = getattr(row, const.EMP_PUNCH_IN_COL)
			punch_out = getattr(row, const.EMP_PUNCH_OUT_COL)
			whse_code = getattr(row, const.EMP_WHSE_CODE_COL)

			kronos_id = int(getattr(row, const.EMP_ID_COL))
			
			otm_id = ids[kronos_id] if kronos_id in ids else ''
			
			full_name = f'{first_name}, {last_name}'

			rows.append([
				name,
				whse_code,
				otm_id,
				kronos_id,
				full_name,
				first_name, 
				last_name,
				apply_date,
				punch_in,
				punch_out,
				paycode,
				hours
				])
		
		return rows


	def fetch_driver_id_cross_ref(self):
		query = f'''
			SELECT KronosId, OtmId 
			FROM {const.DRIVER_LIST}
			'''

		results = self.execute_select(query)

		return {int(kid): oid for kid, oid in results if kid}


	def fetch_reason_codes(self):
		query = f'''
			SELECT *
			FROM {const.REASON_CODES_TABLE}
			'''

		results = self.execute_select(query)

		return results


	def fetch_reason_code_descriptions(self):
		query = f'''
			SELECT ReasonCodeDescription
			FROM {const.REASON_CODES_TABLE}
			'''

		results = self.execute_select(query)

		return [x[0] for x in results]


	def insert_reason_code(self, reason_code):
		query = f'''
			INSERT INTO {const.REASON_CODES_TABLE}(ReasonCodeDescription, UpdateUser, UpdateDate)
			VALUES (?, ?, ?)
			'''

		user = getpass.getuser()
		timestamp = datetime.now()

		self.execute_sql(query, (reason_code, user, timestamp))


	def delete_reason_code(self, reason_code_id):
		query = f'''
			DELETE
			FROM {const.REASON_CODES_TABLE}
			WHERE ReasonCodeId = ?
			'''

		self.execute_sql(query, args=(reason_code_id, ))


	def insert_or_replace_late_order(self, order_release_id, reason_code_description, comments):
		reason_code_id = self._fetch_reason_code_id(reason_code_description)

		if reason_code_id:
			query = f'''
				INSERT OR REPLACE INTO {const.LATE_ORDERS_TABLE}(
					OrderReleaseID, 
					ReasonCodeID, 
					Comments, 
					UpdateUser, 
					UpdateDate
					)
				VALUES (?, ?, ?, ?, ?)
				'''

			user = getpass.getuser()
			timestamp = datetime.now()
			
			self.execute_sql(
				query, 
				args=(order_release_id, reason_code_id, comments, user, timestamp)
				)

	def _fetch_reason_code_id(self, reason_code_description):
		query = f'''
			SELECT ReasonCodeID
			FROM {const.REASON_CODES_TABLE}
			WHERE ReasonCodeDescription = ?
			'''

		results = self.execute_select(query, args=(reason_code_description, ), fetchall=False)

		if results:
			return int(results[0])


	def fetch_late_order(self, order_release_id):
		query = f'''
			SELECT 
				r.ReasonCodeDescription,
				l.Comments,
				l.UpdateUser,
				l.UpdateDate
			FROM {const.LATE_ORDERS_TABLE} l, {const.REASON_CODES_TABLE} r
			WHERE l.ReasonCodeId = r.ReasonCodeId
				AND l.OrderReleaseId = ?
			'''

		results = self.execute_select(query, args=(order_release_id, ), fetchall=False)

		return results


	def delete_later_order(self, order_release_id):
		query = f'''
			DELETE
			FROM {const.LATE_ORDERS_TABLE}
			WHERE OrderReleaseId = ?
			'''

		self.execute_sql(query , args=(order_release_id, ))


	def get_prior_week_date_range(self):
		'''
			Returns the beginning and end dates of the prior week as 
			formatted strings YYYY-mm-dd.
		'''
		# same day last week as today
		last_wk = self.today - timedelta(days=7)

		start = last_wk - timedelta(days=last_wk.weekday())
		end = start + timedelta(days=6)

		str_format = '%Y-%m-%d'

		return (start.strftime(str_format), end.strftime(str_format))


	def is_valid_date_format(self, date_str):
		result = re.match(self.date_format_pattern, date_str)

		return result


	def export_late_or_missing_date_orders(self, saveas_name, from_dt, to_dt, is_shipped, division, order_type):
		query = f'''
			SELECT
				OrderId,
				ShipmentId,
				SUBSTR(StartTime, 0, 11) StartDate,
				PlanShipDate,
				ActualShipDate,
				OnTimePickUp,
				PlanDelivDate,
				ActualDelivDate,
				OnTimeDeliv,
				Product,
				SrcName,
				SrcCityState,
				DestName, 
				DestCityState,
				Mode,
				CarrierType,
				Carrier
			FROM {const.ORDER_LEVEL}
			WHERE BusUnit = ?
				AND OrderType = ?
				AND StartTime > ?
				AND StartTime < ?
				AND (ActualDelivDate = "" OR ActualDelivDate > PlanDelivDate)
			'''

		args = [division, order_type, from_dt, to_dt]

		if is_shipped:
			query += f'AND ActualShipDate <> ?'

			args.append("")
		print('running query:')
		print(query)
		print('with arguments:', args)
		print('this may take a few minutes...')
		results = self.execute_select(query, args)

		df = pd.DataFrame(
			results,
			columns=[
				'Order',
				'Shipment',
				'Shipment Start Date',
				'Planned Ship Date',
				'Actual Ship Date',
				'On-Time Pickup',
				'Planned Delivery Date',
				'Actual Delivery Date',
				'On-Time Delivery',
				'Product',
				'Source Name',
				'Source City',
				'Customer',
				'Customer City',
				'Mode',
				'Carrier Type',
				'Carrier'
				]
			)
		print(f'{len(df):} records returned. Saving to: {saveas_name}')
		df.to_csv(saveas_name, index=False)

		os.startfile(saveas_name)


	def update_table(self, df, update_cols, by_cols, table_name):
		print('\nupdating', update_cols)
		print('by', by_cols)

		update_query = self._update_query(update_cols, by_cols, table_name)

		print('\nSQL: ' + update_query)

		values = df[update_cols + by_cols].values.tolist()
		
		self.execute_many(update_query, values)


	def _update_query(self, update_cols, by_cols, table_name):
		query = f'UPDATE {table_name} SET '

		for update_col in update_cols:
			query += update_col + ' = ?, '

		query = query[:-2] + ' WHERE '

		for by_col in by_cols:
			query += by_col + ' = ? AND '

		query = query[:-4]

		return query

	