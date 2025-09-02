import os
import sys
import time
import requests
import json
import atexit
import urllib.parse
import pathlib

# External modules
sys.path.append(os.path.join(os.getenv("HOME"), 'lib', 'ext'))
from msal import PublicClientApplication, ConfidentialClientApplication, SerializableTokenCache

if 'MS_GRAPH_CRED' in os.environ:
    _CACHE_FILE = os.environ['MS_GRAPH_CRED']
    _CACHE_DIR = os.path.dirname(_CACHE_FILE)
else:
    _CACHE_DIR = os.path.join(pathlib.Path.home(), ".credentials")
    _CACHE_FILE = os.path.join(_CACHE_DIR, "msal_cache.bin")

_AUTHORITY_URL = 'https://login.microsoftonline.com/{}/'

_BASE_URL = 'https://graph.microsoft.com/v1.0'

class Base:
    def __init__(self, debug=False):
        self.debug = debug

    def debug(self, flag):
        self.debug = flag
        
    def debugMsg(self, header, msg=""):
        if not self.debug:
            return

        print("--- {}: {}".format(header, msg))

    def debugDict(self, info):
        for k, v in info.items():
            self.debugMsg(k, v)
        
    def errorMsg(self, msg=""):
        sys.stderr.write(msg +"\n")
              
class PlaintextFilePersistence(Base):
    def __init__(self, file_path):
        self.file_path = file_path
        self._state_changed = False

    def load(self):
        try:
            with open(self.file_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            return ""
        except Exception as e:
            errorMsg(f"Error loading cache from {self.file_path}: {e}")
            return ""

    def save(self, content):
        try:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, "w") as f:
                f.write(content)
                f.close()
            self._state_changed = False
        except Exception as e:
            errorMsg(f"Error saving cache to {self.file_path}: {e}")
            
    def has_state_changed(self):
        return True

persistence = PlaintextFilePersistence(_CACHE_FILE)
cache = SerializableTokenCache()
if os.path.exists(persistence.file_path) and os.path.getsize(persistence.file_path) > 0:
    try:
        cache.deserialize(persistence.load())
    except Exception as e:
        sys.stderr.write("Problem loading the cache {persistence.file_path}\n{e}\n")
        pass

try:
    pathlib.Path(_CACHE_DIR).mkdir()
except:
    pass

atexit.register(lambda: persistence.save(cache.serialize()) if cache.has_state_changed else None)

class MSGraphApplication(Base):
    def __init__(self, application, debug=False):
        Base.__init__(self, debug)
        self.name = application
        self.path = os.path.dirname(__file__)
        self.info = None
        if 'MS_GRAPH_APP' in os.environ:
            self.path = os.environ['MS_GRAPH_APP']
            if not os.path.exists(self.path):
                self.errorMsg("Application file {} can not be found".format(self.path))
                return
        elif 'MS_GRAPH_APP_DIR' in os.environ:
            self.path = os.environ['MS_GRAPH_APP_DIR']
            f = os.path.join(self.path, application + '.json')
            if os.path.exists(f):
                self.path = f
            else:
                self.errorMsg("No '{}' application found at {}".format(application, self.path))
                return
        else:
            f = os.path.join(self.path, application + '.json')
            if not os.path.exists(f):
                self.errorMsg("No '{}' application found at {}".format(application, self.path))
                return
            self.path = f
        
        with open(self.path, "r") as file:
            try:
                self.info = json.loads(file.read())
            except Exception as e:
                self.errorMsg("Application file '{}' could not be read\n{}".format(self.path, str(e)))

    def getName(self):
        return self.name

    def getTenant(self):
        return self.info['tenant'] if 'tenant' in self.info else None
    
    def getID(self):
        return self.info['id'] if 'id' in self.info else None

    def getSecretID(self):
        return self.info['secret_id'] if 'secrect_id' in self.info else None

    def getSecretValue(self):
        return self.info['secret_value'] if 'secret_value' in self.info else None

    def getScopes(self):
        return self.info['scopes'] if 'scopes' in self.info else None
    

class MSGraphCredentials(Base):
    def __init__(self, debug=False):
        Base.__init__(debug)
        return
    
class MSGraphBase(Base):
    def __init__(self, application,
                 credentials=None, debug=False):
        Base.__init__(self, debug)
        self.credentials = credentials
        self._cache = {}
        
        if isinstance(application, str):
            self.application = MSGraphApplication(application)
        elif isinstance(application, MSGraphApplication):
            self.application = application
        else:
            self.errorMsg("No application provided")
            return

    def clear_cache(self, key):
        if key in self._cache:
            del self._cache[key]
            
    def set_cache(self, key, value):
        self._cache[key] = value

    def get_cache(self, key, func=None):
        if key not in self._cache:
            self._cache[key] = func() if func else None
            
        return self._cache[key]
        
    def get_credentials(self):
        if self.credentials:
            return self.credentials

        tenant = self.application.getTenant();
        if not tenant:
            return None

        secret = self.application.getSecretValue()
        if secret:
            app = ConfidentialClientApplication(self.application.getID(),
                                      authority=_AUTHORITY_URL.format(tenant),
                                      client_credential=secret)
            result = app.acquire_token_for_client(scopes=['https://graph.microsoft.com/.default'])
        else:
            app = PublicClientApplication(self.application.getID(),
                                          authority=_AUTHORITY_URL.format(tenant),
                                          token_cache=cache)
            scopes = self.application.getScopes()
            accounts = app.get_accounts()
            if accounts:
                result = app.acquire_token_silent(scopes, account=accounts[0])
                if result:
                    self.credentials = result
                    return self.credentials

            flow = app.initiate_device_flow(scopes=scopes)
            print(flow['message'])
            result = app.acquire_token_by_device_flow(flow)

        self.credentials = result

        return self.credentials

    def token(self):
        creds = self.get_credentials()
        return creds['access_token'] if creds and 'access_token' in creds else ''
    
    def endpoint(self):
        return _BASE_URL + '/me'

    def _url(self, endpoint=''):
        if endpoint.startswith('//'):
            return _BASE_URL + endpoint[2:]

        return _BASE_URL + self.endpoint() + endpoint

    def _args(self, endpoint=''):
        url = endpoint if endpoint else self.endpoint()
        if url.startswith('https://'):
            url = 'https://' + urllib.parse.quote(url[8:])
        
        return {'headers': {'Authorization': 'Bearer ' + self.token() },
                'url': url}
    
    def get(self, endpoint='', props=None):
        self.debugMsg("GET");
        
        args = self._args(endpoint=endpoint)

        if props:
            args['url'] += '?'
            for k, v in props.items():
                args['url'] += f"{k}=" + urllib.parse.quote_plus(v) + '&'

        self.debugDict(args)
        result = requests.get(**args)
        self.debugMsg('Response Code', result.status_code)
        self.debugDict(result.json())
        
        return result.json()

    def post(self, endpoint='', data={}):
        self.debugMsg("POST")
        
        args = self._args(endpoint=endpoint)
        args['json'] = data
        
        self.debugDict(args)
        result = requests.post(**args)
        self.debugMsg('Response Code', result.status_code)
        self.debugDict(result.json())
        
        return result.json()
    
    def put(self, endpoint='', payload=None):
        self.debugMsg("PUT")
        args = self._args(endpoint=endpoint)
        args['data'] = payload

        self.debugDict(args)
        result = requests.put(**args)
        self.debugMsg('Response Code', result.status_code)
        self.debugDict(result.json())
        
        return result.json()

    def patch(self, endpoint='', data=None, json=None):
        self.debugMsg("PATCH")
        args = self._args(endpoint=endpoint)

        if data:
            self.debugMsg("DATA", data)
            args['data'] = data
            
        if json:
            self.debugMsg("JSON", json)
            args['json'] = json   
            args['headers']['Content-Type'] = 'application/json'

        self.debugDict(args)
        result = requests.patch(**args)
        self.debugMsg('Response Code', result.status_code)
        self.debugDict(result.json())
        
        return result.json()
