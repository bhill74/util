import os
import sys

from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from apiclient import discovery

API_DOMAIN = "www.googleapis.com"
API_URL = "https://{}".format(API_DOMAIN)


class GoogleAPI:
    def __init__(self, api, scopes, secret, application,
                 credentials=None, service=None):
        self.api = api
        if not isinstance(scopes, list):
            scopes = (scopes)

        self.scopes = ["{}/{}".format(API_URL, s) for s in scopes]
        self.secret = secret
        self.application = application
        self.credentials = credentials
        self.service = service

    def get_credentials(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """
        if self.credentials and not self.credentials.invalid:
            return self.credentials

        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)

        credential_file = \
            '{}.{}-python-{}.json'.format(
                self.api, API_DOMAIN, self.application)
        credential_path = \
            os.path.join(credential_dir, credential_file)

        store = Storage(credential_path)
        self.credentials = store.get()
        sys.argv = ['']
        if not self.credentials or self.credentials.invalid:
            flow = client.flow_from_clientsecrets(
                self.secret, self.scopes)
            flow.user_agent = self.application
            self.credentials = tools.run_flow(flow, store)
            print('Storing credentials to ' + credential_path)

        return self.credentials

    def get_service(self):
        if not self.service:
            self.service = \
                discovery.build(self.api, 'v3',
                                credentials=self.get_credentials())

        return self.service
