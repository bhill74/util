import msbase

class MSInfo(msbase.MSGraphBase):
    def __init__(self, application, debug=False):
        msbase.MSGraphBase.__init__(self, application, debug=debug)
    
    def info(self, prop=None):
        return self.get(props=({'$select': prop} if prop else None))

    def get_prop(self, prop):
        info = self.info(prop)
        return info[prop] if info and prop in info else ''
    
    def name(self):
        return self.get_prop('displayName')

    def email(self):
        return self.get_prop('mail')
