import httplib2
import gbase
import os
import re
from apiclient import discovery
import pkg_resources
import locale
import time
import gdrive

SHEET_URL_BASE = "docs.google.com/spreadsheets/d/"


def canonicalizeId(gid):
    match = re.match('^https?://{}([^/]+)'.format(SHEET_URL_BASE),
                     gid)
    if match:
        return match.groups()[0]

    return gid


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

    def init(self, name):
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
                        'gridProperties': {'columnCount': 26, 'rowCount': 200},
                        'index': 0,
                        'sheetId': 0,
                        'sheetType': 'GRID',
                        'title': self.application
                    }
                }])

        try:
            result = self.get_spreadsheets().create(
                body=sheet).execute()
            self.gid = result['spreadsheetId']
        except Exception as e:
            print(e)

        return None

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
