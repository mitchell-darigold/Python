import math
import pandas as pd

import utilities as util

# names of input columns after removing special chars
KEY_COL = 'IDorOptionalfield'
MILES_COL = 'PCMilerPracticalMileage'
SRC_CITY_COL = 'OrigCity'
SRC_STATE_COL = 'OrigState'

# partial column names for spot and contract avg linehaul
# the other part will consist of month and year in format "mmm yyyy"
# and will change depending on timeframe of the file
CONT_COL = 'ContractAvgLinehaul'
SPOT_COL = 'SpotAvgLinehaul'


class Dat:
	'''
	'''


	def __init__(self, df, name):
		self.df = df
		self.name = name

		self.clean_input_column_names()
		self.set_linehaul_col_inds()
		self.set_periods()


	def main(self):
		rows = []

		lanes = set()

		keys = self.fetch_current_keys()
		
		for row in self.df.itertuples(index=False):
			print(row)
			key = getattr(row, KEY_COL)
			miles = getattr(row, MILES_COL)

			src_city, src_state, dest_city, dest_state, equip = key.split(',')

			if equip == 'van':
				equip = 'Dryvan'

			mode = 'TL'

			lane = f'{src_city}, {src_state} - {dest_city}, {dest_state} : {mode} - {equip}'

			if lane not in lanes:
				lanes.add(lane)
				
				cont_avgs = row[self.fst_in_cont_col : self.lst_in_cont_col]
				spot_avgs = row[self.fst_in_spot_col : self.lst_in_spot_col]

				for cont, spot, period in zip(cont_avgs, spot_avgs, self.period_cols):
					year = period[0]
					month = period[1]

					key = f'{lane}{year}{month}'

					if key not in keys:
						spot_adj = spot * 1.2 if spot else ''

						rows.append([
							self.name,
							key,
							lane,
							year, 
							month,
							miles,
							cont,
							spot,
							spot_adj
							])
		
		return rows


	def fetch_current_keys(self):
		query = '''
			SELECT Id
			FROM Dat
			'''

		results = util.execute_select(query)
		
		return {x[0] for x in results}


	# todo maybe put this in the model class and pass the model to this class
	def clean_input_column_names(self):
		remove_strs = [' ', '-', ':', '(', ')']

		old_cols = list(self.df)
		new_cols = []

		for col in old_cols: 
			for remove_str in remove_strs:
				col = col.replace(remove_str, '')
			new_cols.append(col)
		
		self.df.columns = new_cols


	def set_linehaul_col_inds(self):
		'''
			Sets the first and last column indexes of the spot and 
			contract average linehaul columns
		'''
		self.fst_in_cont_col = None
		self.fst_in_spot_col = None
		self.lst_in_spot_col = None
		self.lst_in_cont_col = None

		# flags that indicate the iteration is currently going through 
		# either the contract of spot cols
		checking_cont_cols = False
		checking_spot_cols = False

		cols = list(self.df)

		for i, c in enumerate(cols):
			is_cont_col = CONT_COL in c
			is_spot_col = SPOT_COL in c

			# if the flag for contract columns is still on, but the current
			# column is no longer a contract column then set the last index
			# to the current since last index is non inclusive
			if checking_cont_cols:
				if not is_cont_col:
					self.lst_in_cont_col = i
					checking_cont_cols = False

			if checking_spot_cols:
				if not is_spot_col:
					self.lst_in_spot_col = i
					checking_spot_cols = False

			# if the first contract column has not been set the current 
			# column is a contract column then set the first index to 
			# the current one and turn on the flag to indicate currently 
			# iterating through the contract columns
			if self.fst_in_cont_col is None:
				if is_cont_col:
					self.fst_in_cont_col = i
					checking_cont_cols = True

			if self.fst_in_spot_col is None:
				if is_spot_col:
					self.fst_in_spot_col = i
					checking_spot_cols = True

			# if both last contract and spot column indexes have been set
			# then stop the iteration
			if self.lst_in_cont_col is not None and self.lst_in_spot_col is not None:
				break

		# if the last contract column index still has not been set then
		# set it to the index of the first in case there is only one column
		if self.lst_in_cont_col is None:
			self.lst_in_cont_col = self.fst_in_spot_col

		if self.lst_in_spot_col is None:
			self.lst_in_spot_col = self.fst_in_spot_col


	def set_periods(self):
		self.period_cols = []

		cont_cols = list(self.df)[self.fst_in_cont_col : self.lst_in_cont_col]
		
		for col in cont_cols:
			year = col[3 : 7]
			month = col[:3]

			self.period_cols.append((year, month))