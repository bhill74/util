from msdrive import *
import json
from openpyxl import Workbook
import tempfile
import re

SHEET_DELIM = "!"
SHEET_CELL_DELIM = ":"
SHEET_BASE_COLUMN = ord('A')
SHEET_COLUMN_SIZE = 26

def to_colour(colour):
    return '#{:02x}{:02x}{:02x}'.format(
        colour[0],
        colour[1],
        colour[2])
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

def range_to_info(cell_range, limit=None):
    info = {'sheetId': 0 }
    start, stop, multiple = range_decomp(cell_range)
    sh, c, r = cell_decomp(start)
    if sh:
        info['sheetName'] = sh
        start = cell_addr((c, r))

    info['range'] = start
    if start != stop:
        _, c, r = cell_decomp(stop)
        if r == -1 and limit:
            stop = "{}{}".format(c, limit())
            
        info['range'] += SHEET_CELL_DELIM + stop
        
    info['startColumnIndex'], info['startRowIndex'] = cell_to_index(start)
    info['numColumns'] = 1
    info['numRows'] = 1
    if multiple:
        info['endColumnIndex'], info['endRowIndex'] = cell_to_index(stop, 1)
        info['numRows'] = info['endRowIndex'] - info['startRowIndex']
        info['numColumns'] = info['endColumnIndex'] - info['startColumnIndex']
    else:
        info['endColumnIndex'] = info['startColumnIndex'] + 1
        info['endRowIndex'] = info['startRowIndex'] + 1

    return info

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

            new_row[c] = re.sub(r'\#\[(-?\d+),(-?\d+)\]', translate, row[c])

        result += [new_row]

    return result

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

        
class MSExcelItem(MSFile):
    def __init__(self, application, msid=None, path=None, driveId=None, credentials=None, debug=False, info=None):
        MSFile.__init__(self, application, msid=msid, path=path, driveId=driveId, credentials=credentials, debug=debug)

    def endpoint(self):
        return MSFile.endpoint(self)
        
class MSSpreadsheet(MSExcelItem):
    def __init__(self, application, msid=None, name='', driveId=None, credentials=None, debug=None, info=None):
        if msid is None and info:
            msid = info['id']

        MSExcelItem.__init__(self, application=application, msid=msid, driveId=driveId, credentials=credentials, debug=debug)
        if name:
            self._name = name


            
    def init(self, name=None, path='', folder=None, sheetName='Sheet1', rows=200, columns=20, colour=None):
        if self.msid is not None:
            return self.msid

        # Create a blank spreadsheet in the TMP directory
        blank = Workbook()
        file = os.path.join(tempfile.gettempdir(), "blank.xlsx");
        blank.save(file)

        if not name:
            name = self._name
        
        result = {}
        with open(file, "rb") as f:
            if not folder:
                folder = MSRootFolder(self.application, driveId=self.driveId, credentials=self.credentials, debug=self.debug)
   
            result = self.put(folder.endpoint()+':{}/{}.xlsx:/content'.format(path, name), payload=f.read())
            f.close()

        os.remove(file)
        try:
            self.msid = result['id']
        except:
            sys.stderr.write("The new spreadsheet could not be created under {}".format(folder.loc()))
            return None
        
        # TODO: Should just work with index=0 but it doesn't
        sheets = self._sheets()
        wksheet = MSWorksheet(self.application, self.msid, label=sheets[0]['name'], driveId=self.driveId, credentials=self.credentials, debug=self.debug)
        wksheet.setLabel(sheetName)

    def url(self):
        return self.attr('webUrl')

    def title(self):
        return os.path.splitext(self.attr('name'))[0]

    def getSheetIndex(self, sheetName):
        sheets = self._sheets()
        for i in range(len(sheets)):
            if sheets[i] == sheetName:
                return i

        return -1
    
    def getRangeInfo(self, rangeName, limit=None):
        if isinstance(rangeName, dict):
            return rangeName
        
        info = range_to_info(rangeName, limit=limit)
        if 'sheetName' in info:
            info['sheetId'] = self.getSheetIndex(info['sheetName'])
        elif 'sheetName' not in info:
            info['sheetName'] = self.sheetNames()[0]

        return info

    def addSheet(self, sheetName, colour=None, index=-1):
        data = {'name': sheetName }
        result = self.post(MSWorkbook.endpoint(self) + '/add', data=data)
        wksheet = MSWorksheet(self.application, self.msid, info=result, driveId=self.driveId, credentials=self.credentials, debug=self.debug)
        if colour:
            input = {'tabColor': colour }
            url = MSWorksheets.endpoint(self, id=result['position'])
            r = self.patch(url, json=input)

        self.clear_cache('sheets')

        return wksheet

    def _sheets(self):
        def get_sheets():
            i = self.get(MSWorkbook.endpoint(self))
            try:
                return i['value']
            except:
                pass

            return None

        return self.get_cache('sheets', get_sheets)

    def sheetNames(self):
        return [s['name'] for s in self._sheets()]

    def _range_url(self, info):
        return MSWorksheet.endpoint(self, label=info['sheetName'])+'/range(address=\'{}\')'.format(info['range'])

    def retrieve(self, rangeName, quiet=False):
        def get_limit():
            sh, c, r = cell_decomp(rangeName)
            data = self.usedAddress(sheetName=sh)
            start, stop, multiple = range_decomp(data)
            sh, c, r = cell_decomp(stop)
            return r
        
        info = self.getRangeInfo(rangeName, get_limit)

        try:
            result = self.get(self._range_url(info), props={'$select': 'values'})
        except Exception as e:
            if quiet:
                return []
                              
            print(e)
            return None

        return result['values']

    def setNote(self, note, rangeName="A1"):
        self.update([[note.replace("\n", ", ")]], rangeName)
        self.setFormat('font', {'size': 8}, rangeName=rangeName)

    def setFormat(self, type, attributes={}, rangeName="A1"):
        info = self.getRangeInfo(rangeName)
        self.patch(self._range_url(info)+'/format/'+type, json=attributes)
        return None

    def setFillColor(self, color, rangeName="A1"):
        return self.setFormat('fill', {'color':color}, rangeName)
    
    def autoSize(self, rangeName="A1"):
        def get_limit():
            sh, c, r = cell_decomp(rangeName)
            data = self.usedAddress(sheetName=sh)
            start, stop, multiple = range_decomp(data)
            sh, c, r = cell_decomp(stop)
            return r
        
        info = self.getRangeInfo(rangeName, get_limit)
        self.post(self._range_url(info)+'/format/autofitColumns')
        return None
    
    def update(self, values, rangeName="A1", input_option="RAW", quiet=False):
        if input_option == 'USER_ENTERED':
            values = translate_cell_info(rangeName, values)
            
        # Find the number of rows and columns
        rows = len(values)
        cols = 1
        for v in values:
            cols = max(cols, len(v))

        # Fil out columns to rectangular set of data.
        for v in values:
            while len(v) < cols:
                v.append('')
            
        info = self.getRangeInfo(rangeName)
        if rows != info['numRows'] or cols != info['numColumns']:
            rangeName = grow_range(info['range'],
                                   r=cols-info['numColumns'],
                                   b=rows-info['numRows'])
            if 'sheetName' in info:
                rangeName = cell_range(rangeName, sheet=info['sheetName'])

            info = self.getRangeInfo(rangeName)
        
        try:
            self.patch(self._range_url(info), json={'values':values})
        except Exception as e:
            if quiet:
                return False, [], 

            print(e)
            return False, None

        return True, rangeName

    def updateByValue(self, key, values, rangeName="A1", callback=None):
        sheetName, col, row = cell_decomp(rangeName)
        cells = self.retrieve(rangeName)
        num_rows = len(cells)
        col_index = column_to_index(col)
        insert_col = col_index
        insert_row = num_rows
        if values and not isinstance(values, list):
            values = list(values)

        # Find if there is a blank row in the data
        for i in range(len(cells)):
            if not any(d for d in cells[i]):
                insert_row = i
                break
                
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

        if callback:
            callback(self, crange)
            
        return result
    
    def setFormatting (self, colour, formula, rangeName="A1"):
        # NOTE: Not implemented in MSGraph yet
        rangeInfo = self.getRangeInfo(rangeName)
        data = { 'rule':
                 {'text': formula,
                  'format': { 'fill': { 'color': colour } },
                  'type': 'containsText',
                  'operator': 'textContains'},
               'rangeAddress': rangeInfo['range'] }
        url = MSWorksheet.endpoint(self, label=rangeInfo['sheetName'])
        r = self.post(url +'/conditionalFormats/add', data=data)
        print("R", json.dumps(r, indent=4))
        return True

    def formatting(self, sheetName):
        # NOTE: Not implemented in MSGraph yet       
        r = self.get(MSWorksheet.endpoint(self, label=sheetName) + '/conditionalFormats')
        return False

    def used(self, sheetName):
        r = self.get(MSWorksheet.endpoint(self, label=sheetName) + '/usedRange', props={'$select': 'text'})
        return r['text']
    
    def usedAddress(self, sheetName):
        r = self.get(MSWorksheet.endpoint(self, label=sheetName) + '/usedRange', props={'$select': 'address'})
        return r['address']
    
    def __rep__(self):
        return '<MSSpreadsheet {} ({})>'.format(self._name if self._name else self.name(), self.msid)
        
class MSWorkbook(MSExcelItem):
     def __init__(self, application, msid, driveId=None, credentials=None, debug=None):
        MSExcelItem.__init__(self, application=application, msid=msid, driveId=driveId, credentials=credentials, debug=debug)   

     def endpoint(self):
        return MSExcelItem.endpoint(self) + '/workbook/worksheets'
        
class MSWorksheet(MSExcelItem):
    def __init__(self, application, msid, label=None, sheetId=None, driveId=None, credentials=None, debug=None, info=None):
        self.label = label
        self.sheetId = sheetId

        MSExcelItem.__init__(self, application=application, msid=msid, driveId=driveId, credentials=credentials, debug=debug, info=info)

    def endpoint(self, id=None, label=None):
        if not id:
            try:
                id = self.sheetId
            except:
                pass

        if not label:
            try:
                label = self.label
            except:
                pass

        return MSWorkbook.endpoint(self) + ('(\'{}\')'.format(id) if id is not None else '(\'{}\')'.format(label))
        
    def label(self):
        if not self.label:
            self.label = MSSpreadsheet.getSheetLabel(self, self.sheetId)

        return self.label

    def sheetId(sef):
        if not self.sheetId:
            self.sheetId = MSSpreadsheet.getSheetIndex(self, self.label)

        return self.sheetId
        
    def setLabel(self, label):
        self.patch(json={'name':label})
        self.label = label
        self.clear_cache('sheets')
        
    def __rep__(self):
        return "<MSWorksheet &&>"
