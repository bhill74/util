import webbrowser
import httplib2
import base
import os
import re
from apiclient import discovery
import pkg_resources
import locale
import time

SHEET_URL_BASE = "docs.google.com/spreadsheets/d/"


def canonicalizeId(spreadsheetId):
    match = re.match('^https?://{}([^/]+)'.format(SHEET_URL_BASE),
                     spreadsheetId)
    if match:
        return match.groups()[0]

    return spreadsheetId


class GoogleSheets(base.GoogleAPI):
    def __init__(self, application, spreadsheetId=None, spreadsheetName=''):
        client_file = pkg_resources.resource_filename(__name__,
                                                      "sheets_client_id.json")
        if "GOOGLE_SHEETS_CLIENT_ID" in os.environ:
            client_file = os.getenv("GOOGLE_SHEETS_CLIENT_ID", client_file)

        base.GoogleAPI.__init__(
                self, "sheets",
                '{}/auth/spreadsheets'.format(base.API_URL),
                client_file, application)

        self.spreadsheetId = spreadsheetId
        if spreadsheetId is not None:
            self.spreadsheetId = canonicalizeId(spreadsheetId)

        if spreadsheetId is None and spreadsheetName != '':
            self.spreadsheetId = self.create(spreadsheetName)

    def service(self):
        http = self.get_credentials().authorize(httplib2.Http())
        discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                        'version=v4')
        return discovery.build('sheets', 'v4', http=http,
                               discoveryServiceUrl=discoveryUrl)

    def create(self, name):
        service = self.service()

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
            result = service.spreadsheets().create(
                body=sheet).execute()
            return result['spreadsheetId']
        except Exception as e:
            print(e)

        return None

    def update(self, values, rangeName="A1"):
        service = self.service()

        try:
            service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheetId,
                range=rangeName,
                valueInputOption='RAW',
                body={'values': values}).execute()
            return True
        except Exception as e:
            print(e)

        return False

    def append(self, values, rangeName="A1"):
        service = self.service()

        try:
            service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheetId,
                range=rangeName,
                valueInputOption='RAW',
                body={'values': values}).execute()
            return True
        except Exception as e:
            print(e)

        return False

    def retrieve(self, rangeName):
        service = self.service()

        try:
            result = service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheetId, range=rangeName).execute()
        except Exception as e:
            print(e)
            return None

        return result['values'] if 'values' in result else []

    def open(self, spreadsheet_id):
        webbrowser.open(
                'https://{}/%s/edit#gid=0'.format(SHEET_URL_BASE) %
                spreadsheet_id)
