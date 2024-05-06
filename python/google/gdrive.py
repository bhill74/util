import os
import re
import pkg_resources
import sys
import io
import json
import pdb

# Local modules
import gbase
import gsheets

# External modules
sys.path.append(os.path.join(os.getenv('HOME'), 'lib', 'ext'))
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from apiclient import errors
from apiclient import http
from apiclient import discovery

DRIVE_URL_BASE = "drive.google.com/drive/u/0/"

MIME_TYPE_TXT = 'text/plain'
MIME_TYPES = {'folder': 'application/vnd.google-apps.folder',
              'sheet':  'application/vnd.google-apps.spreadsheet',
              'shortcut': 'application/vnd.google-apps.shortcut',
              '.txt':   MIME_TYPE_TXT,
              '.text':  MIME_TYPE_TXT,
              '.csv':   'text/csv',
              '.doc':   'applicaton/msword',
              '.docx':  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
              '.xls':   'application/vnd.ms-excel',
              '.xlsx':  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
              '.pdf':   'application/pdf',
              '.gz':    'application/gzip',
              '.gpg':   'application/gpg',
              '.htm':   'text/html',
              '.html':  'text/html',
              '.gif':   'image/gif',
              '.png':   'image/png',
              '.jpg':   'image/jpg'}

SHARED_NAME = "Shared with me"


def getMimeExt(mimeType):
    return list(MIME_TYPES.keys())[list(MIME_TYPES.values()).index(mimeType)]


def idIs(gid):
    return "id = '{}'".format(gid)


def typeIs(mtype):
    return "mimeType = '{}'".format(mtype)


def typeIsNot(mtype):
    eq_cmp = "mimeType != '"
    if isinstance(mtype, list):
        return eq_cmp + ("' and " + eq_cmp).join(mtype) + "'"
    elif isinstance(mtype, str):
        return "{}{}'".format(eq_cmp, mtype)

    return ''


def isFolder():
    return typeIs(MIME_TYPES['folder'])


def isShortcut():
    return typeIs(MIME_TYPES['shortcut'])


def isShared():
    return "sharedWithMe"


def isAnyFolder():
    return '{} and sharedWithMe = true'.format(isFolder())


def isNotFolder():
    return typeIsNot(MIME_TYPES['folder'])


def isNotFolderOrShortcut():
    return typeIsNot([MIME_TYPES['folder'], MIME_TYPES['shortcut']])


def nameIs(name):
    return "name = '{}'".format(name)


def nameContains(name):
    return "name contains '{}'".format(name)


def canonicalizeId(spreadsheetId):
    match = re.match(
            '^https?://{}(folders|file)/([^/]+)'.format(DRIVE_URL_BASE),
            spreadsheetId)

    if match:
        return match.groups()[1]

    return spreadsheetId


def resolveQ(param={}, q=None):
    if isinstance(param, str):
        param = {'q': param}
    elif isinstance(param, list):
        param = {'q': " and ".join(param)}
    elif not isinstance(param, dict):
        print("NOT SUPPORTED", param)

    if q:
        if 'q' in param:
            param['q'] = "{} and {}".format(q, param['q'])
        else:
            param['q'] = q

    return param


def get_pattern(pattern):
    return re.compile('^{}$'.format(re.sub('\\*', '.+', pattern)))


def _mkdir(path):
    if not os.path.exists(path):
        os.mkdir(path)


_format_pattern = re.compile('\033\[((\d+;)*?\d+)?m')


def _format_code(*codes):
    """Escapes the formatting code"""
    return '\033[{}m'.format(";".join([str(c) for c in codes]))


def _format_str(text, *codes):
    if len(codes) == 0:
        return text

    return _format_code(*codes) + text + _format_code()


def _remove_formatting(text):
    return re.sub(_format_pattern, '', text)


def _add_path(paths, new_paths, name):
    for p in paths:
        new_paths.append(os.path.join(name, p) if len(p) else name)


def transferMsg(gfile, name):
    gfile = gfile if isinstance(gfile, GFile) \
        else GFile(gfile['id'], gfile['name'])
    print("{} --> {}/{}".format(gfile.getPaths()[0], os.getcwd(), name))


class GDriveBase(gbase.GoogleAPI):
    def __init__(self, scope, application="drive",
                 client_file=None, credentials=None, service=None):
        if not client_file:
            client_file = \
                pkg_resources.resource_filename(__name__, "drive_client_id.json")
            client_file = os.getenv("GOOGLE_DRIVE_CLIENT_ID", client_file)

        scopes = ('.metadata.readonly', '.file', '')
        gbase.GoogleAPI.__init__(self, "drive",
                                 ["auth/drive{}".format(s) for s in scopes],
                                 client_file, application,
                                 credentials=credentials,
                                 service=service)

    def batch(self):
        return self.get_service().new_batch_http_request(calllback=callback)

    def get_service(self):
        if not self.service:
            self.service = \
                discovery.build(self.api, 'v3',
                                credentials=self.get_credentials())

        return self.service

    def get_permission_ids(self):
        r = self.service.permissions().list(fileId=self.gid).execute()
        if 'permissions' in r:
            return r['permissions']
        return None

    def get_permissions(self):
        return self.infoById(self.gid, ['capabilities'])

    def get_domain(self):
        owners = self.infoById(self.gid, ['owners'])
        if 'owners' in owners:
            for o in owners['owners']:
                domain = o['emailAddress'].split('@')[1]
                return domain

        return None

    def set_domain_permission(self, role='reader', domain=None):
        domain = domain if domain else self.get_domain()

        permission = {
            'type': 'domain',
            'role': role,
            'domain': domain
        }
        r = self.get_service().permissions().create(fileId=self.gid,
                                              body=permission,
                                              fields='id').execute()
 
    def get_files(self):
        return self.get_service().files()

    def infoById(self, gid, fields=['*']):
        try:
            return self.get_files().get(fileId=gid,
                                        fields=",".join(fields)).execute()
        except Exception as e:
            return None

    def toItems(self, items, parent=None):
        results = []
        for i in items:
            if i['mimeType'] == MIME_TYPES['folder']:
                results.append(self.toFolder(i, parent))
            elif i['mimeType'] == MIME_TYPES['shortcut']:
                results.append(self.toShortcut(i, parent))
            else:
                results.append(self.toFile(i, parent))

        return results

    def toFile(self, item, parent=None):
        return GFile(item['id'], item['name'],
                     application=self.application,
                     credentials=self.get_credentials(),
                     service=self.get_service(),
                     parent=parent)

    def toFiles(self, results, parent=None):
        return [self.toFile(r, parent) for r in results]

    def toShortcut(self, item, parent=None):
        gid = None
        shortcutId = item['id'] if 'id' in item else None
        mimeType = None
        if 'shortcutDetails' not in item:
            i = self.infoById(shortcutId, ['shortcutDetails'])
            item = dict(item, **i)

        if 'shortcutDetails' in item:
            details = item['shortcutDetails']
            gid = details['targetId'] if 'targetId' in details \
                else gid
            mimeType = details['targetMimeType'] if 'targetMimeType' in details \
                else mimeType

        return GShortcut(gid, shortcutId,
                         name=item['name'] if 'name' in item else '',
                         mimeType=mimeType,
                         application=self.application,
                         credentials=self.get_credentials(),
                         service=self.get_service(),
                         parent=parent)

    def toShortcuts(self, results, parent=None):
        return [self.toShortcut(r, parent) for r in results]

    def toFolder(self, item, parent=None):
        return GFolder(item['id'], name=item['name'],
                       application=self.application,
                       credentials=self.get_credentials(),
                       service=self.get_service(),
                       parent=parent)

    def toFolders(self, results, parent=None):
        return [self.toFolder(r, parent) for r in results]

    def uniqueName(self, path, unique=False):
        return path if not unique else "{}:{}".format(path, self.gid)

    def getRootFolder(self):
        return GFolder('root',
                       application=self.application,
                       credentials=self.get_credentials(),
                       service=self.get_service())

    def getShared(self):
        return GShared(application=self.application,
                       credentials=self.get_credentials(),
                       service=self.get_service())


class GItem(GDriveBase):
    def __init__(self, gid, name='',
                 application=None,
                 client_file=None,
                 credentials=None,
                 service=None,
                 parent=None):
        self.gid = gid
        self.name = name
        self.parents = [parent] if parent else []
        GDriveBase.__init__(self, "",
                            application=application,
                            client_file=client_file,
                            credentials=credentials,
                            service=service)

    def isFile(self):
        return False

    def isFolder(self):
        return False

    def isShortcut(self):
        return False

    def isShared(self):
        return False

    def isRoot(self):
        return False

    def formatName(self):
        return self.name

    def getParents(self):
        if len(self.parents):
            return self.parents

        parents = self.infoById(self.gid, ['parents'])
        if not parents or len(parents) == 0:
            return []

        results = [self.infoById(g, ['id', 'name'])
                   for g in parents['parents']]
        return self.toFolders(results)

    def remove(self):
        self.get_files().delete(fileId=self.gid).execute()

    def _add_node(self, path):
        if self.isRoot():
            return [path]

        path.insert(0, self.formatName())
        if self.isShared():
            return [path]

        parents = self.getParents()
        if parents and len(parents):
            r = []
            for p in parents:
                r += p._add_node(path[:])

            return r

        if not self.isShortcut():
            i = self.infoById(self.gid, ['sharedWithMeTime'])
            if i and 'sharedWithMeTime' in i:
                return self.getShared()._add_node(path)

        return []

    def getPaths(self, cache={}):
        if self.isRoot():
            return []

        return [os.path.join(*p) for p in self._add_node([])]

    def fullPath(self, filter=None, unique=False, cache={}):
        if filter and len(os.path.split(filter)) <= 1:
            return self.uniqueName(self.name, unique)

        paths = self.getPaths(cache={})
        if filter:
            pat = get_pattern(filter)
            paths = [p for p in paths
                     if pat.match(_remove_formatting(p))]

        if len(paths) == 0:
            return ''

        return os.path.join(paths[0], ' ') if self.isFolder() \
            else paths[0]


class GFile(GItem):
    def __init__(self, gid, name,
                 application=None,
                 client_file=None,
                 credentials=None,
                 service=None,
                 parent=None):
        GItem.__init__(self, gid, name=name,
                       application=application,
                       client_file=client_file,
                       credentials=credentials,
                       service=service,
                       parent=parent)

    def isFile(self):
        return True

    def __rep__(self):
        return "<GFile: {} ({})>".format(self.name, self.gid)

    def __str__(self):
        return self.__rep__()

    def formatName(self):
        return self.name

    def text(self):
        result = self.get_files().export(fileId=self.gid,
                                         mimeType=MIME_TYPE_TXT).execute()
        return result.decode('utf-8')

    def export(self, mimeType=None, info=None, output=None, quiet=False):
        info = info if info else self.infoById(self.gid, ['name', 'mimeType'])
        name = output if output else info['name']
        if not mimeType:
            fname, ext = os.path.splitext(name)
            if ext in MIME_TYPES:
                mimeType = MIME_TYPES[ext]
            else:
                mimeType = MIME_TYPE_TXT
        else:
            fname, ext = os.path.splitext(name)
            if ext == '':
                ext = getMimeExt(mimeType)
                name = fname + ext

        if MIME_TYPES['sheet'] == info['mimeType']:
            sheet = self.toSheet()
            try:
                sheet.export(mimeType=mimeType, output=output, quiet=quiet)
                return
            except gsheets.IncompatibleFormat:
                if mimeType == MIME_TYPES['.xls']:
                    ext = '.xlsx'
                elif mimeType == MIME_TYPES['.doc']:
                    ext = '.docx'

                mimeType = MIME_TYPES[ext] if ext in MIME_TYPES \
                    else MIME_TYPES['.csv']
                name = "{}{}".format(fname, ext)

        if not quiet:
            transferMsg(self, name)

        result = self.get_files().export(fileId=self.gid,
                                         mimeType=mimeType).execute()
        fd = open(name, 'wb')
        fd.write(result)
        fd.close()

        if not quiet:
            print('  Export Complete')

    def download(self, mimeType=None, output=None, quiet=False):
        info = self.infoById(self.gid, ['name', 'mimeType'])
        if 'google-apps' in info['mimeType']:
            self.export(output=output, quiet=quiet, mimeType=mimeType)
            return

        request = self.get_files().get_media(fileId=self.gid)
        name = output if output else info['name']

        if not quiet:
            transferMsg(self, name)

        fd = open(name, 'wb')
        media_request = http.MediaIoBaseDownload(fd, request)
        while True:
            try:
                progress, done = media_request.next_chunk()
            except errors.HttpError as error:
                if not quiet:
                    print('An error occurred: %s' % error)
                return
            if progress:
                if not quiet:
                    print('  Download Progress: %d%%'
                          % int(progress.progress() * 100))
            if done:
                if not quiet:
                    print('  Download Complete')
                return

    def getDownloadUrl(self):
        links = self.infoById(self.gid, ['webContentLink'])
        if 'webContentLink' in links:
            return links['webContentLink']

        return None

    def getViewUrl(self):
        links = self.infoById(self.gid, ['webViewLink'])
        if 'webViewLink' in links:
            return links['webViewLink']

        return None

    def getMimeType(self):
        links = self.infoById(self.gid, ['mimeType'])
        if 'mimeType' in links:
            return links['mimeType']

        return None

    def getData(self):
        return self.get_files().get_media(fileId=self.gid).execute()

    def update(self, info={}):
        body = self.get_files().get(fileId=self.gid).execute()
        body.pop('id')

        # Combine meta-data
        body.update(info)

        # File's new content.
        media_body = MediaIoBaseUpload(body['stream'],
                                       mimetype=body['mimeType'],
                                       resumable=True)

        # Send the request to the API.
        body.pop('stream')
        update = self.get_files().update(
            fileId=self.gid,
            body=body,
            media_body=media_body).execute()
        if 'id' not in update or update['id'] != self.gid:
            print("There has been a problem ({})".format(str(update)))

    def append(self, content):
        data = self.get_files().export(fileId=self.gid,
                                       mimeType=MIME_TYPE_TXT).execute()
        newLine = bytearray("\n".encode())

        if 'stream' in content:
            content['stream'].seek(0, os.SEEK_SET)
            data += newLine + content['stream'].read()
        elif 'file' in content:
            fd = open(content['file'], 'rb')
            data += newLine + bytearray(fd.read().encode())
            content.pop('file')

        content['stream'] = io.BytesIO()
        content['stream'].write(data)
        self.update(content)

    def getMetaData(self):
        return self.infoById(self.gid)

    def toSheet(self):
        return gsheets.GSpreadsheet(self.gid, self.name,
                                    application=self.application)


class GContainer(GItem):
    def __init__(self, gid, name,
                 application=None,
                 client_file=None,
                 credentials=None,
                 service=None,
                 parent=None):
        GItem.__init__(self, gid, name=name,
                       application=application,
                       client_file=client_file,
                       credentials=credentials,
                       service=service,
                       parent=parent)

    def isFolder(self):
        return True

    def isRoot(self):
        return self.isFolder() and self.gid == 'root'

    def _base(self):
        return None

    def search(self, param={}):
        return GDrive.activeSearch(self, resolveQ(param, self._base()))

    def getItems(self, query=None):
        criteria = {'fields': ['id', 'name', 'mimeType', 'shortcutDetails', 'sharedWithMeTime']}
        if query:
            criteria['q'] = query

        items = self.search(criteria)
        r = self.toItems(items, self)
        if self.isRoot():
            r.append(GShared(application=self.application,
                             credentials=self.get_credentials(),
                             service=self.get_service()))

        return r

    def getItemsByPattern(self, pattern):
        query = None
        if pattern:
            query = "name contains '{}'".format(pattern)

        pattern = get_pattern(pattern)
        return [r for r in self.getItems(query) if re.match(pattern, r.name)]

    def getFiles(self):
        return self.toFiles(self.search(isNotFolderOrShortcut()), self) + \
            self.getShortcutsByNotType(MIME_TYPES['folder'])

    def getFilesByName(self, name):
        terms = [isNotFolderOrShortcut(), nameIs(name)]
        return self.toFiles(self.search(terms), self)

    def getFilesContainsName(self, name):
        terms = [isNotFolderOrShortcut(), nameContains(name)]
        return self.toFiles(self.search(terms))

    def getFilesByType(self, mtype):
        terms = [isNotFolderOrShortcut(), typeIs(mtype)]
        return self.toFiles(self.search(terms))

    def getFilesByPattern(self, pattern):
        pattern = get_pattern(pattern)
        return [f for f in self.getFiles() if re.match(pattern, f.name)]

    def getShortcuts(self):
        p = {'q': isShortcut(), 'fields': ['id', 'name', 'shortcutDetails']}
        return self.toShortcuts(self.search(p), self)

    def getShortcutsByType(self, mimeType):
        return [s for s in self.getShortcuts() if s.mimeType == mimeType]

    def getShortcutsByNotType(self, mimeType):
        return [s for s in self.getShortcuts() if s.mimeType != mimeType]

    def getFolders(self):
        return self.toFolders(self.search(isFolder()), self) + \
            self.getShortcutsByType(MIME_TYPES['folder'])

    def getFoldersByName(self, name):
        terms = [isFolder(), nameIs(name)]
        return self.toFolders(self.search(terms), self)

    def getFoldersByPattern(self, pattern):
        pattern = get_pattern(pattern)
        return [f for f in self.getFolders() if re.match(pattern, f.name)]

    def resolve(self, paths, create=False, debug=None):
        if isinstance(paths, str):
            paths = os.path.normpath(paths).split(os.path.sep)

        if debug:
            print("resolve(): Paths ", paths)

        size = len(paths)
        if size == 0:
            return [self]

        if paths[0] == '':
            return [self] if size == 1 else \
               self.resolve(paths[1:], create=create)

        result = []
        if size > 1:
            dirs = self.getFoldersByPattern(paths[0])
            if len(dirs) == 0 and create:
                dirs = [self.createFolder(paths[0])]
            if len(dirs) == 0:
                return []

            dirs.sort(key=lambda x: x.name)
            for d in dirs:
                result += d.resolve(paths[1:], create=create)

        else:
            result = self.getItemsByPattern(paths[0])
            if len(result) == 0 and create:
                result = [self.createFolder(paths[0])]
            if len(result) == 0:
                return []

            result.sort(key=lambda x: x.name)

        return result

    def download(self, output=None, quiet=False):
        cwd = os.getcwd()
        if output:
            _mkdir(output)
            os.chdir(output)

        _mkdir(self.name)
        os.chdir(self.name)

        for f in self.getFolders():
            f.download(quiet=quiet)

        for f in self.getFiles():
            f.download(quiet=quiet)

        os.chdir('..')

        if output:
            os.chdir(cwd)

    def createFile(self, name, content):
        mimeType = content['mimeType'] if 'mimeType' in content \
                else None

        if not mimeType:
            fname, ext = os.path.splitext(name)
            ext = ext.lower()
            if ext in MIME_TYPES:
                mimeType = MIME_TYPES[ext]
            else:
                mimeType = MIME_TYPE_TXT

        body = {'name': name, 'parents': [self.gid], 'mimeType': mimeType}

        if 'file' in content:
            media = MediaFileUpload(content['file'],
                                    mimetype=mimeType,
                                    resumable=True)
        elif 'stream' in content:
            content['stream'].seek(0, os.SEEK_SET)
            media = MediaIoBaseUpload(content['stream'],
                                      mimetype=mimeType,
                                      resumable=True)
        else:
            print("No known content type")
            return

        result = self.get_files().create(body=body,
                                         media_body=media,
                                         fields='id').execute()
        return self.toFiles([{'id': result['id'], 'name': name}], self)[0]

    def createFileFromStdin(self, name, content):
        content['stream'] = io.BytesIO()
        content['stream'].write(bytearray(sys.stdin.read().encode()))
        return self.createFile(name, content)

    def createFolder(self, name):
        body = {'name': name, 'parents': [self.gid],
                'mimeType': MIME_TYPES['folder']}
        result = self.get_files().create(body=body, fields='id').execute()
        return self.toFolder({'id': result['id'], 'name': name})


class GShared(GContainer):
    def __init__(self,
                 application=None,
                 client_file=None,
                 credentials=None,
                 service=None):
        GContainer.__init__(self, 'sharedWithMe', name=SHARED_NAME,
                            application=application,
                            client_file=client_file,
                            credentials=credentials,
                            service=service)

    def isShared(self):
        return True

    def formatName(self):
        return _format_str(self.name, 91)

    def _base(self):
        return 'sharedWithMe = true'

    def _prepend_path(self, path):
        path.prepend(self.formatName())
        return [path]

    def __str__(self):
        return "GShared: {} ({})".format(self.name, self.gid)


class GShortcut(GContainer):
    def __init__(self, gid, shortcutgid, name='', mimeType=None,
                 application=None, client_file=None, credentials=None, service=None,
                 parent=None):
        GContainer.__init__(self, gid, name=name,
                            application=application,
                            client_file=client_file,
                            credentials=credentials,
                            service=service,
                            parent=parent)
        self.shortcutgid = shortcutgid
        if not mimeType:
            i = self.infoById(gid, ['mimeType'])
            if i and 'mimeType' in i:
                mimeType = i['mimeType']

        self.mimeType = mimeType

    def isFile(self):
        return True if self.mimeType == MIME_TYPES['file'] else False

    def isFolder(self):
        return True if self.mimeType == MIME_TYPES['folder'] else False

    def isShortcut(self):
        return True

    def _base(self):
        return "'{}' in parents".format(self.gid) if self.isFolder() else None

    def formatName(self):
        return _format_str(self.name, 32)

    def __str__(self):
        return "GShortcut: {} ({})".format(self.name, self.gid)


class GFolder(GContainer):
    def __init__(self, gid, name='',
                 application=None,
                 client_file=None,
                 credentials=None,
                 service=None,
                 parent=None):
        GContainer.__init__(self, gid, name=name,
                            application=application,
                            client_file=client_file,
                            credentials=credentials,
                            service=service,
                            parent=parent)

    def _base(self):
        return "'{}' in parents".format(self.gid)

    def getFolders(self):
        f = GContainer.getFolders(self)
        if self.isRoot():
            f.append(GShared(application=self.application,
                             credentials=self.get_credentials(),
                             service=self.get_service()))

        return f

    def open(self):
        gbase.GoogleAPI.open(
                'https://{}/folders/%s'.format(DRIVE_URL_BASE) %
                self.gid)

    def __str__(self):
        return "GDrive: {} ({})".format(self.name, self.gid)


class GDrive(GDriveBase):
    def __init__(self, application=None):
        GDriveBase.__init__(self, ".metadata.readonly",
                            application=application)

    def byId(self, fileId, param={}):
        service = self.get_service()
        param = resolveQ(param)

        if 'fields' not in param:
            param['fields'] = 'id, name'
        else:
            f = param['fields']
            if isinstance(f, list):
                f = ", ".join(f)

            param['fields'] = f

        param['fileId'] = fileId

        response = service.files().get(fileId=fileId).execute()
        return response

    def search(self, param={}):
        service = self.get_service()
        param = resolveQ(param)

        if 'fields' not in param:
            param['fields'] = 'nextPageToken, files(id, name)'
        else:
            f = param['fields']
            if isinstance(f, list):
                f = ", ".join(f)

            param['fields'] = 'nextPageToken, files({})'.format(f)

        if 'q' not in param:
            param['q'] = "'root' in parents and trashed=false"

        results = []
        page_token = None
        while True:
            sys.stdout.flush()
            #print("PP", param)
            response = service.files().list(**param).execute()
            page_token = response.get('nextPageToken', None)
            results.extend(response.get('files', []))
            if page_token is None:
                break

            param['pageToken'] = page_token

        return results

    def activeSearch(self, param={}):
        return GDrive.search(self, resolveQ(param, "trashed=false"))

    def getFiles(self):
        return self.toFiles(self.activeSearch(isNotFolderOrShortcut()), self)

    def getFileById(self, gid):
        result = GDrive.byId(self, gid, {})
        if result and 'kind' in result and result['kind'] == 'drive#file':
            return self.toFile(result)

        return None

    def getFilesByName(self, name):
        terms = [isNotFolderOrShortcut(), nameIs(name)]
        return self.toFiles(self.activeSearch(terms), self)

    def getFilesContainsName(self, name):
        terms = [isNotFolderOrShortcut(), nameContains(name)]
        return self.toFiles(self.activeSearch(terms), self)

    def getFilesByType(self, mtype):
        terms = [isNotFolderOrShortcut(), typeIs(mtype)]
        return self.toFiles(self.activeSearch(terms), self)

    def getFolders(self):
        return self.toFolders(self.activeSearch(isFolder()), self)

    def getFolderById(self, gid):
        terms = [isFolderOrShortcut(), idIs(gid)]
        return self.toFolders(self.activeSearch(terms), self)

    def getFoldersByName(self, name):
        terms = [isFolderOrShortcut(), nameIs(name)]
        return self.toFolders(self.activeSearch(terms), self)

    def resolve(self, path, create=False, debug=None):
        return self.getRootFolder().resolve(path, create=create, debug=debug)

    def open(self):
        self.getRootFolder().open()

    def __str__(self):
        return "GDrive"
