from msbase import *
import json
import re

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

class MSDriveBase(MSGraphBase):
    def __init__(self, application,
                 credentials=None, driveId=None, debug=False, parent=None, info=None):
        self.parent = parent
        self._name = info['name'] if info and 'name' in info else None
        self._cache = {}
        self.driveId = driveId
    
        MSGraphBase.__init__(self, application, credentials=credentials, debug=debug)
    
    def endpoint(self):
        if self.driveId:
            return MSGraphBase.endpoint(self, path='drives/{}'.format(self.driveId))
        
        return MSGraphBase.endpoint(self) + '/drive'

    def driveId(self):
        if not self.driveId:
            pinfo = self.attr('parentReference')
            drive_id = pinfo['driveId'] if 'driveId' in pinfo else None

        return self.driveId
    
    def infoById(self, msid, fields=['*']):
        return self.get(props={'select': ','.join(fields)})

    def attr(self, prop):
        info = self.infoById(self.msid)
        return info[prop] if prop in info else None

    def parent(self):
        if self.parent:
            return self.parent
        pinfo = self.attr('parentReference')
        return self.toFolder(pinfo) if 'id' in pinfo else None

    def name(self):
        self._name = self.attr('name')
        return self._name
    
    def path(self):
        pinfo = self.attr('parentReference')
        if 'path' in pinfo:
            return pinfo['path'].replace('/drive/root:', '/')

        return None
    
    def fullPath(self, filter=None):
        return self.path() + '/' + (self._name if self._name else self.name())
    
    def loc(self):
        info = self.infoById(self.msid, fields=['parentReference', 'name'])
        path = info['parentReference']['path'].replace('/drive/root:', '/')
        return os.path.join(path, info['name'])

    def getViewUrl(self):
        return self.attr('@microsoft.graph.downloadUrl')
    
    def __str__(self):
        return self.__rep__()

    def toFile(self, item, parent=None):
        return MSFile(self.application, msid=item['id'],
                      driveId=self.driveId,
                      credentials=self.credentials,
                      debug=self.debug, parent=parent, info=item)
    
    def toFolder(self, item, parent=None):
        return MSFolder(self.application, msid=item['id'],
                        driveId=self.driveId,
                        credentials=self.credentials,
                        debug=self.debug, info=item, parent=parent)

    def toContents(self, items):
        results = []
        for i in items:
            if not isinstance(i, dict):
                results.append(i)
                continue
            
            if 'file' in i:
                results.append(self.toFile(i))
            else:
                results.append(self.toFolder(i))

        return results

    def getRootFolder(self):
        return MSRootFolder(self.application,
                            driveId=self.driveId,
                            credentials=self.get_credentials(),
                            debug=self.debug)   

class MSDriveItem(MSDriveBase):
    def __init__(self, msid, application, credentials=None, driveId=None, debug=False, parent=None, info=None):
        self.msid = msid
        self.parent = parent
        MSDriveBase.__init__(self, application, credentials=credentials, driveId=driveId, debug=debug, parent=parent, info=info)
        if msid and '@' in msid:
            ids = msid.split('@')
            self.msid = ids[0]
            self.drive_id = ids[1]

    def id(self):
        return self.msid

    def driveId(self):
        if not self.drive_id:
            pinfo = self.attr('parentReference')
            self.drive_id = pinfo['driveId'] if 'driveId' in pinfo else None

        return self.drive_id
    
    def fid(self):
        return '{}@{}'.format(self.msid, self.driveId())

    def endpoint(self):
        return MSDriveBase.endpoint(self) + '/items/{}'.format(self.msid)
    
    def root(self):
        return MSRootDrive(self.application, credentials=self.credentials, debug=self.debug)
        
    def set_domain_permission(self, role='reader', domain=None):
        data = {'type': 'edit',
                'scope': 'organization'}
        return self.post(self.endpoint()+'/createLink', data=data)

    def permissions(self):
        return self.get(self.endpoint()+'/permissions')
    
class MSContainer(MSDriveItem):
    def __init__(self, msid, application, credentials=None, driveId=None, debug=False, parent=None, info=None):
        MSDriveItem.__init__(self, msid, application, credentials=credentials, driveId=driveId, debug=debug, parent=parent, info=info)

    def isFolder(self):
        return True

    def isRoot(self):
        return self.isFolder() and self.msid is None
    
    def _children_endpoint(self):
        return self.endpoint() + "/children"

    def search(self, param={}):
        return MSDrive.activeSearch(self, resolveQ(param, None))   
    
    def createFolder(self, name):
        body = { 'name': name, 'folder': {} }
        result = self.post(self._children_endpoint(), data=body)
        if 'id' in result:
           return self.toFolder({'id': result['id'], 'name': name})

        id = self.id()
        items = self.get(self.endpoint() +'/search(q=\'{}\')'.format(name))
        for v in items['value']:
            if 'folder' not in v:
                continue
            
            if v['name'] != name:
                continue

            if v['parentReference']['id'] != id:
                continue

            return self.toFolder(v)
                 
    def list(self):
        info = self.get(endpoint=self._children_endpoint())
        return self.toContents(info['value'])

    def search(self, query=None):
        if query is None:
            return self.list()

        if len(query) == 0:
            return self.list()

        if len(query) == 1 and 'name' in query and query['name'] == '*':
            return self.list()
        
        params={}
        endpoint=self._children_endpoint()
        
        # TODO: Handle multiple string matches in the same query
        if 'name' in query or 'text' in query:
            endpoint= self.endpoint + '/search(q=\'{}\')'.format(query['name'] if 'name' in query else '*')
            
        for k, v in query.items():
            if k == 'q':
                continue

            if '$filter' in params:
                params['$filter'] += ' and '

            if k == 'file':
                params['$filter'] += ('file' if v else 'folder') + ' ne null'
            elif k == 'folder':
                params['$filter'] += ('folder' if v else 'file') + ' ne null'
            elif k == 'deleted':
                params['$filter'] += 'deleted ' + ('eq' if v else 'ne') + ' null'
            #TODO add more
        
        info = self.get(endpoint=endpoint, props=params)
        contents = info['value']
        if 'name' in query and '*' not in query['name']:
            p = get_patterm(query['name'])
            contents = [c for c in contents if p.match(c['name'])]
        
        return self.toContents(contents)

    def activeSearch(self, query=None):
        return self.search((query if query else {}).merge({'deleted': False}))
    
    def getItems(self, query=None):
        criteria = {'fields': ['id', 'name', 'mimeType', 'shortcutDetails', 'sharedWithMeTime']}
        if query:
            criteria['q'] = query
            

        items = self.search(criteria)
        r = self.toContents(items)
        if False and self.isRoot():
            r.append(MSShared(application=self.application,
                              credentials=self.credentials))

        return r
    
    def getItemsByPattern(self, pattern):
        query = {}
        if pattern:
            query['name'] = pattern

        pattern = get_pattern(pattern)
        return [r for r in self.getItems(query) if re.match(pattern, r._name)]

    def getFoldersByPattern(self, pattern):
        query = {}
        if pattern:
            query['name'] = pattern

        query['folder'] = True
        pattern = get_pattern(pattern)
        return [r for r in self.getItems(query) if re.match(pattern, r._name)]        
    
    def resolve(self, paths, create=False):
        if isinstance(paths, str):
            paths = os.path.normpath(paths).split(os.path.sep)

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

            dirs.sort(key=lambda x: x._name)
            for d in dirs:
                result += d.resolve(paths[1:], create=create)
        else:
            result = self.getItemsByPattern(paths[0])
            if len(result) == 0 and create:
                result = [self.createFolder(paths[0])]
            if len(result) == 0:
                return []

            result.sort(key=lambda x: x._name)

        return result
    
class MSFile(MSDriveItem):
    def __init__(self, application, msid=None, path=None, credentials=None, driveId=None, debug=False, info=None, parent=None):
        if not msid and info:
            msid=info['id']
            
        MSDriveItem.__init__(self, msid, application, credentials=credentials, driveId=driveId, debug=debug, parent=parent, info=info)

    def download(self, quiet=None, mimeType=None, output=None):
        return True
        
    def __rep__(self):
        return "<MSFile: {} ({})>".format(self._name if self._name else self.name(), self.msid)

class MSFolder(MSContainer):
    def __init__(self, application, msid=None, path=None, credentials=None, driveId=None, debug=False, info=None, parent=None):
        if not msid and info:
            msid=info['id']
            
        MSContainer.__init__(self, msid, application, credentials=credentials, driveId=driveId, debug=debug, parent=parent, info=info)
        self.drive_id = info['driveId'] if info and 'driveId' in info else None
    
    def __rep__(self):
        return "<MSFolder: {} ({})>".format(self._name if self._name else self.name(), self.msid)

    
    
class MSDrive(MSDriveBase):
    def __init__(self, application, driveId=None, path=None, credentials=None, debug=False):
        if not driveId:
            driveId = os.getenv('MS_DRIVE_ID', driveId)
        MSDriveBase.__init__(self, application, driveId=driveId, credentials=credentials, debug=debug)

    def driveId(self):
        if not self.driveId:
            result = self.get(props={'$select': 'id'})
            self.driveId = result['id']

        return self.driveId

    def attr(self, prop):
        info = self.get()
        return info[prop] if prop in info else None
    
    def search(self, param={}):
        return self.getRootFolder().search(param=param)

    def activeSearch(self, param={}):
        return self.getRootFolder().activeSsearch(param=param)  
    
    def resolve(self, path, create=False):
        return self.getRootFolder().resolve(path, create=create)

    def getFileById(self, id):
        return MSFile(self.application, id, credentials=self.credentials, debug=self.debug)
    
class MSRootFolder(MSContainer):
    def __init__(self, application, credentials=None, driveId=None, debug=False):
        MSContainer.__init__(self, None, application, driveId=driveId, credentials=credentials, debug=debug)

    def id(self):
        if not self.msid:
            result = self.get(props={'$select': 'id'})
            self.msid = result['id'] if 'id' in result else None

        return self.msid

    def endpoint(self):
        return MSDriveBase.endpoint(self) + '/root'

