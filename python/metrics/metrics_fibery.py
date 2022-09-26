from fibery import *

#BugPrefix = "FB"
#StoryPrefix = "FS"
#SimulatorStoryPrefix = "FSS"
_databases = {}


class Products(CommonDatabase):
    """
        A representation of a Products database
    """
    def __init__(self, domain=None, token=None):
        super().__init__(None, 'Product Management/product', domain, token)

    def query_by_name(self, fname, select=[], limit=None):
        return Database.query_by_field(self, fname, field='Product Management/name', select=select, limit=limit)

    def names(self):
        results = Database.query(self)
        return [r['Product Management/name'] for r in results]


class Bugs(CommonDatabase):
    """
        A representation of a Metrics bug database.
    """
    def __init__(self, domain=None, token=None):
        super().__init__(Bug, 'Product Management/bug', domain, token)

    def query_by_product(self, product, select=[], limit=None):
        return Database.query_by_field(self, product, field='Product Management/product', select=select, limit=limit)

    def bugs(self, query={}, limit=None):
        bugs = self.query(query=query, limit=limit)
        return self.toItems(bugs)

    def byProduct(self, product):
        bugs = self.query_by_product(product)
        return self.toItems(bugs)


class Bug(CommonEntity):
    """
        A representation of a Metrics bug
    """
    def __init__(self, b, domain=None, token=None):
        super().__init__(b, Bugs, domain, token)

    def name(self):
        return self._attr('Product Management/name')

    def id(self):
        return Bug.prefix() + CommonEntity.id(self)

    def prefix():
        return "FB"


RegisterDatabase(Bugs, Bug, True)


class SimulatorStories(CommonDatabase):
    """
        A representation of a Simulator Story database
    """
    def __init__(self, domain=None, token=None):        super().__init__(SimulatorStory, 'DSIM Development/Simulator story', domain, token)

    def stories(self, query={}, limit=None):
        stories = self.query(query=query, limit=limit)
        return self.toItems(stories)


class SimulatorStory(CommonEntity):
    """
        A representation of a Simulator Story (DSIM)
    """
    def __init__(self, story, domain=None, token=None):
        super().__init__(story, SimulatorStories, domain, token)

    def name(self):
        return self._attr('DSIM Development/name')

    def id(self):
        return SimulatorStory.prefix + CommonEntity.id(self)

    def prefix():
        return "FSS"


RegisterDatabase(SimulatorStories, SimulatorStory)


class Stories(CommonDatabase):
    """
        A representation of a Story database
    """
    def __init__(self, domain=None, token=None):
        super().__init__(Story, 'Product Management/Story', domain, token)

    def stories(self, query={}, limit=None):
        stories = self.query(query=query, limit=limit)
        return self.toItems(stories)


class Story(CommonEntity):
    """
        A representation of a Story (DSIM)
    """
    def __init__(self, story, domain=None, token=None):
        super().__init__(story, Stories, domain, token)

    def name(self):
        return self._attr('Product Management/name')

    def id(self):
        return Story.prefix() + CommonEntity.id(self)

    def prefix():
        return "FS"


RegisterDatabase(Stories, Story)
