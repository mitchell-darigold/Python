import ntpath
import pandas as pd
from pathlib import Path

import constants as const


class XlsxToCsv:
	def __init__(self, in_paths, out_dir):
		self.in_paths = [Path(path) for path in in_paths]
		self.out_dir = Path(out_dir)


	def convert(self):
		for path in self.in_paths:
			updated_name = self.update_file_name(path)
			out_path = self.out_dir.joinpath(updated_name)

			df = pd.read_excel(path)
			self.xlsx_to_csv(df, out_path)


	def update_file_name(self, path_obj):
		'''
			Returns a string of the path with .xlsx replaced with .csv
		'''
		name = ntpath.basename(path_obj)
		return name.replace(path_obj.suffix, const.CSV)


	def xlsx_to_csv(self, df, out_path):
		if out_path.is_file():
			out_path.unlink()

		df.to_csv(out_path, sep=const.CSV_SEP, index=False)