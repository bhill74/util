import os
import sys
import re
import pkg_resources
import locale
import time

# Local modules
import gbase
import gdrive

# External modules
sys.path.append(os.path.join(os.getenv('HOME'), 'lib', 'ext'))
import httplib2
from apiclient import discovery

SHEET_URL_BASE = "docs.google.com/spreadsheets/d/"


def canonicalizeId(gid):
    match = re.match('^https?://{}([^/]+)'.format(SHEET_URL_BASE),
                     gid)
    if match:
        return match.groups()[0]

    return gid


def cell_addr(cell):
    if isinstance(cell, str):
        return cell

    if isinstance(cell, tuple) and len(cell) == 2:
        return "{}{}".format(cell[0], cell[1])

    print("not supported", cell)
    return ""


def cell_range(start, end=None, sheet=None):
    addr = ""
    if sheet:
        addr = sheet + "!"

    addr += cell_addr(start)
    if end:
        addr += ":" + cell_addr(end)

    return addr


def cell_decomp(cell):
    if isinstance(cell, str):
        c = re.compile(r'\d+').split(cell)[0]
        r = int(cell[len(c):])
        return c, r

    if isinstance(cell, tuple):
        return cell[0], int(cell[1])

    return "", 0


def to_colour(colour):
    return {'red': (colour[0]+0.0)/255, 
            'green': (colour[1]+0.0)/255,
            'blue': (colour[2]+0.0)/255}


def shift_column(column, offset):
    a = ord('A')
    val = [ord(c)-a for c in column.upper()]
    size = 26
    last = size-1

    r = offset
    for i in range(len(val)-1, -1, -1):
        val[i] += r
        r = int(val[i]/size)
        #print(" *V", val)
        if val[i] > last:
            val[i] %= last
        elif val[i] < 0:
            val[i] = ((size+val[i]) % size)
            r -= 1
        else:
            r = 0

        #print(" I", val, r)
        if r == 0:
            break

    if r > 0:
        val.prepend(r)
    elif r == -1 and val[0] == last:
        val = val[1:]
    elif r != 0:
        print("Offset too large")
        return column

    return "".join([chr(c+a) for c in val])


class GSheetBase(gbase.GoogleAPI):
    def __init__(self, scope, application="sheets",
                 credentials=None, service=None,
                 client_file=None,
                 credential_dir=None):
        if not client_file:
            client_file = \
                pkg_resources.resource_filename(__name__,
                                                "sheets_client_id.json")
            client_file = os.getenv("GOOGLE_SHEETS_CLIENT_ID", client_file)

        scopes = ['']
        gbase.GoogleAPI.__init__(
                self, "sheets",
                ["auth/spreadsheets{}".format(s) for s in scopes],
                client_file, application,
                credentials=credentials,
                service=service,
                credential_dir=credential_dir)

    def get_service(self):
        if not self.service:
            http = self.get_credentials().authorize(httplib2.Http())
            discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                            'version=v4')
            self.service = discovery.build(self.api, 'v4',
                                           http=http,
                                           discoveryServiceUrl=discoveryUrl)

        return self.service

    def get_spreadsheets(self):
        return self.get_service().spreadsheets()


class GItem(GSheetBase):
    def __init__(self, gid,
                 application=None, credentials=None, service=None,
                 client_file=None,
                 credential_dir=None):
        self.gid = gid
        GSheetBase.__init__(self, "",
                            application=application,
                            credentials=credentials,
                            service=service,
                            client_file=client_file,
                            credential_dir=credential_dir)


class IncompatibleFormat(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)


class GSpreadsheet(GItem):
    def __init__(self,
                 gid=None, name='',
                 application=None, credentials=None, service=None,
                 client_file=None,
                 credential_dir=None):
        self.name = name
        if gid is not None:
            gid = canonicalizeId(gid)

        GItem.__init__(self, gid=gid,
                       application=application,
                       credentials=credentials,
                       service=service,
                       client_file=client_file,
                       credential_dir=credential_dir)

    def init(self, name, sheetName='Sheet1', rows=200, columns=26, colour=None):
        if self.gid is not None:
            return self.gid

        sheet = dict(
            properties={
                'autoRecalc': 'ON_CHANGE',
                'title': name,
                'locale': locale.getlocale()[0],
                'timeZone': time.tzname[0]
            },
            sheets=[
                {
                    'properties': {
                        'gridProperties': {'columnCount': columns, 'rowCount': rows},
                        'index': 0,
                        'sheetId': 0,
                        'sheetType': 'GRID',
                        'title': sheetName 
                    }
                }])

        if colour:
            sheet['sheets'][0]['properties']['tabColor'] = to_colour(colour) 

        try:
            result = self.get_spreadsheets().create(
                body=sheet).execute()
            self.gid = result['spreadsheetId']
        except Exception as e:
            print(e)

        return None

    def _batchUpdate(self, requests):
        requests = requests if isinstance(requests, list) else [requests]
        try:
            self.get_spreadsheets().batchUpdate(
                spreadsheetId=self.gid,
                body={'requests': requests}).execute()
            return True
        except Exception as e:
            print(e)

        return False

    def info(self):
        return self.get_spreadsheets().get(spreadsheetId=self.gid).execute()

    def url(self):
        info = self.info()
        return info['spreadsheetUrl']

    def getSheetInfo(self, sheetId):
        info = self.info()
        if info and 'sheets' in info:
            sheets = [s for s in info['sheets'] if s['properties']['title'] == sheetId or s['properties']['sheetId'] == sheetId]
            return sheets[0] if len(sheets) else None

        return None 

    def getSheetIndex(self, sheetName):
        info = self.getSheetInfo(sheetName)
        if not info:
            return -1

        return info['properties']['sheetId']

    def addSheet(self, sheetName, rows=None, columns=None, colour=None):
        info = self.getSheetInfo(sheetName)
        if info:
            return False

        # TODO: Update sheet if not a match to properies??
        r = {'addSheet': {'properties': {'title': sheetName}}}
        if rows or columns:
            r['addSheet']['properties']['gridProperties'] = {}
            if rows:
                r['addSheet']['properties']['gridProperties']['rowCount'] = rows
            if columns:
                r['addSheet']['properties']['gridProperties']['columnCount'] = columns
        if colour:
            r['addSheet']['properties']['tabColor'] = to_colour(colour) 

        return self._batchUpdate(r)

    def protect(self, values, rangeName="A1"):
        r = [{'addProtectedRange':
                {'protectedRange':
                    {'range': {
                        'sheetId': 0, #index,
                        'startRowIndex': 0,
                        'startColumnIndex': 1,
                        'endColumnIndex': 2 },
                     'description': 'getting a lock'}}}]
        res = self._batchUpdate(r)
        print("RES", res)

    def update(self, values, rangeName="A1"):
        try:
            self.get_spreadsheets().values().update(
                spreadsheetId=self.gid,
                range=rangeName,
                valueInputOption='RAW',
                body={'values': values}).execute()
            return True
        except Exception as e:
            print(e)

        return False

    def append(self, values, rangeName="A1"):
        try:
            self.get_spreadsheets().values().append(
                spreadsheetId=self.gid,
                range=rangeName,
                valueInputOption='RAW',
                body={'values': values}).execute()
            return True
        except Exception as e:
            print(e)

        return False

    def retrieve(self, rangeName, quiet=False):
        try:
            result = self.get_spreadsheets().values().get(
                spreadsheetId=self.gid, range=rangeName).execute()
        except Exception as e:
            if quiet:
                return []

            print(e)
            return None

        return result['values'] if 'values' in result else []

    def export(self, mimeType=None, output=None, quiet=False):
        output = output if output else self.name
        fname, ext = os.path.splitext(output)
        if mimeType == 'text/csv':
            info = self.get_spreadsheets().get(spreadsheetId=self.gid).execute()
            multiple = True if len(info['sheets']) > 1 else False
            for sheet in info['sheets']:
                title = sheet['properties']['title']
                cells = self.retrieve(title)
                csv_name = "{}{}{}".format(fname, "_{}".format(title) if multiple else "", ext)

                if not quiet:
                    gdrive.transferMsg(self.toFile(), csv_name)

                fd = open(csv_name, 'w')
                for row in cells:
                    fd.write("{}\n".format(",".join(row)))
                fd.close()
        else:
            raise IncompatibleFormat("Cannot convert spreadsheet to {}".format(mimeType))

        if not quiet:
            print('  Export Complete')

    def open(self):
        gbase.GoogleAPI.open(
                'https://{}/%s/edit#gid=0'.format(SHEET_URL_BASE) %
                self.gid)

    def toFile(self):
        return gdrive.GFile(self.gid, self.name,
                            application=self.application)
