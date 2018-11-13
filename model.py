from jss_server import JssServer
import inspect
from management_tools import loggers
import os
import plistlib

cf = inspect.currentframe()
filename = inspect.getframeinfo(cf).filename
filename = os.path.basename(filename)
filename = os.path.splitext(filename)[0]
logger = loggers.FileLogger(name=filename, level=loggers.DEBUG)


class Model(object):

    def __init__(self):
        jss_info = plistlib.readPlist(file)

        self.jss_server = JssServer(**jss_info)


        self.incorrect_barcode = None
        self.incorrect_asset = None
        self.incorrect_name = None
        self.incorrect_serial = None

        self.search_param = None
        self.jss_id = None

        self.proceed = False

        self.final_tugboat_fields = None

        self.barcode_var = None

        self.barcode = None
        self.asset = None
        self.asset_chkbtn = None
        self.asset_entry = None
        self.name = None
        self.serial = None