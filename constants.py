from pathlib import Path
import fuelcost as fc
import sys


APP_VERSION = '1.0.0'
APP_NAME = f'SC TOOLS {APP_VERSION}'
# todo update this list of modules
MODULES = [
	'collections',
	'contextlib',
	'datetime',
	'getpass',
	'ntpath',
	'pandas',
	'pathlib',
	'os',
	're',
	'requests',
	'sqlite3',
	'time',
	'threading',
	]

# path depends on whether the app is bundled as an executable
APP_DIR = (
	Path(sys._MEIPASS) if getattr(sys, 'frozen', False) 
	else Path(__file__).resolve().parent
	)

FILES_DIR = APP_DIR.joinpath('files')
MEDIA_DIR = FILES_DIR.joinpath('media')

# depending on the machine and exact path to shared folder. 
DATA_DIR = Path('s:/supply_chain/analytics/data/')
# DATA_DIR = Path('//dhqshareddata/Data/Supply_Chain/Analytics/Data')

TEST_DATA_DIR = DATA_DIR.joinpath('Test')

SQL_DIR = Path('s:/supply_Chain/Analytics/SQL')
CREATE_SQL_DIR = SQL_DIR.joinpath('Create')
CREATE_SQL_INDEX_DIR = CREATE_SQL_DIR.joinpath('Index')
SELECT_SQL_DIR = SQL_DIR.joinpath('Select')

DB_NAME = 'power_bi_data.db'

DB_PATH = DATA_DIR.joinpath(DB_NAME)

CSV = '.csv'
XLSX = '.xlsx'

FILE_TYPES = [CSV, XLSX]

CSV_SEP = ';'

# folder and SQL table names
EMP_TIME_DETAIL = 'EmployeeTimeDetail'
DAT = 'Dat'
DRIVER_LIST = 'DriverList'
ORDER_LEVEL = 'OrderLevel'
PLANTS = 'Plants'
STOP_LEVEL = 'StopLevel'
STOP_LEVEL_NFR = 'StopLevel_NFR'

LATE_ORDERS_TABLE= 'LateOrders'
REASON_CODES_TABLE = 'ReasonCodes'

# list of tables built from source files
FILE_TABLES = [
	DAT,
	EMP_TIME_DETAIL,
	ORDER_LEVEL,
	STOP_LEVEL,
	STOP_LEVEL_NFR
]

# column names in sql table
FILE_NAME_COL = 'FileName'
ORDER_ID_COL_NAME = 'OrderId'
SHIP_ID_COL_NAME = 'ShipmentId'
DEST_ID_COL_NAME = 'DestCode'

# column names in Employee Time Detail input data
EMP_DATE_COL = 'APPLYDTM'
EMP_FNAME_COL = 'FIRSTNAME'
EMP_HRS_COL = 'HOURS'
EMP_ID_COL = 'DRIVERID'
EMP_LNAME_COL = 'LASTNAME'
EMP_PAYCODE_COL = 'PAYCODE'
EMP_PUNCH_IN_COL = 'INPUNCH'
EMP_PUNCH_OUT_COL = 'OUTPUNCH'
EMP_WHSE_CODE_COL = 'HOMELABORLEVELNM1'

# column names in both order and stop level data
ACCEPT_TNDR_COST_COL = 'AcceptedTenderCost'
ACCS_COL = 'Accessorials'
APPT_DELIV_COL = 'AppointmentDelivery'
APPT_PICKUP_COL = 'AppointmentPickup'
APPT_END_COL = 'AppointmentWindowEnd'
APPT_START_COL = 'AppointmentWindowStart'
DRIVER_FNAME_COL = 'DriverFirstName'
DRIVER_ID_COL = 'DriverID'
DRIVER_LNAME_COL = 'DriverLastName'
EQP_COL = 'EquipmentGroupProfile' 
FUEL_COL = 'Fuel'
LN_HAUL_COL = 'LineHaul'
LOAD_DIST_COL = 'LoadedDistance'
SERV_PROV_COL = 'ServiceProvider'
SHIP_GL_COST = 'ShipmentGLCost'
SHIP_ID_COL = 'ShipmentID'
SRC_COL = 'SourceLocationName'
SRC_WHSE_ID_COL = 'SourceLocationID'
TENDER_STAT_COL = 'TenderStatus'
TOT_DIST_COL = 'TotalDistance'
UNLOAD_DIST_COL = 'UnloadedDistance'
WT_UTIL_COL = 'WeightUtilization' 

#fuel cost variable for changing fuel cost for spot shipments
FUEL_COST = fc.FUEL_COST

# row indexes in both order and stop level data
EXPORT_DATE_ROW = 0

# label width
LBL_W = 10

# combobox width 
CBO_WIDTH = 75

# entry width
ENT_WIDTH = CBO_WIDTH + 3

PAD = 10

FILE_FRM_TXT = 'Loaded Files'
COL_FRM_TXT = 'Columns'

OPEN_FILE_TRIES = 5



