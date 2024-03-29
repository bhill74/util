#!/usr/bin/python3

"""
Fibery objects
"""

import os
import sys
import json
import requests
import urllib.parse
import re
import subprocess
import traceback

# Local modules
sys.path.append(os.path.join(os.getenv('HOME'), "lib", "config"))
from local_config import LocalConfigParser

# External modules
sys.path.insert(0, os.path.join(os.getenv('HOME'), 'lib', 'ext'))
import browsercookie
from pyparsing import nestedExpr

# Standard Names
_FIBERY_id = 'fibery/id' 
_FIBERY_public_id = 'fibery/public-id' 

# Standard Types
_FIBERY_text_type = 'fibery/text' 


class Config(LocalConfigParser):
    """
    Used to retrieve information for interfacing with the Fibery API
   {} 
    Arguments:
        [name = 'fibery.cfg'] -- The name of the configuration file to look for.
    """

    def __init__(self, name='fibery.cfg'):
        LocalConfigParser.__init__(self, name)

    def _insert(self, section, option, value, preserve=True):
        if not self.has_section(section):
            self.add_section(section)

        if self.has_section(section) and self.has_option(section, option):
            old_value = self.get(section, option)
            if old_value == value:
                print("Same value as existing")
                return False

            index=1
            old_option = "{}{}".format(option, index)
            while (self.has_option(section, old_option)):
                index=index+1
                old_option = "{}{}".format(option, index)

            print("Storing {}->{}->{}".format(section, option, old_value))
            self.set(section, old_option, old_value)

        print("Adding {}->{}->{}".format(section, option, value))
        self.set(section, option, value)
        return True

    def _retrieve(self, section, option):
        if self.has_section(section) and self.has_option(section, option):
            return self.get(section, option).strip()

        return None

    def _set_base(self, option, value):
        return self._insert('general', option, value)

    def _get_base(self, option, var):
        result = self._retrieve('general', option)
        return result if result else os.getenv(var, '')

    def account(self):
        return self._get_base('account', 'FB_ACCOUNT')

    def set_account(self, account):
        return self._set_base('account', account)

    def domain(self):
        domain = self._get_base('domain', 'FB_DOMAIN')
        if not domain:
            domain = "{}.fibery.io".format(self.account())

        return domain

    def token(self):
        return self._get_base('token', 'FB_TOKEN')

    def set_token(self, token):
        return self._set_base('token', token)

    def browser(self):
        return self._get_base('browser', 'FB_BROWSER')

    def set_browser(self, browser):
        return self._set_base('browser', browser)


def _download(response, output='archive'):
    """
    Used to download a file based on HTTP resonse
    """
    if response.status_code != 200:
        info = json.loads(response.text)
        msg = info['message'] if 'message' in info else "{} Unknown".format(response.status_code) 
        print("Unable to download ({})".format(msg))
        return 

    print("Downloading ({}):".format(output), end='', flush=True)
    count = 0
    with open(output, 'wb') as f:
        for chunk in response.iter_content(chunk_size=2048):
            count += 1
            if count % 80 == 0:
                print(".", end='', flush=True)
            if chunk:
                f.write(chunk)

        f.close()
        print(" done!")

def _get_attr(info, key):
    if key in info:
        return info[key]

    key = f'fibery/{key}'
    if key in info:
        return info[key]

    return None

def _get_name_and_id(info):
    if isinstance(info, dict):
        name = _get_attr(info, 'name')
        fid = _get_attr(info, 'id')
        return name, fid
    if isinstance(info, str):
        if len(info) == 36:
            return None, info
        else:
            return info, None

    return None, info

_all_schemas = {}
_config = Config()

_header_authorization = "Authorization"
_header_content_type = "Content-Type"

class FakeResponse:
    def __init__(self, text):
        l = len(text)
        self.status_code = int(text[l-3:])
        self.text = text[:l-3]

    def json(self):
        return json.loads(self.text)

_databases = {}
def RegisterDatabase(Class, Item, default=False):
    tag = Item.prefix()
    _databases[tag] = (Class, Item)
    if default:
        _databases['#'] = (Class, Item)


class Base:
    """
    The base Fibery class for interfacing with the Fibery WebAPI.

    Arguments:
        [account] -- The Fibery account, will default to the local configuration.
        [token] -- The Fibery access token, will default to the generated one.
    """

    def __init__(self, domain=None, token=None):
        if not domain:
            domain = _config.domain()

        self.domain = domain
        self.token = token

    def _headers(self, headers={}, token=None):
        if not token:
            if 'token' in headers:
                token = headers['token']
            else:
                token = self._token()

        if not token:
            raise ValueError("Missing access token")

        headers['Authorization'] = 'Token {}'.format(token)
        return headers

    def _data(self, data):
        if isinstance(data, list):
            return json.dumps(data)

        if isinstance(data, dict):
            return json.dumps(data)

        return data

    def get(self, url, headers={}, data={}, stream=False, token=None):
        if self._debug():
            print("URL:", url)

        headers = self._headers(headers=headers, token=token)
  
        if self._debug():
            print("Headers:", headers)

        response = requests.get(url, headers=headers, data=self._data(data), stream=stream)

        if self._debug():
            print("Response", json.dumps(response.json(), indent=4))
    
        return response

    def post(self, url, headers={}, data={}, files={}, token=None):
        if self._debug():
            print("URL:", url)

        headers = self._headers(headers=headers, token=token)

        if self._debug():
            print("Headers:", headers)
            print("DATA", data)
            if (isinstance(data, dict) or isinstance(data, list)) and len(data):
                print("Data:\n", json.dumps(data, indent=4))
            if len(files):
                print("Files:", files)

        if len(files):
            headers[_header_content_type] = 'multipart/form-data'
            cmd = ['curl', '-s', '-w', '%{http_code}', '-X', 'POST', url]

            def combine(option, pattern, info):
                cmd = []
                for k in info.keys():
                    cmd += [option, pattern.format(k, info[k])]
                return cmd

            if len(headers):
                cmd += combine('-H', '{}: {}', headers)
            cmd += combine('-F', '{}=@{}', files)
            if self._debug():
                print("Command:", " ".join(cmd))

            result = subprocess.run(cmd, stdout=subprocess.PIPE)
            response = FakeResponse(result.stdout.decode('utf-8'))
        else:
            headers[_header_content_type] = 'application/json'
            response = requests.post(url, headers=headers, data=self._data(data))

        if self._debug():
            print("Response", json.dumps(response.json(), indent=4))
        
        return response

    def delete(self, url, headers={}, token=None):
        if self._debug():
            print("URL:", url)

        headers = self._headers(headers=headers, token=token)
        return requests.delete(url, headers=headers)

    def getJSON(self, url, headers={}, data={}, stream=False, token=None, 
                default=None):
        r = self.get(url, headers=headers, data=data, stream=stream, token=token)
        if r.status_code != 200:
            return default

        return json.loads(r.text)

    def postJSON(self, url, headers={}, data={}, files={}, token=None, 
                default=None):
        r = self.post(url, headers=headers, data=data, files=files, token=token)

        if self._debug():
            print("Status Code:", r.status_code)

        if r.status_code != 200:
            print("Error:", json.loads(r.text)['message'])
            return default

        return json.loads(r.text)

    def download(self, url, output='archive', token=0):
        return _download(self.get(url, stream=True, token=token), output=output)

    def _debug(self):
        return os.getenv("FB_DEBUG", 'False') == 'True'

    def _domain(self, domain=None):
        if domain:
            return domain

        if hasattr(self, 'domain'):
            return self.domain

        return _config.domain() 

    def _url(self, domain):
        return 'https://{}'.format(domain)

    def _api(self, domain):
        return self._url(domain) + '/api'

    def _cookies(selfi, browser=None):
        browser = browser if browser else _config.browser()
        if browser == 'firefox':
            return browsercookie.firefox()
        elif browser == 'chrome':
            return browsercookie.chrome()
        
        return browsercookie.load()

    def new_token(self, browser=None):
        cookiejar = self._cookies(browser=None) 
        domain = self._domain()
        url = '{}/tokens'.format(self._api(domain))
        print("URL", url)
        r = requests.post(url, cookies=cookiejar)
        if r.status_code == 500:
            print('Error[{}]: Invalid login'.format(r.status_code))
            return None

        if r.status_code != 201:
            print('Error[{}]: Invalid address ({})'.format(r.status_code, url))
            return None

        obj = json.loads(r.text)
        if 'value' not in obj:
            print("No key was returned")
            return None

        token = obj['value']
        print('New token: {}'.format(token))
        return token
    
    def insert_token(self, token, browser=None):
        if not _config.account():
            account = self.domain
            account = account.replace('.fibery.io', '')
            account = account.replace('https://', '')
            _config.set_account(account)

        if not _config.browser() and browser:
            _config.set_browser(browser)

        if _config.set_token(token):
            _config.write()

    def _tokens(self):
        cookiejar = self._cookies()
        domain = self._domain()
        url = '{}/tokens'.format(self._api(domain))
        r = requests.get(url, cookies=cookiejar)
        if r.status_code == 500:
            return []

        if r.status_code != 201:
            print('Error[{}]: Invalid address ({})'.format(r.status_code, url))
            return []

        items = json.loads(r.text)
        return items

    def _token(self):
        if hasattr(self, 'token') and self.token:
            return self.token

        token = _config.token()
        if not token:
            token = self.new_token()

        return token 

    def _commands(self, domain=None):
        domain = self._domain(domain)
        return "{}/commands".format(self._api(domain))

    def command(self, command, args=None, domain=None, token=None):
        url = self._commands(domain=domain)
        cmd = {'command': command}
        if args:
            cmd['args'] = args

        return self.postJSON(url, headers={}, token=token, data=[cmd])

    def add(self, field, fid, items, domain=None, token=None):
        args = {'type': self.name(),
                'field': field,
                'entity': { _FIBERY_id: fid },
                'items': items}

        res = self.command('fibery.entity/add-collection-items', args, domain=domain, token=token)

        res = res[0]
        if 'success' not in res:
            if self._debug():
                print("Not successful")
            return False
       
        if not res['success']:
            print("Error: {}".format(res['result']['message']))
            return False 

        return True

    def query(self, command, select=[], domain=None, token=None, query={}, params={}):
        url = self._commands(domain=domain)
        args = None
        if len(query):
            if not args:
                args = {}

            args['query'] = query

        if len(params):
            if not args:
                args = {}

            args['params'] = params
 
        res = self.command(command, args, domain=domain, token=token)

        if not isinstance(res, list):
            return []
        
        res = res[0]
        if 'success' not in res:
            if self._debug():
                print("Not successful")
            return []
       
        if not res['success']:
            print("Error: {}".format(res['result']['message']))
            exit()
            return []

        if self._debug():
            print("Result:\n", json.dumps(res['result'], indent=4))

        return res['result']

    def schema_query(self, domain=None, token=None):
        if not domain:
            domain = self._domain()

        if domain not in _all_schemas:
            _all_schemas[domain] = Base.query(self, 'fibery.schema/query', domain=domain, token=token)
            
        return _all_schemas[domain]

    def get_schema(self, domain=None, token=None):
        res = self.schema_query(domain=domain, token=token)
        return res['fibery/types'] if len(res) else []

    def get_schema_by_id(self, fid, domain=None, token=None):
        schemas = self.get_schema(domain=domain, token=token)
        schemas = [s for s in schemas if s[_FIBERY_id] == fid]
        return schemas[0] if len(schemas) else None

    def get_schema_by_name(self, name, domain=None, token=None):
        schemas = self.get_schema(domain=domain, token=token)
        schemas = [s for s in schemas if s['fibery/name'] == name]
        return schemas[0] if len(schemas) else None


class Object(Base):
    """
        The common functionality of any Fibery object
    """
    def __init__(self, fid, domain=None, token=None):
        super().__init__(domain, token)
        self.fid = None
        self.info = None
        if isinstance(fid, str) or isinstance(fid, tuple):
            self.info = self._get_info(fid)
        elif isinstance(fid, dict):
            self.info = fid
        
        self.fid = self.info[_FIBERY_id] if self.info and _FIBERY_id in self.info else '-1'

    def _attr(self, name):
        return self.info[name] if self.info and name in self.info else None

    def _set_attr(self, name, value):
        if not self.info:
            self.info = {}
        self.info[name] = value

    def obj_type(self):
        return self.__class__.__name__

    def fibery_id(self):
        return self.fid

    def id(self):
        return self._attr(_FIBERY_public_id)

    def __rep__(self):
        return "<{} '{}'>".format(self.obj_type(), self.name())

    def __str__(self):
        return self.__rep__()


class Document(Base):
    def __init__(self, secret, domain=None, token=None):
        super().__init__(domain=domain, token=token)
        self._secret = secret

    def getContent(self, fmt='md'):
        url = "{}/documents/{}?format={}".format(self._api(self._domain()), self._secret, fmt)
        return self.getJSON(url)


class Documents(Base):
    def __init__(self, domain=None, token=None):
        super().__init__(domain=domain, token=token)

    def _commands(self, domain=None):
        domain= self._domain(domain)
        return "{}/documents/commands".format(self._api(domain))

    def getContentBySecrets(self, secrets, fmt='md'):
        url = "{}?format={}".format(self._commands(), fmt)
        secrets = [{'secret': s} for s in secrets]
        return self.postJSON(url, data={'command': 'get-documents', 'args': secrets})


class Field(Object):
    """
        A representation of a field from a Fibery database
    """
    def __init__(self, fid, parent_fid, domain=None, token=None):
        self.parent_fid = parent_fid 
        super().__init__(fid, domain, token)

    def _get_info(self, fid):
        schema = self.get_schema_by_id(self.parent_fid)
        fields = schema['fibery/fields'] if schema else []
        fields = [f for f in fields if f[_FIBERY_id] == fid]
        return fields[0] if len(fields) else None

    def name(self):
        return self._attr('fibery/name')

    def type(self):
        return self._attr('fibery/type')

    def meta(self):
        return self._attr('fibery/meta')

    def isDeleted(self):
        return self._attr('fibery/deleted?')

    def isPrimitive(self):
        if self.type() not in ["fibery/int", "fibery/decimal", "fibery/bool", "fibery/text", "fibery/email",
                   "fibery/emoji", "fibery/date", "fibery/date-time", "fibery/date-range", "fibery/date-time-range",
                   "fibery/uuid", "fibery/rank", "fibery/json-value", "fibery/url", "fibery/color"]:
            return False

        return True
    
    def isCollection(self):
        meta = self.meta()
        if not meta or 'fibery/collection?' not in meta or not meta['fibery/collection?']:
            return False

        return True

    def _get_db(self):
        db = None
        if hasattr(self, '_db') and self._db:
            db = self._db
        else:
            db = self._db = Database({'fibery/name': self.type()})

        return db

    def texts(self):
        db = self._get_db()
        if db is None:
            return [] 

        names = []
        for f in db.fields():
            n = f.name()
            if n == _FIBERY_public_id:
                continue

            if f.type() == _FIBERY_text_type:
                names.append(n)
        
            elif f.type() == 'fiberty/uuid':
                if n.endswith('/document-secret') or n.endswith('/secret'):
                    names.append(n)

        return names 
    
    def secrets(self):
        db = self._get_db()
        if db is None:
            return [] 

        names = []
        for f in db.fields():
            n = f.name()
            if n.endswith('/document-secret'):
                names.append(n)

        return names

    def select(self):
        name = self.name()
        if self.isPrimitive():
            return name 

        n = self.secrets()
        if len(n) == 0:
            n = self.texts()

        if len(n) == 0:
            n.append(_FIBERY_id)

        if self.isCollection():
            return {name: {'q/select': n, 'q/limit': 'q/no-limit'}}

        return {name: n}

    def _info(self):
        db = self._get_db()
        if db is None:
            return [] 

        select = [f for f in db.fields() if f.isPrimitive()]
        return db.query(select=select)

    def values(self):
        return [v['enum/name'] for v in self._info()]

_FIBERY_condition_ops = {
    '==':   '=',
    'in':   'q/contains',
    'and':  'q/and',
    'or':   'q/or',
    '&&':   'q/and',
    '||':   'q/or' }

class Condition:
    """
        A representation of a Fibery condition
    """
    def __init__(self, cond_type, ops):
        self.ops = (ops)
        self.type = cond_type
      
    def _toStr(op):
        if isinstance(op, str):
            return op
        elif isinstance(op, int):
            return str(op)
        elif isinstance(op, Condition):
            return op.toStr()
        elif isinstance(op, Field):
            return op.name()
        else:
            return "<unknown>"

    def toStr(self):
        return "{} {} {}".format(Condition._toStr(self.ops[0]),
                                 self.type, 
                                 Condition._toStr(self.ops[1]))

    def where(self, values):
        query = [self.type]
        for op in self.ops:
            if isinstance(op, str):
                key = "$value{}".format(len(values)+1)
                values[key] = op
                query.append(key)

            elif isinstance(op, int):
                key = "$value{}".format(len(values)+1)
                values[key] = str(op) 
                query.append(key)
            
            if isinstance(op, Field):
                arg = [op.name()]
                if not op.isPrimitive():
                    texts = op.texts()
                    if len(texts):
                        arg.append(texts[0])
                query.append(arg)

            elif isinstance(op, Condition):
                q, v = op.where(values)
                query.append(q)

        return query, values 

    def __str__(self):
        return self.__rep__()

    def __rep__(self):
        return "<Condition {}>".format(self.toStr())


def EqCondition(Condition):
    """
        A representation of a Fibrary query Eq condition
    """


class Database(Object):
    """
        A representation of a Fibery database
    """
    def __init__(self, i, item=None, domain=None, token=None):
        self.item = item if item else Entity
        name, fid = _get_name_and_id(i) 
        if not fid and name:
            fid = Base.get_schema_by_name(self, name, domain=domain, token=token)
        super().__init__(fid, domain, token)
        self.database_name = self.info['fibery/name'] if self.info else 'Unknown'

    def __rep__(self):
        return "<{} database '{}'>".format(self.__class__.__name__, self._domain())

    def _get_info(self, fid):
        return self.get_schema_by_id(fid)

    def name(self):
        return self._attr('fibery/name')

    def query(self, select=[], query={}, params={}, limit=None):
        query['q/from'] = self.name()
        if len(select) == 0:
            fields = self.fields()
        else:
            fields = select

        #print("S", select, "Q", query, "P", params)

        query['q/select'] = []
        for f in fields:
            if isinstance(f, str):
                f = self.toField({'fibery/name': f})

            if isinstance(f, Field):
                query['q/select'].append(f.select())
            else:
                query['q/select'].append(f)

        query['q/limit'] = limit if limit else 'q/no-limit'
        return Base.query(self, 'fibery.entity/query', query=query, params=params)

    def query_by_fid(self, fid, select=[]):
        query={'q/where': ['=', [_FIBERY_id], '$fid']}
        params={'$fid': fid}
        r = self.query(select=select, query=query, params=params, limit=1)
        return r[0] if len(r) else None 

    def query_by_pid(self, pid, select=[]):
        query={'q/where': ['=', [_FIBERY_public_id], '$pid']}
        params={'$pid': str(pid)}
        r = self.query(select=select, query=query, params=params, limit=1)
        return r[0] if len(r) else None 

    def query_by_pids(self, pids, select=[]):
        query={'q/where': ['q/or', ['=', [_FIBERY_public_id], '$pid1'], 
                                    ['=', [_FIBERY_public_id], '$pid2']]}
        params={'$pid1': str(pids[0]), '$pid2': str(pids[1])}
        r = self.query(select=select, query=query, params=params, limit=3)
        return r

    def query_by_field(self, value, field, select=[], limit=None, exact=False):
        query={'q/where': ['=' if exact else 'q/contains', [field], '$value']}
        params={'$value': value}
        return self.query(select=select, query=query, params=params, limit=limit)

    def query_by_field_enum(self, value, field, select=[], limit=None, exact=False):
        query={'q/where': ['=', [field, 'enum/name'], '$value']}
        params={'$value': value}
        return self.query(select=select, query=query, params=params, limit=limit)

    def toItem(self, i):
        """
        Used to convert a record into an item class.
        """
        return self.item(i, domain=self.domain, token=self._token()) if i else None

    def toItems(self, items):
        return [self.toItem(i) for i in items]

    def byFiberyId(self, fid):
        """
        Used to look up an item class by Fibery ID
        """
        return self.toItem(self.query_by_fid(fid))

    def byId(self, fid):
        """
        Used to look up an item class by public ID
        """
        return self.toItem(self.query_by_pid(fid))

    def search_fields(self, f):
        """
        Used to retrieve the corresponding field entries. 
        """
        name, fid = _get_name_and_id(f)

        schema = self.get_schema_by_name(self.database_name)
        fields = schema['fibery/fields'] if schema else []
        if name and fid:
            fields = [f for f in fields if f['fibery/name'] == name and f[_FIBERY_id] == fid]
        elif name:
            fields = [f for f in fields if f['fibery/name'] == name]
        else:
            fields = [f for f in fields if f[_FIBERY_id] == fid]

        return fields

    def isField(self, f):
        """
        Used to determine if a given name is a field.
        """
        fields = self.search_fields({'fibery/name': f})
        return True if len(fields) else False

    def toField(self, f):
        """
        Used to convert a field record into a field class.
        """
        name, fid = _get_name_and_id(f)
        if name:
            fields = self.search_fields(f)

            f = fields[0] if len(fields) else None

        return Field(f, self.fid, domain=self.domain, token=self._token())

    def _fields(self):
        return [f for f in self.info['fibery/fields'] if f['fibery/deleted?'] == False]

    def fields(self):
        return [self.toField(f) for f in self._fields()]

    def num_fields(self):
        return len(self._fields())

    def unique_fields(self):
        return [_FIBERY_id]

    def addCondition(self, ctype, ops):
        ops = [self.toField(o) if self.isField(o) else o for o in ops]
        return Condition(ctype, ops) 

    def _parse(self, conds):
        if isinstance(conds, str):
            for op, val in _FIBERY_condition_ops.items():
                if op == conds:
                    return val

                elif op in conds:
                    ops = [o.strip() for o in conds.split(op)]
                    return self.addCondition(val, ops)

            raise Exception("Unrecognized term {}".format(conds))

        elif not isinstance(conds, list):
            return conds

        if len(conds) == 1:
            return self._parse(conds[0])

        for i in range(len(conds)):
            conds[i] = self._parse(conds[i])

        if len(conds) == 3:
            return self.addCondition(conds[1], [conds[0], conds[2]])

        return conds
                    
    def parseCondition(self, condition):
        c = nestedExpr('(', ')').parseString("({})".format(condition)).asList()
        return self._parse(c)


class Entity(Object):
    """
        A representation of an entity from a Fibery database
    """
    def __init__(self, entity, database, domain=None, token=None):
        self.database = database
        db = database(domain=domain, token=token) 
        if isinstance(entity, dict):
            if len(entity) < db.num_fields():
                for f in db.unique_fields():
                    if f in entity:
                        entity = (f,entity[f])
                        break

                    modified_f = f.split('/')[1] 
                    if modified_f in entity:
                        entity = (f,entity[modified_f])
                        break

        super().__init__(entity, domain, token)

    def db(self):
        return self.database(domain=self.domain, token=self._token())

    def _get_info(self, fid):
        db = self.db()
        fields = db.unique_fields()
        if isinstance(fid, tuple):
            fields = [fid[0]]
            fid = fid[1]

        for f in fields:
            r = db.query_by_field(fid, f, exact=True)
            if len(r) > 0:
                return r[0]


class Users(Database):
    """
    The class for interfacing with the Fibery Users.

    Arguments:
        [domain] -- The Fibery domain, will default to the local configuration.
        [token] -- The Fibery access token, will default to the local configuration.    
    """

    def __init__(self, domain=None, token=None):
        fid = Base.get_schema_by_name(self, 'fibery/user', domain=domain, token=token)
        super().__init__(fid, User, domain, token)

    def query(self, select=[], query={}, params={}, limit=None):
        return Database.query(self, select=select, query=query, params=params, limit=limit)

    def query_by_name(self, name, limit=None):
        return Database.query_by_field(self, name, 'user/name', domain=domain, limit=limit)

    def users(self, select=[], query={}, params={}, limit=None):
        if _FIBERY_id not in select:
            select.append(_FIBERY_id)

        users = self.query(select=select, query=query, params=params, limit=limit)
        return self.toItems(users) 

    def byName(self, name):
        """
        Used to look up a user by Name.
        """
        return self.toItems(self.query_by_name(name))


class User(Entity):
    """
    A class for interfacing with a single Fibery User. 
    
    Arguments:
        user_id -- The unique id of the User in Fibery.
        [domain] -- The Fibery domain, will default to the local configuration.
        [token] -- The Fibery access token, will default to the local configuration.
    """
    def __init__(self, fid, domain=None, token=None):
        super().__init__(fid, Users, domain, token)

    def name(self):
        """
        Returns the name of the user.
        """
        return self._attr('user/name')

    def email(self):
        """
        Returns the email of the user.
        """
        return self._attr('user/email')
    
    def prefix():
        return "FU"


RegisterDatabase(Users, User)


class Files(Database):
    """
    The class for interfacing with the Fibery Files.

    Arguments:
        [domain] -- The Fibery domain, will default to the local configuration.
        [token] -- The Fibery access token, will default to the local configuration.    
    """

    def __init__(self, domain=None, token=None):
        fid = Base.get_schema_by_name(self, 'fibery/file', domain=domain, token=token)
        super().__init__(fid, File, domain, token)

    def query_by_secret(self, secret):
        r = Database.query_by_field(self, secret, 'fibery/secret', exact=True) 
        return r[0] if len(r) else None

    def bySecret(self, fid):
        """
        Used to look up a file by secret.
        """
        return self.toItem(self.query_by_secret(fid))

    def byFilename(self, name):
        """
        Used to retrieve all files of a given name.
        """
        return self.toItems(Database.query_by_field(self, name, 'fibery/name', exact=True))

    def unique_fields(self):
        return [_FIBERY_id, 'fibery/secret']

    def files(self):
        return self.toItems(Database.query(self)) 


class File(Entity):
    def __init__(self, f, domain=None, token=None):
        super().__init__(f, Files, domain, token)

    def filename(self):
        return self.name()

    def name(self):
        return self._attr('fibery/name')

    def set_name(self, name):
        self._set_attr('fibery/name', name)

    def secret(self):
        return self._attr('fibery/secret')

    def content_type(self):
        return self._attr('fibery/content-type')

    def download(self, output=None):
        url = "{}/files/{}".format(self._api(self._domain()), self.secret())
        if not output:
            output=self.filename()

        return _download(self.get(url, stream=True), output=output) 

    def upload(self):
        url = "{}/files".format(self._api(self._domain()))
        files = {'file': self.name()}
        result = self.postJSON(url, headers={}, files=files)

        if result and 'fibery/secret' in result:
            self.info = result
            self.fid = result[_FIBERY_id]
            return True

        return False


class CommonEntity(Entity):
    def __init__(self, b, database, domain=None, token=None):
        super().__init__(b, database, domain, token)

    def link(self):
        return "{}/{}/{}".format(self._url(self._domain()), self.db().database_name.replace(' ', '_'), CommonEntity.id(self))

    def title(self):
        return self.name()

    def files(self):
        if not self.info:
            return []

        db = Files(domain=self._domain(), token=self._token())
        return [db.toItem(f) for f in self.info['Files/Files']]

    def attach_files(self, files):
        if not isinstance(files, list):
            files = [files]

        file_ids = [{_FIBERY_id: f.fid} for f in files]
        return self.db().add('Files/Files', self.fid, file_ids)


def addSecret(secrets, mapping, key, secret, fid, pid):
    secrets.append(secret)
    if secret not in mapping:
        mapping[key] = {}

    mapping[secret] = (fid, pid, key)


def _terms_inside(terms, line):
    for t in terms:
        if t not in line:
            return False

    return True


class CommonDatabase(Database):
    def __init__(self, item, name, domain=None, token=None):
        fid = Base.get_schema_by_name(self, name, domain=domain, token=token)
        super().__init__(fid, item, domain, token)

    def unique_fields(self):
        return super().unique_fields() + [_FIBERY_public_id]

    def search(self, terms):
        if isinstance(terms, str):
            terms = [terms]

        text_type = _FIBERY_text_type

        results = {}
        params = {}
        for i in range(len(terms)):
            params['$value{}'.format(i)] = terms[i]

        fields = self.fields()
        for t in [f for f in fields if f.type() == _FIBERY_text_type]:
            name = t.name()

            match=[] 
            for i in range(len(terms)):
                match.append(['q/contains', [name], '$value{}'.format(i)])

            if len(terms) == 1:
                query={'q/where': match[0]}
            else:
                query={'q/where': ['q/and'] + match}

            for r in Database.query(self, select=[_FIBERY_id, _FIBERY_public_id, name], query=query, params=params):
                pid = r[_FIBERY_public_id]
                if pid in results:
                    results[pid][name] = r[name]
                else:
                    results[pid] = r

        doc_fields = [f.name() for f in fields if f.type() in ['Collaboration~Documents/Document', 'comments/comment']]

        secrets = []
        smap = {}
        n_items = 0
        for i in self.query(select=[_FIBERY_id, _FIBERY_public_id] + doc_fields):
            fid = i[_FIBERY_id]
            pid = i[_FIBERY_public_id]

            n_items = n_items + 1
            for s in i['comments/comments']:
                addSecret(secrets, smap, 'comment/comments', s['comment/document-secret'], fid, pid)

            for k in i.keys():
                if isinstance(i[k], dict) and 'Collaboration~Documents/secret' in i[k]:
                    addSecret(secrets, smap, k, i[k]['Collaboration~Documents/secret'], fid, pid)

        docs = Documents().getContentBySecrets(secrets)
        filtered = [d['secret'] for d in docs if _terms_inside(terms, d['content'].lower())]
    
        for f in filtered:
            fid = smap[f][0]
            pid = smap[f][1]
            key = smap[f][2]

            c = [r['content'] for r in docs if r['secret'] == f]
            c = [l for l in c[0].split("\n") if _terms_inside(terms, l.lower())]
            if pid not in results:
                results[pid] = {_FIBERY_public_id: pid, _FIBERY_id: fid, key: c}
            elif key not in results[pid]:
                results[pid][key] = c
            else:
                results[pid][key] = results[pid][key] + c

        return results


def Search(criteria, domain=None, token=None):
    db = CommonDatabase(None, name='Product Management/Story', domain=domain, token=token)
    os.putenv("FB_DEBUG", "True")
    os.environ['FB_DEBUG'] = 'True'
    print("DEBUG", db._debug())
    results = db.query()


def getDatabase(name, domain=None, token=None):
    if isinstance(name, str):
        for tag in _databases.keys():
            if tag == name:
                return _databases[tag][0](domain=domain, token=token)

    return None


def getDatabases(name, domain=None, token=None):
    if name:
        return [getDatabase(name, domain=domain, token=token)]

    return [getDatabase(t) for t in _database.keys()]


def getDatabaseNames():
    return [k for k in _database.keys() if k != '#']


def getItem(pid, domain=None, token=None):
    if isinstance(pid, str):
        for tag in _databases.keys():
            length = len(tag)
            if pid.startswith(tag) and pid[length:].isnumeric():
                return getDatabase(tag).byId(pid[length:])

        print("Format of {} is not understood".format(pid))
        exit(1)
    elif isinstance(pid, int):
        return _databases['#'][0](domain=domain, token=token).byId(pid)
    else:
        return getItem(str(pid))

