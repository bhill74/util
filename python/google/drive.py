import webbrowser
import base
import os
import re
import pkg_resources
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from apiclient import errors
from apiclient import http
import sys
import io

DRIVE_URL_BASE = "drive.google.com/drive/u/0/"

MIME_TYPES = {'folder': 'application/vnd.google-apps.folder'}


def idIs(gid):
    return "id = '{}'".format(gid)


def typeIs(mtype):
    return "mimeType = '{}'".format(mtype)


def typeIsNot(mtype):
    return "mimeType != '{}'".format(mtype)


def isFolder():
    return typeIs(MIME_TYPES['folder'])


def isNotFolder():
    return typeIsNot(MIME_TYPES['folder'])


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


class GDriveBase(base.GoogleAPI):
    def __init__(self, scope, application="drive",
                 credentials=None, service=None):
        client_file = \
            pkg_resources.resource_filename(__name__, "drive_client_id.json")
        client_file = os.getenv("GOOGLE_DRIVE_CLIENT_ID", client_file)

        scopes = ('.metadata.readonly', '.file', '')
        base.GoogleAPI.__init__(self, "drive",
                                ["auth/drive{}".format(s) for s in scopes],
                                client_file, application,
                                credentials=credentials,
                                service=service)

    def get_files(self):
        return self.get_service().files()

    def infoById(self, gid, fields=[]):
        return self.get_files().get(fileId=gid,
                                    fields=",".join(fields)).execute()

    def toItems(self, items):
        results = []
        for i in items:
            if i['mimeType'] == MIME_TYPES['folder']:
                results.append(GFolder(i['id'], i['name'],
                               application=self.application,
                               credentials=self.get_credentials(),
                               service=self.get_service()))
            else:
                results.append(GFile(i['id'], i['name'],
                               application=self.application,
                               credentials=self.get_credentials(),
                               service=self.get_service()))

        return results

    def toFiles(self, results):
        return [GFile(r['id'], r['name'],
                      application=self.application,
                      credentials=self.get_credentials(),
                      service=self.get_service())
                for r in results]

    def toFolder(self, item):
        return GFolder(item['id'], name=item['name'],
                       application=self.application,
                       credentials=self.get_credentials(),
                       service=self.get_service())

    def toFolders(self, results):
        return [self.toFolder(r) for r in results]


class GItem(GDriveBase):
    def __init__(self, gid, name='',
                 application=None, credentials=None, service=None):
        self.gid = gid
        self.name = name
        GDriveBase.__init__(self, "",
                            application=application,
                            credentials=credentials,
                            service=service)

    def getParents(self):
        parents = self.infoById(self.gid, ['parents'])
        if len(parents) == 0:
            return []

        results = [self.infoById(g, ['id', 'name'])
                   for g in parents['parents']]
        return self.toFolders(results)

    def getPaths(self):
        paths = ['']
        dirs = [self]
        while len(dirs):
            result = []
            new_paths = []
            for d in dirs:
                for p in d.getParents():
                    result.append(p)

                    for p in paths:
                        if len(p):
                            p = "/{}".format(p)

                        new_paths.append("{}{}".format(d.name, p))

            dirs = result
            if len(result) == 0:
                break

            paths = new_paths

        return paths


class GFile(GItem):
    def __init__(self, gid, name,
                 application=None, credentials=None, service=None):
        GItem.__init__(self, gid, name=name,
                       application=application,
                       credentials=credentials,
                       service=service)

    def download(self, output=None):
        request = self.get_files().get_media(fileId=self.gid)
        name = output if output else self.infoBy(self.gid, ['name'])
        fd = open(name, 'wb')
        media_request = http.MediaIoBaseDownload(fd, request)
        while True:
            try:
                progress, done = media_request.next_chunk()
            except errors.HttpError as error:
                print('An error occurred: %s' % error)
                return
            if progress:
                print('Download Progress: %d%%'
                      % int(progress.progress() * 100))
            if done:
                print('Download Complete')
                return

    def remove(self):
        self.get_files().delete(fileId=self.gid).execute()

    def getParents(self):
        parents = self.infoById(self.gid, ['parents'])
        if len(parents) == 0:
            return []

        results = [self.infoById(g, ['id', 'name'])
                   for g in parents['parents']]
        return self.toFolders(results)

    def getDownloadUrl(self):
        links = self.infoById(self.gid, ['webContentLink'])
        if 'webContentLink' in links:
            return links['webContentLink']

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
                                       mimeType='text/plain').execute()
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

    def __str__(self):
        return "GFile: {} ({})".format(self.name, self.gid)


class GItem(GDriveBase):
    def __init__(self, gid, name='',
                 application=None, credentials=None, service=None):
        self.gid = gid
        self.name = name
        GDriveBase.__init__(self, "",
                            application=application,
                            credentials=credentials,
                            service=service)

    def getParents(self):
        parents = self.infoById(self.gid, ['parents'])
        if len(parents) == 0:
            return []

        results = [self.infoById(g, ['id', 'name'])
                   for g in parents['parents']]
        return self.toFolders(results)

    def getPaths(self):
        paths = ['']
        dirs = [self]
        while len(dirs):
            result = []
            new_paths = []
            for d in dirs:
                for p in d.getParents():
                    result.append(p)

                    for p in paths:
                        if len(p):
                            p = "/{}".format(p)

                        new_paths.append("{}{}".format(d.name, p))

            dirs = result
            if len(result) == 0:
                break

            paths = new_paths

        return paths


class GFolder(GItem):
    def __init__(self, gid, name='',
                 application=None, credentials=None, service=None):
        GItem.__init__(self, gid, name=name,
                       application=application,
                       credentials=credentials,
                       service=service)

    def search(self, param={}):
        base_q = "'{}' in parents".format(self.gid)
        return GDrive.activeSearch(self, resolveQ(param, base_q))

    def getItems(self):
        items = self.search({'fields': ['id', 'name', 'mimeType']})
        return self.toItems(items)

    def getItemsByPattern(self, pattern):
        pattern = get_pattern(pattern)
        items = self.search({'fields': ['id', 'name', 'mimeType']})
        return self.toItems([r for r in items if re.match(pattern, r['name'])])

    def getFiles(self):
        return self.toFiles(self.search(isNotFolder()))

    def getFilesByName(self, name):
        terms = [isNotFolder(), nameIs(name)]
        return self.toFiles(self.search(terms))

    def getFilesContainsName(self, name):
        terms = [isNotFolder(), nameContains(name)]
        return self.toFiles(self.search(terms))

    def getFilesByType(self, mtype):
        terms = [isNotFolder(), typeIs(mtype)]
        return self.toFiles(self.search(terms))

    def getFilesByPattern(self, pattern):
        pattern = get_pattern(pattern)
        return [f for f in self.getFiles() if re.match(pattern, f.name)]

    def getFolders(self):
        return self.toFolders(self.search(isFolder()))

    def getFoldersByName(self, name):
        terms = [isFolder(), nameIs(name)]
        return self.toFolders(self.search(terms))

    def getFoldersByPattern(self, pattern):
        pattern = get_pattern(pattern)
        return [f for f in self.getFolders() if re.match(pattern, f.name)]

    def createFile(self, name, content):
        mimeType = content['mimeType'] if 'mimeType' in content \
                else 'plain/txt'
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
        return self.toFiles([{'id': result['id'], 'name': name}])[0]

    def createFileFromStdin(self, name, content):
        content['stream'] = io.BytesIO()
        content['stream'].write(bytearray(sys.stdin.read().encode()))
        return self.createFile(name, content)

    def createFolder(self, name):
        body = {'name': name, 'parents': [self.gid],
                'mimeType': MIME_TYPES['folder']}
        result = self.get_files().create(body=body, fields='id').execute()
        return self.toFolder({'id': result['id'], 'name': name})

    def resolve(self, paths, create=False):
        if isinstance(paths, str):
            paths = paths.split('/')

        size = len(paths)
        if size == 0 or paths[0] == '':
            return [self]

        result = []
        if size > 1:
            dirs = self.getFoldersByPattern(paths[0])
            if len(dirs) == 0 and create:
                dirs = [self.createFolder(paths[0])]

            for d in dirs:
                result += d.resolve(paths[1:], create=create)
        else:
            result = self.getItemsByPattern(paths[0])
            if len(result) == 0 and create:
                result = [self.createFolder(paths[0])]

        return result

    def __str__(self):
        return "GDrive: {} ({})".format(self.name, self.gid)


class GDrive(GDriveBase):
    def __init__(self, application=None):
        GDriveBase.__init__(self, ".metadata.readonly",
                            application=application)

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
            #print(param)
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
        return self.toFiles(self.activeSearch(isNotFolder()))

    def getFileById(self, gid):
        terms = [isNotFolder(), idIs(gid)]
        return self.toFiles(self.activeSearch(terms))

    def getFilesByName(self, name):
        terms = [isNotFolder(), nameIs(name)]
        return self.toFiles(self.activeSearch(terms))

    def getFilesContainsName(self, name):
        terms = [isNotFolder(), nameContains(name)]
        return self.toFiles(self.activeSearch(terms))

    def getFilesByType(self, mtype):
        terms = [isNotFolder(), typeIs(mtype)]
        return self.toFiles(self.activeSearch(terms))

    def getFolders(self):
        return self.toFolders(self.activeSearch(isFolder()))

    def getFolderById(self, gid):
        terms = [isFolder(), idIs(gid)]
        return self.toFolders(self.activeSearch(terms))

    def getFoldersByName(self, name):
        terms = [isFolder(), nameIs(name)]
        return self.toFolders(self.activeSearch(terms))

    def getRootFolder(self):
        return GFolder('root',
                       application=self.application,
                       credentials=self.get_credentials(),
                       service=self.get_service())

    def resolve(self, path, create=False):
        return self.getRootFolder().resolve(path, create=create)

    def open(self, folder_id):
        webbrowser.open(
                'https://{}/folders/%s'.format(DRIVE_URL_BASE) %
                folder_id)

    def __str__(self):
        return "GDrive"
