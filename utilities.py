from datetime import datetime
import pandas as pd
import sqlite3 as sql

import constants as const


def execute_select(query, args=(), fetchall=True):
		with sql.connect(
			const.DB_PATH, uri=True, detect_types=sql.PARSE_DECLTYPES
			) as con:
			results = con.execute(query, args)
			
		return results.fetchall() if fetchall else results.fetchone()


def carrier_type(carrier):
	if 'FLEET' in carrier:
		carrier_type = 'Fleet'
	elif 'CPU' in carrier:
		carrier_type = carrier
	else:
		carrier_type = '3PL'
	return carrier_type


def clean_column_names(names, remove_strs=[], replace_with=''):
	if not remove_strs:
		remove_strs = [' ', '-', ':', '.', '(', ')']

	clean_names = []

	for name in names: 
		for remove_str in remove_strs:
			name = name.replace(remove_str, '')
		clean_names.append(name)
	
	return clean_names


def convert_to_datetime(value):
	'''
		Returns the same value if it's already a datetime, which will 
		be true if coming from an xlsx file, or if it's an emplty string.
		Otherwise it will convert the string datetime to a datetime object.
	'''
	return (
		value if isinstance(value, datetime) or not value 
		else pd.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
		)


def convert_to_float(value):
		return float(value) if value else 0


def on_time(plan, actual):
	'''
		Returns "Y" if the actual date is before or the same as the plan
		date and "N" if otherwise, but only if both arguments are datetime 
		objects.
		
		Args:
			plan: datetime
			actual: datetime
	'''
	if isinstance(plan, datetime) and isinstance(actual, datetime):
		return 'Y' if actual.date() <= plan.date() else 'N'


def remove_dgi(value):
		return value.replace('DGI.', '') if value else ''


def remove_underscore(value, replace_with=' '):
	'''
		Replaces all underscores in the string value with an empty string
		unless a replace string is specified.
	'''
	return value.replace('_', replace_with) if value else ''