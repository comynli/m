class Extension:
    def __init__(self, **kwargs):
        self.app = kwargs.get('app')
        if self.app is not None:
            self._initialized = True
        else:
            self._initialized = False

    def initialize(self, app):
        self.app = app
        self._initialized = True

    @property
    def initialized(self):
        return self._initialized

