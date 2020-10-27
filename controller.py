import ntpath
import pandas as pd
from pathlib import Path

from cbthread import CbThread
import constants as const
from dat import Dat
from dwelltime import DwellTime
from model import Model
from orderlevel import OrderLevel
from stoplevel import StopLevel
from view import View, InputLateOrderReasonCodesView, ExportLateOrBlankDateOrdersView


class Controller:
	'''
		Passes the user actions from the main window to the model.
	'''


	def __init__(self):
		self.model = Model()
		self.view = View(self)

		self.load_enabled = False
		self.delete_enabled = False
		self.delete_all_enabled = False

		self.input_late_orders_view = None
		self.export_late_or_blank_date_orders_view = None


	def main(self):
		self.view.db_path.set(self.model.db_path)
		self.view.sel_table_var.trace('w', self.on_table_change)
		self.view.mainloop()


	def on_load_new_click(self):
		initialdir = self._initial_data_dir()

		files = self.view.browse_for_files(initialdir)

		if files:
			if any(Path(p).suffix not in const.FILE_TYPES for p in files):
				message = f'File type must be of type {const.FILE_TYPES}.'
				self.view.show_message(message)
			else:
				for file in files:
					name = ntpath.basename(file)

					print('reading............', name)

					if self.model.is_csv(file):
						sep = (
							',' if self.model.tbl_name == const.EMP_TIME_DETAIL 
							else const.CSV_SEP
							)
						df = pd.read_csv(file, sep=sep, low_memory=False)
					else:
						df = pd.read_excel(file)

					if not df.empty:
						df.fillna('', axis=1, inplace=True)
						
						print('processing rows...')
						
						if self.model.tbl_name == const.DAT:
							dat = Dat(df, name)
							new_rows = dat.main()

						elif self.model.tbl_name == const.EMP_TIME_DETAIL:
							new_rows = self.model.process_emp_time_detail_rows(df, name)

						elif self.model.tbl_name == const.ORDER_LEVEL:
							order_level = OrderLevel(df, name)
							new_rows = order_level.main()

						elif self.model.tbl_name == const.STOP_LEVEL:
							stop_level = StopLevel(df, name)
							new_rows = stop_level.main()

						else:
							new_rows = [(name,) + r for r in df.itertuples(index=False)]
						
						print('inserting values..')
						
						insert_query = self.model.insert_many_string()
						
						self.model.execute_many(insert_query, new_rows)

						self.view.insert_file(name)

						self._set_row_count_label()
						self.set_file_frame_text()

						if self.model.tbl_name == const.STOP_LEVEL:
							dwell_time = DwellTime()
							dwell_time.main()

						print('finished!\n')

				self.view.show_message('Finished loading all files!')


	def _initial_data_dir(self):
		initialdir = Path(const.DATA_DIR)
		if initialdir.joinpath(self.model.tbl_name).is_dir():
			initialdir = initialdir.joinpath(self.model.tbl_name)
		if initialdir.joinpath('csv').is_dir():
			initialdir = initialdir.joinpath('csv')
		return initialdir


	def on_table_combobox_click(self):
		'''
			Post command method for the table drop down.
		'''
		self.model.set_table_names()
		self.view.tbl_cbo.config(values=self.model.tbl_names)


	def _update_progress(self, message, current_count, total_count):
		'''
			Updates the progress label on the GUI with the given message
			and the progress bar based on the ratio of the current 
			count and the total count.
		'''
		self.view.prg_msg.set(message)

		progress = 100 * current_count / total_count
		self.view.prg_var.set(progress)


	def exit(self):
		'''
			Prompts the user to click whether or not they want to exit
			and closes the window if the answer is yes.
		'''
		# user_answer = msg.askyesno(constants.APP_NAME, 'Are you sure?')

		# if user_answer:
		#  	self.view.destroy()
		self.view.destroy()


	def on_table_change(self, *args):
		table = self.view.sel_table_var.get()
		if table != self.model.tbl_name:
			print(f'table: {table} selected...')
			self.model.tbl_name = table
			print('fetching loaded file names...')
			self._set_file_names()
			
			if not self.view.file_lstbx.size():
				self.view.disable_delete_button()
			print('fetching record count...')
			self._set_row_count_label()
			
			self.model.col_names = self.model.fetch_table_columns()
			
			self.view.col_list_var.set(self.model.col_names)
			
			self.set_file_frame_text()
			self.set_col_frame_text()

			if not self.load_enabled:
				self.view.enable_load_button()
				self.load_enabled = True

			if not self.delete_all_enabled:
				self.view.enable_delete_all_button()
				self.delete_all_enabled = True


	def set_file_frame_text(self):
		file_count = self.view.file_lstbx.size()
		self.view.file_frm.config(text=f'{const.FILE_FRM_TXT} ({file_count})')


	def set_col_frame_text(self):
		col_count = self.view.col_lstbx.size()
		self.view.col_frm.config(text=f'{const.COL_FRM_TXT} ({col_count})')


	def on_create_table_menu_click(self):
		query = self._read_sql_query(const.CREATE_SQL_DIR)
		if query:
			table = self.model.table_name_from_query(query)
			self._run_function_in_new_thread(
				func=self.model.create_table,
				args=(table, query),
				cb_func=self.view.show_message,
				cb_func_args=(f'Table {table} created!',)
				)


	def on_create_index_menu_click(self):
		query = self._read_sql_query(const.CREATE_SQL_INDEX_DIR)
		if query:
			index = self.model.index_name_from_query(query)
			self._run_function_in_new_thread(
				func=self.model.create_index,
				args=(index, query),
				cb_func=self.view.show_message,
				cb_func_args=(f'Index {index} created!',)
				)


	def on_select_click(self):
		query = self._read_sql_query(const.SELECT_SQL_DIR)
		if query:
			output_path = self.view.browse_for_saveas_name(
				initialdir=const.TEST_DATA_DIR,
				filetypes=(
					('CSV Files', '*.csv'),
					('Excel Files', '*.xlsx')
					)
				)
			if output_path:
				self._run_function_in_new_thread(
					func=self.model.export_from_sql_query,
					args=(query, output_path),
					cb_func=self.view.show_message,
					cb_func_args=(f'{output_path} created!',)
					)


	def on_xlsx_to_csv_click(self):
		input_files = self.view.browse_for_files(
			initialdir=const.DATA_DIR,
			filetypes=(('Excel Files', '*.xlsx'),)
			)
		if input_files:
			# gets the directory from the first input file
			input_dir = ntpath.basename(input_files[0])
			out_dir = self.view.browse_for_folder(initialdir=input_dir)
			if out_dir:
				self._run_function_in_new_thread(
					func=self.model.xlsx_to_csv,
					args=(input_files, out_dir),
					cb_func=self.view.show_message,
					cb_func_args=('Conversion Finished!',)
					)


	def _read_sql_query(self, query_dir):
		sql_file = self.view.browse_for_file(query_dir)
		if sql_file:
			return open(sql_file).read()


	def selected_file_name(self):
		sel = self.view.file_lstbx.curselection()

		return self.view.file_lstbx.get(sel)


	def on_alphabetical_change(self):
		self.view.clear_column_listbox()

		cols = (
			sorted(self.model.col_names) if self.view.is_alpha_field.get()
			else self.model.col_names
			)

		self.view.col_list_var.set(cols)


	def on_file_list_click(self, event):
		'''
			Enables the delete button if it's not enabled and there
			are files present.
		'''
		if not self.delete_enabled and self.view.file_lstbx.size():
			self.view.enable_delete_button()


	def on_delete_click(self):
		file_name = self.selected_file_name()[0]

		message = (
			f'This action will delete all rows where {const.FILE_NAME_COL} '
			f'equals "{file_name}". Are you sure you want to continue?'
			)

		delete = self.view.ask_yes_no(message)
		if delete:
			query = f'''
				DELETE FROM {self.model.tbl_name}
				WHERE {const.FILE_NAME_COL} = ?
				'''

			args = (file_name, )

			self.model.execute_sql(query, args)

			self.view.file_lstbx.delete(self.view.file_lstbx.curselection())

			self.set_file_frame_text()
			self._set_row_count_label()


	def on_delete_all_click(self):
		message = (
			'This action will delete all records from table '
			f'{self.model.tbl_name}. Are you sure you want to continue?'
			)

		delete = self.view.ask_yes_no(message)
		if delete:
			query = f'DELETE FROM {self.model.tbl_name}'

			self.model.execute_sql(query)

			self.view.clear_file_listbox()

			self.set_file_frame_text()
			self._set_row_count_label()

			self.view.disable_delete_button()


	def _set_file_names(self):
		file_names = self.model.fetch_file_names()

		self.view.file_list_var.set(file_names)


	def _set_row_count_label(self):
		row_count = self.model.fetch_row_count()

		self.view.row_count_label.config(text=f'Record Count: {row_count:,}')


	def _run_function_in_new_thread(self, func, args=(), cb_func=None, cb_func_args=()):
		'''
			Args:
				func:         function object used as target in new thread
				args:         arguments for taget function
				cb_func:      function object called when thread is finished
				cb_func_args: arguments for callback function
		'''
		thread = CbThread(
		    target=func,
		    callback=cb_func,
		    callback_args=cb_func_args,
		    args=args
		)

		thread.start()


	def on_input_late_orders_click(self):
		table_columns = self.model.fetch_table_columns(const.REASON_CODES_TABLE)

		self.input_late_orders_view = InputLateOrderReasonCodesView(self, table_columns)

		self._populate_reason_codes_treeview()


	def _populate_reason_codes_treeview(self, clear_first=False):
		reason_codes = self.model.fetch_reason_codes()

		treeview = self.input_late_orders_view.reason_code_treeview

		if clear_first:
			treeview.delete(*treeview.get_children())

		for values in reason_codes:
			reason_code_id = values[0]

			treeview.insert('', 'end', iid=reason_code_id, text=reason_code_id, values=values)


	def reason_code_combobox_post_command(self):
		reason_code_descriptions = self.model.fetch_reason_code_descriptions()
		
		if reason_code_descriptions:
			self.input_late_orders_view.reason_code_cbo.config(
				values=reason_code_descriptions
				)


	def on_delete_late_order_click(self, order_release_id):
		self.model.delete_later_order(order_release_id)

		self._clear_later_order_values()


	def _clear_later_order_values(self):
		self.input_late_orders_view.order_release_value.set('')
		self.input_late_orders_view.reason_code_cbo.set('')
		self.input_late_orders_view.comments_txt.delete('1.0', 'end')
		
		self._clear_later_order_update_info()


	def _clear_later_order_update_info(self):
		self.input_late_orders_view.update_user_value.set('')
		self.input_late_orders_view.update_date_value.set('')


	def on_fetch_late_order_click(self, order_release_id):
		late_order = self.model.fetch_late_order(order_release_id)

		if late_order:
			reason, comments, user, date = late_order

			# clear the old comments before inserting the new
			self.input_late_orders_view.comments_txt.delete('1.0', 'end')

			self.input_late_orders_view.reason_code_cbo.set(reason)
			self.input_late_orders_view.comments_txt.insert('1.0', comments)
			self.input_late_orders_view.update_user_value.set('Update User: ' + user)
			self.input_late_orders_view.update_date_value.set('Update Date: ' + date.strftime('%Y/%m/%d, %H:%M:%S'))
		else:
			self.view.show_message(
				f'Order ({order_release_id}) does not exist in table ({const.LATE_ORDERS_TABLE}).',
				parent=self.input_late_orders_view
				)


	def on_save_late_order_click(self, order_release_id, reason_code_description, comments):
		self._clear_later_order_update_info()

		self.model.insert_or_replace_late_order(order_release_id, reason_code_description, comments)

		self.view.show_message(
			f'Later order ({order_release_id}) saved!', 
			parent=self.input_late_orders_view
			)


	def on_add_reason_code_click(self, reason_code):
		self.model.insert_reason_code(reason_code)

		self._populate_reason_codes_treeview(clear_first=True)


	def on_delete_reason_code_click(self):
		selection = self.input_late_orders_view.reason_code_treeview.selection()

		for reason_code_id in selection:
			self.model.delete_reason_code(int(reason_code_id))

			self._populate_reason_codes_treeview(clear_first=True)


	def on_export_late_or_blank_date_orders_menu_click(self):
		self.export_late_or_blank_date_orders_view = ExportLateOrBlankDateOrdersView(self)
		
		self._set_default_export_date_range()

	def _set_default_export_date_range(self):
		date_range = self.model.get_prior_week_date_range()

		from_dt, to_dt = date_range

		self.export_late_or_blank_date_orders_view.from_date_value.set(from_dt)
		self.export_late_or_blank_date_orders_view.to_date_value.set(to_dt)


	def on_export_late_or_blank_date_orders_button_click(self, from_dt, to_dt, is_shipped, division, order_type):
		if self.check_valid_date_format(from_dt):
			if self.check_valid_date_format(to_dt):
				file_name = self.view.browse_for_saveas_name(
					filetypes=(('CSV Files', '*' + const.CSV),), 
					parent=self.export_late_or_blank_date_orders_view
					)

				if const.CSV not in file_name:
					file_name += const.CSV
				
				self.model.export_late_or_missing_date_orders(
					file_name, from_dt, to_dt, is_shipped, division, order_type
					)


	def check_valid_date_format(self, date_str):
		valid = self.model.is_valid_date_format(date_str)

		if not valid:
			self.view.show_message(
				f'Date "{date_str}" format must be like "{self.model.sample_date_format}"',
				parent=self.export_late_or_blank_date_orders_view
				)

		return valid


	def on_updatel_table_menu_click(self, by_cols, table_name):
		file_path = self.view.browse_for_file(
			filetypes=(
					('Excel Files', '*.xlsx'),
					('CSV Files', '*.csv')
					)
			)

		if file_path:
			file_type = '.' + file_path.rsplit('.', 1)[1]
			
			if file_type in {const.CSV, const.XLSX}:
				print('reading:', file_path)

				df = pd.read_excel(file_path) if file_type == const.XLSX else pd.read_csv(file_path)

				columns = list(df)

				print('\ndata:', df.head())

				if all(c in columns for c in by_cols):
					table_cols = self.model.fetch_table_columns(table_name)

					match_cols = [x for x in columns if x in table_cols and x not in by_cols]

					if match_cols:
						self.model.update_table(df, match_cols, by_cols, table_name)

						self.view.show_message(f'Finished updating {match_cols} by {by_cols} in {table_name}!')
					else:
						self.view.show_message(
							f'No matching column names found in {file_path} and the {table_name} table.'
							f'For any columns that need to be updated in the {table_name} table, the column '
							'names in the input file must match exactly.'
							)
				else:
					self.view.show_message(
						f'Column(s) {by_cols} are required. Their names in {file_path} '
						f'must match exactly to their names in table {table_name}.'
						)
			else:
				self.view.show_message(
					f'Unsupported file: {file_path}. File type must be {const.CSV} or {const.XLSX}.'
					)
					