import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox as msg
from tkinter import ttk 

import constants as const


class View(tk.Tk):
	'''
		Main window of the application.
	'''


	def __init__(self, controller):
		super().__init__()
		self.cntlr = controller

		self.title(const.APP_NAME)
		self.protocol('WM_DELETE_WINDOW', self.cntlr.exit)
		self.config(menu=Menu(self.cntlr))

		self.tbl_cbo = None

		self.col_frm = None
		self.file_frm = None
		self.col_lstbx = None
		self.file_lstbx = None

		self.load_btn = None
		self.delete_btn = None
		self.row_count_label = None

		self.prg_msg = tk.StringVar()
		self.prg_var = tk.DoubleVar()

		# stores the state of the "Alphabetical" checkbox
		self.is_alpha_field = tk.IntVar()

		self.db_path = tk.StringVar()

		# selected table variable
		self.sel_table_var = tk.StringVar()

		self.col_list_var = tk.StringVar()
		self.file_list_var = tk.StringVar()

		#self.state('zoomed') # maximizes the window
		self._make_frames() 
		self._make_widgets()
		self._center_window()

		self.disable_load_button()
		self.disable_delete_button()
		self.disable_delete_all_button()


	def _center_window(self):
		# updates the window dimensions
		self.update()

		width = self.winfo_width()
		height = self.winfo_height()

		x_offset = (self.winfo_screenwidth() - width) // 2
		y_offset = (self.winfo_screenheight() - height) // 2

		self.geometry(
			f'{width}x{height}+{x_offset}+{y_offset}'
			)


	def _make_frames(self):
		# main frame covering the whole window
		self.main_frm = ttk.Frame(self)
		self.main_frm.pack(
			fill='both', expand=1, padx=const.PAD, pady=const.PAD
			)
		self.prg_frm = ttk.Frame(self)


	def _make_widgets(self):
		frm = ttk.Frame(self.main_frm)
		frm.pack(anchor=tk.W)

		lbl = ttk.Label(frm, text='Database:', width=const.LBL_W)
		lbl.pack(side=tk.LEFT)

		ent = ttk.Entry(
			frm, textvariable=self.db_path, state='readonly', 
			width=const.ENT_WIDTH
			)
		
		ent.pack()

		frm = ttk.Frame(self.main_frm)
		frm.pack(anchor=tk.W, pady=(0, const.PAD))

		lbl = ttk.Label(frm, text='Tables:', width=const.LBL_W)
		lbl.pack(side=tk.LEFT)

		self.tbl_cbo = ttk.Combobox(
			frm, postcommand=self.cntlr.on_table_combobox_click,
			textvariable=self.sel_table_var, state='readonly',
			width=const.CBO_WIDTH
			)

		self.tbl_cbo.pack()

		tbl_info_frm = ttk.Frame(self.main_frm)
		tbl_info_frm.pack(fill=tk.BOTH)

		self.file_frm = ttk.LabelFrame(tbl_info_frm, text=const.FILE_FRM_TXT)
		self.file_frm.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

		frm = tk.Frame(self.file_frm, background='white', relief='sunken')
		frm.pack(fill=tk.BOTH, expand=1)

		self.file_lstbx = tk.Listbox(
			frm, listvariable=self.file_list_var, borderwidth=0, 
			highlightthickness=0
			)

		self.file_lstbx.pack(fill=tk.BOTH, expand=1, padx=const.PAD)
		self.file_lstbx.bind('<Button-1>', self.cntlr.on_file_list_click)

		self.col_frm = ttk.LabelFrame(tbl_info_frm, text=const.COL_FRM_TXT)
		self.col_frm.pack(side=tk.RIGHT, fill=tk.BOTH, expand=1, padx=(10, 0))

		frm = tk.Frame(self.col_frm, background='white', relief='sunken')
		frm.pack(fill=tk.BOTH, expand=1)

		self.col_lstbx = tk.Listbox(
			frm, listvariable=self.col_list_var, borderwidth=0, 
			highlightthickness=0
			)

		self.col_lstbx.pack(fill=tk.BOTH, expand=1, padx=const.PAD)

		chk = ttk.Checkbutton(
			self.main_frm, text='Alphabetical', 
			command=self.cntlr.on_alphabetical_change,
			variable=self.is_alpha_field
			)

		chk.pack(anchor=tk.E, pady=(0, const.PAD))

		footer_frm = ttk.Frame(self.main_frm)
		footer_frm.pack(fill='x')

		self.row_count_label = ttk.Label(footer_frm)
		self.row_count_label.pack(side=tk.LEFT)

		frm = ttk.Frame(footer_frm)
		frm.pack(anchor=tk.E)

		self.load_btn = ttk.Button(
			frm, text='Load New', command=self.cntlr.on_load_new_click
			)

		self.load_btn.pack(side=tk.LEFT, padx=const.PAD)

		self.delete_btn = ttk.Button(
			frm, text='Delete', command=self.cntlr.on_delete_click
			)

		self.delete_btn.pack(side=tk.LEFT)

		self.delete_all_btn = ttk.Button(
			frm, text='Delete All', command=self.cntlr.on_delete_all_click
			)
		self.delete_all_btn.pack(side=tk.LEFT, padx=(10, 0))

		# progress bar widgets 
		self.prg_lbl = ttk.Label(self.prg_frm, textvariable=self.prg_msg)
		self.prg_lbl.pack(fill='x')
		self.prg_bar = ttk.Progressbar(self.prg_frm, variable=self.prg_var)
		self.prg_bar.pack(fill='x')


	def insert_file(self, name):
		self.file_lstbx.insert(tk.END, name)


	def clear_file_listbox(self):
		self.file_lstbx.delete(0, tk.END)


	def clear_column_listbox(self):
		self.col_lstbx.delete(0, tk.END)


	def show_progress_widgets(self):
		'''
			Resets the progress message and bar and makes them visible.
		'''
		self.prg_msg.set('')
		self.prg_var.set(0)

		self.prg_frm.pack(fill='x')


	def hide_progress_widgets(self):
		'''
			Makes the progress message and bar not visible.
		'''
		self.prg_frm.pack_forget()


	def enable_load_button(self):
		self.load_btn.config(state=tk.NORMAL)


	def disable_load_button(self):
		self.load_btn.config(state=tk.DISABLED)


	def enable_delete_button(self):
		self.delete_btn.config(state=tk.NORMAL)


	def disable_delete_all_button(self):
		self.delete_btn.config(state=tk.DISABLED)


	def enable_delete_all_button(self):
		self.delete_all_btn.config(state=tk.NORMAL)


	def disable_delete_button(self):
		self.delete_all_btn.config(state=tk.DISABLED)


	def ask_yes_no(self, message):
		return msg.askyesno(const.APP_NAME, message)


	def show_message(self, message, parent=None):
		msg.showinfo(const.APP_NAME, message, parent=parent)


	def browse_for_file(self, initialdir=None, filetypes=()):
		return filedialog.askopenfilename(
			initialdir=initialdir,
			filetypes=filetypes
			)


	def browse_for_files(self, initialdir=None, filetypes=()):
		return filedialog.askopenfilenames(
			initialdir=initialdir, 
			filetypes=filetypes
			)


	def browse_for_saveas_name(self, initialdir=None, filetypes=(), parent=None):
		return filedialog.asksaveasfilename(
			initialdir=initialdir, 
			filetypes=filetypes,
			parent=parent
			)


	def browse_for_folder(self, initialdir):
		return filedialog.askdirectory(initialdir=initialdir)


class Menu(tk.Menu):
	'''
		Menu bar of the main window.
	'''


	def __init__(self, cntlr):
		super().__init__()

		self.cntlr = cntlr

		self._make_file_menu()
		self._make_tools_menu()


	def _make_file_menu(self):
		file_menu = tk.Menu(self, tearoff=False)

		self.add_cascade(label='File', menu=file_menu)

		file_menu.add_command(
			label='Exit', command=self.cntlr.exit, accelerator='Ctrl+q'
			)


	def _make_tools_menu(self):
		tools_menu = tk.Menu(self, tearoff=False)
		exe_sql_menu = tk.Menu(self, tearoff=False)
		create_menu = tk.Menu(self, tearoff=False)
		update_orders_menu = tk.Menu(self, tearoff=False)
		update_stops_menu = tk.Menu(self, tearoff=False)

		exe_sql_menu.add_cascade(label='CREATE', menu=create_menu)

		exe_sql_menu.add_command(
			label='SELECT', command=self.cntlr.on_select_click
			)

		create_menu.add_command(
			label='Table', command=self.cntlr.on_create_table_menu_click
			)

		create_menu.add_command(
			label='Index', command=self.cntlr.on_create_index_menu_click
			)

		update_orders_menu.add_command(
			label=f'By {const.ORDER_ID_COL_NAME}',
			command=lambda:self.cntlr.on_updatel_table_menu_click(
				[const.ORDER_ID_COL_NAME,], const.ORDER_LEVEL
				)
			)

		update_orders_menu.add_command(
			label=f'By {const.SHIP_ID_COL_NAME} & {const.DEST_ID_COL_NAME}',
			command=lambda:self.cntlr.on_updatel_table_menu_click(
				[const.SHIP_ID_COL_NAME, const.DEST_ID_COL_NAME], const.ORDER_LEVEL
				)
			)

		update_orders_menu.add_command(
			label=f'By {const.SHIP_ID_COL_NAME}',
			command=lambda:self.cntlr.on_updatel_table_menu_click(
				[const.SHIP_ID_COL_NAME,], const.ORDER_LEVEL
				)
			)

		update_stops_menu.add_command(
			label=f'By {const.SHIP_ID_COL_NAME} & {const.DEST_ID_COL_NAME}',
			command=lambda:self.cntlr.on_updatel_table_menu_click(
				[const.SHIP_ID_COL_NAME, const.DEST_ID_COL_NAME], const.STOP_LEVEL
				)
			)

		update_stops_menu.add_command(
			label=f'By {const.SHIP_ID_COL_NAME}',
			command=lambda:self.cntlr.on_updatel_table_menu_click(
				[const.SHIP_ID_COL_NAME,], const.STOP_LEVEL
				)
			)

		tools_menu.add_cascade(label='Execute SQL', menu=exe_sql_menu)

		tools_menu.add_command(
			label='Input Late Order Reason Codes', 
			command=self.cntlr.on_input_late_orders_click
			)

		tools_menu.add_cascade(label='Update Order Level Table', menu=update_orders_menu)
		tools_menu.add_cascade(label='Update Stop Level Table', menu=update_stops_menu)

		tools_menu.add_command(
			label='XLSX to CSV', 
			command=self.cntlr.on_xlsx_to_csv_click
			)

		self.add_cascade(label='Tools', menu=tools_menu)


class InputLateOrderReasonCodesView(tk.Toplevel):
	'''
	'''

	LBL_W = 15
	COMMENT_LINES = 5


	def __init__(self, cntlr, reason_code_cols):
		super().__init__()

		self.cntlr = cntlr
		self.reason_code_cols = reason_code_cols

		self.config(menu=InputLateOrderReasonCodesMenu(self.cntlr))


		self.delete_later_order_enabled = False
		self.fetch_enabled = False
		self.save_enabled = False

		self.order_release_value = tk.StringVar()
		self.reason_code_value = tk.StringVar()
		self.update_user_value = tk.StringVar()
		self.update_date_value = tk.StringVar()

		self.order_release_value.trace('w', self._on_order_release_value_change)
		self.reason_code_value.trace('w', self._on_reason_code_value_change)

		self._make_frames()
		self._make_widgets()

		self._center_window()

		self._disable_delete_late_order_button()
		self._disable_fetch_button()
		self._disable_save_button()
		self._disable_delete_reason_code_button()


	def _on_order_release_value_change(self, *args):
		if self.order_release_value.get():
			if not self.delete_later_order_enabled:
				self._enable_delete_later_order_button()

			if not self.fetch_enabled:
				self._enable_fetch_button()

			if not self.save_enabled:
				if self.reason_code_value.get():
					self._enable_save_button()
		else:
			if self.delete_later_order_enabled:
				self._disable_delete_late_order_button()

			if self.fetch_enabled:
				self._disable_fetch_button()

			if self.save_enabled:
				self._disable_save_button()


	def _on_reason_code_value_change(self, *args):
		if self.reason_code_value.get():
			if not self.save_enabled:
				if self.order_release_value.get():
					self._enable_save_button()
		else:
			if self.save_enabled:
				self._disable_save_button()


	def _center_window(self):
		# updates the window dimensions
		self.update()

		width = self.winfo_width()
		height = self.winfo_height()

		x_offset = (self.winfo_screenwidth() - width) // 2
		y_offset = (self.winfo_screenheight() - height) // 2

		self.geometry(
			f'{width}x{height}+{x_offset}+{y_offset}'
			)


	def _make_frames(self):
		main_frm = ttk.Frame(self)
		main_frm.pack(fill='both', padx=const.PAD, pady=const.PAD)

		self.left_frm = ttk.Frame(main_frm)
		self.left_frm.pack(anchor='n', side=tk.LEFT)

		self.right_frm = ttk.Frame(main_frm)
		self.right_frm.pack(padx=(const.PAD * 2, 0))

		self.bottom_frm = ttk.Frame(main_frm)
		self.bottom_frm.pack(anchor='e', pady=(const.PAD, 0))

		self.order_realease_frm = ttk.Frame(self.left_frm)
		self.order_realease_frm.pack(fill='x')

		self.reason_frm = ttk.Frame(self.left_frm)
		self.reason_frm.pack(fill='x', pady=const.PAD)

		self.comments_frm = ttk.Frame(self.left_frm)
		self.comments_frm.pack(fill='x')

		self.left_btn_frm = ttk.Frame(self.left_frm)
		self.left_btn_frm.pack(anchor='e', pady=const.PAD)

		self.update_info_frm = ttk.Frame(self.left_frm)
		self.update_info_frm.pack(anchor='w')

		self.reason_codes_frm = ttk.Frame(self.right_frm)
		self.reason_codes_frm.pack()

		self.right_btn_frm = ttk.Frame(self.right_frm)
		self.right_btn_frm.pack(anchor='e', pady=const.PAD)


	def _make_widgets(self):
		lbl = ttk.Label(self.order_realease_frm, text='Order Release ID:', justify=tk.LEFT, width=self.LBL_W)
		lbl.pack(side=tk.LEFT)

		ent = ttk.Entry(self.order_realease_frm, textvariable=self.order_release_value)
		ent.pack(fill='x')
		ent.focus()

		lbl = ttk.Label(self.reason_frm, text='Reason Code:', justify=tk.LEFT, width=self.LBL_W)
		lbl.pack(side=tk.LEFT)

		self.reason_code_cbo = ttk.Combobox(
			self.reason_frm, textvariable=self.reason_code_value,
			postcommand=self.cntlr.reason_code_combobox_post_command, state='readonly'
			)
		self.reason_code_cbo.pack(fill='x', expand=1)

		lbl = ttk.Label(self.comments_frm, text='Comments:', justify=tk.LEFT, width=self.LBL_W)
		lbl.pack(anchor='n', side=tk.LEFT)

		self.comments_txt = tk.Text(self.comments_frm,  height=self.COMMENT_LINES)
		self.comments_txt.pack(fill='x')

		self.delete_late_order_btn = ttk.Button(
			self.left_btn_frm, text='Delete', 
			command=lambda:self.cntlr.on_delete_late_order_click(self.order_release_value.get())
			)
		self.delete_late_order_btn.pack(side=tk.LEFT)

		self.fetch_btn = ttk.Button(
			self.left_btn_frm, text='Fetch',
			command=lambda:self.cntlr.on_fetch_late_order_click(self.order_release_value.get())
			)
		self.fetch_btn.pack(side=tk.LEFT, padx=const.PAD)

		self.save_btn = ttk.Button(
			self.left_btn_frm, text='Save',
			command=lambda:self.cntlr.on_save_late_order_click(
				self.order_release_value.get(), 
				self.reason_code_value.get(), 
				self.comments_txt.get('1.0', tk.END)
				)
			)
		self.save_btn.pack(side=tk.LEFT)

		lbl = ttk.Label(self.update_info_frm, textvariable=self.update_user_value)
		lbl.pack(anchor='w')

		lbl = ttk.Label(self.update_info_frm, textvariable=self.update_date_value)
		lbl.pack(anchor='w')

		lbl = ttk.Label(self.reason_codes_frm, text='Available Reason Codes')
		lbl.pack()

		self.reason_code_treeview = ttk.Treeview(
			self.reason_codes_frm, columns=self.reason_code_cols, show='headings'
			)

		self.reason_code_treeview.bind('<<TreeviewSelect>>', self._on_treeview_select)

		for i, col in enumerate(self.reason_code_cols):
			self.reason_code_treeview.heading(col, text=col)

		self.reason_code_treeview.pack()

		btn = ttk.Button(
			self.right_btn_frm, text='Add', command=lambda:AddReasonCodeView(self.cntlr)
			)
		btn.pack(side=tk.LEFT, padx=const.PAD)

		self.delete_reason_code_btn = ttk.Button(self.right_btn_frm, text='Delete', command=self.cntlr.on_delete_reason_code_click)
		self.delete_reason_code_btn.pack()

		btn = ttk.Button(self.bottom_frm, text='Done', command=self.destroy)
		btn.pack()


	def _on_treeview_select(self, event):
		if not self.delete_reason_code_enabled:
			self._enable_delete_reason_code_button()


	def _disable_delete_late_order_button(self):
		self.delete_late_order_btn.config(state='disabled')
		self.delete_later_order_enabled = False


	def _enable_delete_later_order_button(self):
		self.delete_late_order_btn.config(state='enabled')
		self.delete_later_order_enabled = True


	def _disable_fetch_button(self):
		self.fetch_btn.config(state='disabled')
		self.fetch_enabled = False


	def _enable_fetch_button(self):
		self.fetch_btn.config(state='enabled')
		self.fetch_enabled = True


	def _disable_save_button(self):
		self.save_btn.config(state='disabled')
		self.save_enabled = False


	def _enable_save_button(self):
		self.save_btn.config(state='enabled')
		self.save_enabled = True


	def _disable_delete_reason_code_button(self):
		self.delete_reason_code_btn.config(state='disabled')
		self.delete_reason_code_enabled = False


	def _enable_delete_reason_code_button(self):
		self.delete_reason_code_btn.config(state='enabled')
		self.delete_reason_code_enabled = True


class InputLateOrderReasonCodesMenu(tk.Menu):
	def __init__(self, cntlr):
		super().__init__()

		self.cntlr = cntlr

		self.export_late_or_blank_orders_view = None

		self._make_file_menu()


	def _make_file_menu(self):
		file_menu = tk.Menu(self, tearoff=False)

		file_menu.add_command(
			label='Export Late or Blank Date Orders',
			command=self.cntlr.on_export_late_or_blank_date_orders_menu_click
			)
		self.add_cascade(label='File', menu=file_menu)


class AddReasonCodeView(tk.Toplevel):
	'''
	'''

	ENT_W = 40


	def __init__(self, cntlr):
		super().__init__()

		self.cntlr = cntlr

		self.reason_code_value = tk.StringVar()
		self.reason_code_value.trace('w', self._on_reason_code_change)

		self.add_btn_enabled = False

		self._make_widgets()
		self._center_window()

		self._disable_add_button()


	def _on_reason_code_change(self, *args):
		reason_code = self.reason_code_value.get()

		if reason_code:
			if not self.add_btn_enabled:
				self._enable_add_btn()
		else:
			if self.add_btn_enabled:
				self._disable_add_button()


	def _make_widgets(self):
		frm = ttk.Frame(self)
		frm.pack(padx=const.PAD, pady=const.PAD)

		lbl = ttk.Label(frm, text='Reason Code:')
		lbl.pack(side=tk.LEFT)

		ent = ttk.Entry(frm, textvariable=self.reason_code_value, width=self.ENT_W)
		ent.pack()
		ent.focus()

		frm = ttk.Frame(self)
		frm.pack(anchor='e', padx=const.PAD, pady=(0, const.PAD))

		self.add_btn = ttk.Button(
			frm, text='Add', command=lambda:self.cntlr.on_add_reason_code_click(self.reason_code_value.get())
			)
		self.add_btn.pack(side=tk.LEFT, padx=const.PAD)

		btn = ttk.Button(frm, text='Done', command=self.destroy)
		btn.pack()


	def _disable_add_button(self):
		self.add_btn.config(state='disabled')
		self.add_btn_enabled = False


	def _enable_add_btn(self):
		self.add_btn.config(state='enabled')
		self.add_btn_enabled = True


	def _center_window(self):
		# updates the window dimensions
		self.update()

		width = self.winfo_width()
		height = self.winfo_height()

		x_offset = (self.winfo_screenwidth() - width) // 2
		y_offset = (self.winfo_screenheight() - height) // 2

		self.geometry(
			f'{width}x{height}+{x_offset}+{y_offset}'
			)


class ExportLateOrBlankDateOrdersView(tk.Toplevel):
	'''
	'''

	LBL_W = 11


	def __init__(self, cntlr):
		super().__init__()

		self.cntlr = cntlr

		self.from_date_value = tk.StringVar()
		self.to_date_value = tk.StringVar()
		self.shippped_value = tk.StringVar(value='Y')
		self.division_value = tk.StringVar(value='ID')
		self.order_type_value = tk.StringVar(value='Sales')

		self.from_date_value.trace('w', self._valid_inputs)
		self.to_date_value.trace('w', self._valid_inputs)
		self.shippped_value.trace('w', self._valid_inputs)
		self.division_value.trace('w', self._valid_inputs)
		self.order_type_value.trace('w', self._valid_inputs)

		self._make_frames()
		self._make_widgets()
		self._center_window()

		self._disable_export_button()


	def _make_frames(self):
		main_frm = ttk.Frame(self)
		main_frm.pack(fill='both', padx=const.PAD, pady=const.PAD)

		self.from_frm = ttk.Frame(main_frm)
		self.from_frm.pack(fill='x')

		self.to_frm = ttk.Frame(main_frm)
		self.to_frm.pack(fill='x', pady=const.PAD)

		self.shipped_frm = ttk.Frame(main_frm)
		self.shipped_frm.pack()

		self.division_frm = ttk.Frame(main_frm)
		self.division_frm.pack(pady=const.PAD)

		self.order_type_frm = ttk.Frame(main_frm)
		self.order_type_frm.pack()

		self.btn_frm = ttk.Frame(main_frm)
		self.btn_frm.pack(anchor='e', pady=const.PAD)


	def _make_widgets(self):
		lbl = ttk.Label(self.from_frm, text='From:', width=self.LBL_W)
		lbl.pack(side=tk.LEFT)

		ent = ttk.Entry(self.from_frm, textvariable=self.from_date_value)
		ent.pack(fill='x')

		lbl = ttk.Label(self.to_frm, text='To:', width=self.LBL_W)
		lbl.pack(side=tk.LEFT)

		ent = ttk.Entry(self.to_frm, textvariable=self.to_date_value)
		ent.pack(fill='x')

		lbl = ttk.Label(self.shipped_frm, text='Shipped:', width=self.LBL_W)
		lbl.pack(side=tk.LEFT)

		cbo = ttk.Combobox(
			self.shipped_frm, textvariable=self.shippped_value, values=['Y', 'N']
			)
		cbo.pack()

		lbl = ttk.Label(self.division_frm, text='Division:', width=self.LBL_W)
		lbl.pack(side=tk.LEFT)

		cbo = ttk.Combobox(
			self.division_frm, textvariable=self.division_value, 
			values=['CP', 'ID']
			)
		cbo.pack()

		lbl = ttk.Label(self.order_type_frm, text='Order Type:', width=self.LBL_W)
		lbl.pack(side=tk.LEFT)

		cbo = ttk.Combobox(
			self.order_type_frm, textvariable=self.order_type_value, 
			values=['Purchase', 'Sales', 'Transfer']
			)
		cbo.pack()

		self.export_btn = ttk.Button(
			self.btn_frm, text='Export', 
			command=lambda:self.cntlr.on_export_late_or_blank_date_orders_button_click(
				self.from_date_value.get(),
				self.to_date_value.get(),
				self.shippped_value.get(),
				self.division_value.get(),
				self.order_type_value.get()
				)
			)
		self.export_btn.pack(side=tk.LEFT, padx=const.PAD)

		btn = ttk.Button(self.btn_frm, text='Cancel', command=self.destroy)
		btn.pack()


	def _disable_export_button(self):
		self.export_btn.config(state='disabled')
		self.export_enabled = False


	def _enable_export_button(self):
		self.export_btn.config(state='enabled')
		self.export_enabled = True


	def _valid_inputs(self, *args):
		if self.from_date_value.get() and self.to_date_value.get() and self.shippped_value.get() and self.division_value.get() and self.order_type_value.get():
			if not self.export_enabled:
				self._enable_export_button()
		else:
			if self.export_enabled:
				self._disable_export_button()


	def _center_window(self):
		# updates the window dimensions
		self.update()

		width = self.winfo_width()
		height = self.winfo_height()

		x_offset = (self.winfo_screenwidth() - width) // 2
		y_offset = (self.winfo_screenheight() - height) // 2

		self.geometry(
			f'{width}x{height}+{x_offset}+{y_offset}'
			)

		

