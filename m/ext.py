

class Extension:
    def __init__(self, **kwargs):
        self.app = kwargs.get('app')
        self._initialized = False

    def initialize(self, app):
        self.app = app
        self._initialized = True

    @property
    def initialized(self):
        return self._initialized

