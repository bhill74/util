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
SHEET_DELIM = "!"
SHEET_CELL_DELIM = ":"
SHEET_BASE_COLUMN = ord('A')
SHEET_COLUMN_SIZE = 26


def canonicalizeId(gid):
    match = re.match('^https?://{}([^/]+)'.format(SHEET_URL_BASE),
                     gid)
    if match:
        return match.groups()[0]

    return gid


def to_colour(colour):
    return {'red': (colour[0]+0.0)/255, 
            'green': (colour[1]+0.0)/255,
            'blue': (colour[2]+0.0)/255}


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
        if sheet.isalnum() and not sheet.isnumeric():
            addr = sheet + SHEET_DELIM
        else:
            addr = "'{}'{}".format(sheet, SHEET_DELIM)

    addr += cell_addr(start)
    if end:
        addr += SHEET_CELL_DELIM + cell_addr(end)

    return addr


def cell_decomp(cell):
    if isinstance(cell, str):
        sh = None
        cr = cell
        if SHEET_DELIM in cell:
            sh, cr = cell.split(SHEET_DELIM)
            if sh[0] == '\'' and sh[-1] == '\'':
                sh = sh[1:-1]

        c = re.compile(r'\d+').split(cr)[0]
        v = cr[len(c):].split(SHEET_CELL_DELIM)[0]
        r = int(v) if len(v) else -1
        return sh, c, r

    if isinstance(cell, tuple):
        return None, cell[0], int(cell[1])

    return None, "", 0


def _same_cell(a, b):
    if a == b:
        return True

    if a.endswith(SHEET_DELIM+b):
        return True

    return False


def range_decomp(crange):
    if isinstance(crange, str):
        if SHEET_CELL_DELIM in crange:
            i = crange.split(SHEET_CELL_DELIM)
            e = i[1]
            if SHEET_DELIM in e:
                e = e.split(SHEET_DELIM)[1]

            return i[0], e, not _same_cell(i[0], e)

        e = crange
        if SHEET_DELIM in e:
            e = e.split(SHEET_DELIM)[1]
        return crange, e, not _same_cell(crange, e)

    if isinstance(crange, tuple):
        return crange[0], crange[1]

    return None, None


def column_to_index(column):
    val = [ord(c)-SHEET_BASE_COLUMN for c in column.upper()][::-1]

    r = 0
    f = 1;
    for i in range(len(val)):
        r += (val[i] + (1 if i > 0 else 0))*f
        f *= SHEET_COLUMN_SIZE;

    return r


def index_to_column(index):
    if index == 0:
        return chr(SHEET_BASE_COLUMN)

    val = []
    while True:
        val.insert(0, index % SHEET_COLUMN_SIZE)
        if index < SHEET_COLUMN_SIZE:
            break
        index = int(index/SHEET_COLUMN_SIZE) - 1

    return "".join([chr(c+SHEET_BASE_COLUMN) for c in val])


def shift_column(column, offset):
    return index_to_column(column_to_index(column) + offset)

def expand_range(crange, column_width=0, row_height=0):
    start, stop, _ = range_decomp(crange)
    if SHEET_DELIM in stop:
        stop = stop.split(SHEET_DELIM)[1]

    stop = shift_cell(stop, column_offset=column_width, row_offset=row_height)
    if start == stop:
        return start

    return start + SHEET_CELL_DELIM + stop

def get_from_range(crange, col=1, row=1, width=1, height=1):
    start, stop, _ = range_decomp(crange)
    if col >= 1 and row >= 1:
        start = shift_cell(start, col-1, row-1)
        return grow_range(start, r=width-1, b=height-1)
    elif col >= 1 and row < 0:
        start = shift_cell(start, col-1, 0)
        sh, c, stopr = cell_decomp(stop)
        stopr += row+1
        sh, c, r = cell_decomp(start)
        cell = cell_range(cell_addr((c, stopr)), sheet=sh)
        return grow_range(cell, r=width-1, t=height-1)
    elif col < 0 and row >= 1:
        start = shift_cell(start, 0, row-1)
        sh, stopc, r = cell_decomp(stop)
        sh, c, r = cell_decomp(start)
        cell = cell_range(cell_addr((stopc, r)), sheet=sh)
        cell = shift_cell(cell, 1+col, 0)
        return grow_range(cell, l=width-1, b=height-1)

    # Both negative
    stop = shift_cell(stop, col+1, row+1)
    return grow_range(stop, l=width-1, t=height-1)

def shift_range(crange, column_offset, row_offset=0):
    start, stop, multiple = range_decomp(crange)
    if not multiple:
        return shift_cell(start, column_offset=column_offset, row_offset=row_offset)

    start = shift_cell(start, column_offset=column_offset, row_offset=row_offset)
    stop = shift_cell(stop, column_offset=column_offset, row_offset=row_offset)
    return start + SHEET_CELL_DELIM + stop

def isolate_range_by_column(crange, columns):
    startc = stopc = columns
    if SHEET_CELL_DELIM in columns:
        startc, stopc = columns.split(SHEET_CELL_DELIM)
        
    start, stop, multiple = range_decomp(crange)
    s, c, r = cell_decomp(start)
    start = cell_range(cell_addr((startc, r)), sheet=s)
    if not multiple:
        return start

    _, c, r = cell_decomp(stop)
    stop = cell_addr((stopc, r))
    if _same_cell(start, stop):
        return start

    return start + SHEET_CELL_DELIM + stop
    
def isolate_range_by_row(crange, rows):
    startr = stopr = rows
    if isinstance(rows, str) and SHEET_CELL_DELIM in rows:
        startr, stopr = rowss.split(SHEET_CELL_DELIM)
        
    if isinstance(startr, str):
        startr = int(startf)
    if isinstance(stopr, str):
        stopr = int(stopr)

    start, stop, multiple = range_decomp(crange)
    s, c, r = cell_decomp(start)
    start = cell_range(cell_addr((c, startr)), sheet=s)
    if not multiple:
        return start

    _, c, r = cell_decomp(stop)
    stop = cell_addr((c, stopr))
    if _same_cell(start, stop):
        return start

    return start + SHEET_CELL_DELIM + stop
   
def grow_range(crange, l=0, r=0, b=0, t=0, lrbt=0, lr=0, bt=0, lt=0, rb=0):
    start, stop, _ = range_decomp(crange)
    if l != 0 or t != 0 or lrbt != 0 or lr != 0 or bt != 0:
        start = shift_cell(start, -l, -t)
        start = shift_cell(start, -lt, -lt)
        start = shift_cell(start, -lrbt, -lrbt)
        start = shift_cell(start, -lr, -bt)

    if r != 0 or b != 0 or lrbt != 0 or lr != 0 or bt != 0:
        stop = shift_cell(stop, r, b)
        stop = shift_cell(stop, rb, rb)
        stop = shift_cell(stop, lrbt, lrbt)
        stop = shift_cell(stop, lr, bt)

    if _same_cell(start, stop):
        return start

    return start + SHEET_CELL_DELIM + stop


def shift_cell(crange, column_offset=0, row_offset=0):
    if column_offset == 0 and row_offset == 0:
        return crange

    sh, c, r = cell_decomp(crange)
    ci = column_to_index(c)
    if column_offset < 0 and abs(column_offset) > ci:
        sys.stderr.write("Shift is too large\n")
        ci = 0
    else:
        ci += column_offset

    if row_offset < 0 and abs(row_offset) > (r-1):
        sys.stderr.write("Row shift is too great\n")
        r = 1
    else:
        r += row_offset

    c = index_to_column(ci)
    return cell_range("{}{}".format(c, r), sheet=sh)


def shift_range(cell_range, column_offset=0, row_offset=0):
    if SHEET_CELL_DELIM in cell_range:
        start, end = cell_range.split(SHEET_CELL_DELIM)
        start = shift_cell(start, column_offset, row_offset)
        end = shift_cell(end, column_offset, row_offset)
        return SHEET_CELL_DELIM.join([start, end])

    return shift_cell(cell_range, column_offset, row_offset)

def cell_to_index(address, offset=0):
    sh, c, r = cell_decomp(address)
    i = column_to_index(c) + offset
    if r > -1:
        r += offset - 1

    return i, r

def translate_cell_info(crange, data):
    start, stop, _ = range_decomp(crange)
    sh, c, r = cell_decomp(start)
    start = cell_addr((c, r))

    result = []
    for r in range(len(data)):
        row = data[r]
        new_row = row.copy()
        for c in range(len(row)):
            if not isinstance(row[c], str):
                continue

            if not row[c].startswith('='):
                continue

            def translate(match):
                coff = int(match[1], 10)
                roff = int(match[2], 10)
                return shift_cell(start, c + coff, r + roff)

            new_row[c] = re.sub('\#\[(-?\d+),(-?\d+)\]', translate, row[c])

        result += [new_row]

    return result


def range_to_info(cell_range):
    info = {'sheetId': 0 }
    start, stop, multiple = range_decomp(cell_range)
    sh, c, r = cell_decomp(start)
    if sh:
        info['sheetName'] = sh
        start = cell_addr((c, r))

    info['startColumnIndex'], info['startRowIndex'] = cell_to_index(start)
    if multiple:
        info['endColumnIndex'], info['endRowIndex'] = cell_to_index(stop, 1)
    else:
        info['endColumnIndex'] = info['startColumnIndex'] + 1
        info['endRowIndex'] = info['startRowIndex'] + 1

    return info


class GSheetBase(gbase.GoogleAPI):
    def __init__(self, scope, application="sheets",
                 credentials=None, service=None,
                 client_file=None,
                 credential_file=None,
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

    def title(self):
        info = self.info()
        return info['properties']['title']

    def getSheetInfo(self, sheetId):
        info = self.info()
        if info and 'sheets' in info:
            shts = [s['properties']['title'] for s in info['sheets']]
            sheets = [s for s in info['sheets'] if s['properties']['title'] == sheetId or s['properties']['sheetId'] == sheetId]
            return sheets[0] if len(sheets) else None

        return None 

    def getSheetIndex(self, sheetName):
        info = self.getSheetInfo(sheetName)
        if not info:
            return -1

        return info['properties']['sheetId']

    def getRangeInfo(self, rangeName):
        info = range_to_info(rangeName)
        if 'sheetName' in info:
            info['sheetId'] = self.getSheetIndex(info['sheetName'])
            del info['sheetName']
        
        return info
   
    def addSheet(self, sheetName, rows=None, columns=None, colour=None, index=-1):
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

        if index >= 0:
            r['addSheet']['properties']['index'] = index; 

        return self._batchUpdate(r)

    def protect(self, values, rangeName="A1"):
        r = [{'addProtectedRange':
                {'protectedRange':
                    {'range': self.getRangeInfo(rangeName),
                     'description': 'getting a lock'}}}]
        res = self._batchUpdate(r)

    def update(self, values, rangeName="A1", input_option='RAW'):
        if input_option == 'USER_ENTERED':
            values = translate_cell_info(rangeName, values)

        try:
            self.get_spreadsheets().values().update(
                spreadsheetId=self.gid,
                range=rangeName,
                valueInputOption=input_option,
                body={'values': values}).execute()
            columns = max([len(r) for r in values])
            result = grow_range(rangeName, b=len(values)-1, r=columns)
            return True, result
        except Exception as e:
            print(e)

        return False, None

    def updateByValue(self, key, values, rangeName="A1", note=None):
        sheetName, col, row = cell_decomp(rangeName)
        cells = self.retrieve(rangeName)
        num_rows = len(cells)
        col_index = column_to_index(col)
        insert_col = col_index
        insert_row = num_rows
        if values and not isinstance(values, list):
            values = list(values)

        data = [key]
        if values:
            values = [str(v) for v in values]
            data += values

        for i in range(num_rows):
            if cells[i][0] == key:
                insert_row = i
                data = values
                insert_col = col_index + 1
                break

        crange = cell_range("{}{}".format(
            index_to_column(insert_col), row + insert_row), sheet=sheetName)
        result = None
        if values:
            result = self.update([data], crange)
        else:
            result = self.update([3*['']], crange)

        if note:
            crange = cell_range("{}{}".format(
                index_to_column(col_index+1), row + insert_row), sheet=sheetName)
            self.setNote(note, crange)

        return result

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

    def setNote(self, note, rangeName="A1"):
        r = [{'repeatCell':
                {'range': self.getRangeInfo(rangeName), 
                 'cell': {'note': note},
                 'fields': 'note'}}]
        res = self._batchUpdate(r)

    def removeNote(self, rangeName="A1"):
        self.setNote('', rangeName)

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

    def toFile(self, client_file=None, application=None):
        if client_file:
            return gdrive.GFile(self.gid, self.name, application=application,
                                client_file=client_file)
        else:
            return gdrive.GFile(self.gid, self.name,
                                application=self.application,
                                credentials=self.credentials)
