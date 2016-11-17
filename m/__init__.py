import os
import sys
import json
import webob
from webob.dec import wsgify
from webob.exc import HTTPNotFound
from pyhocon import ConfigFactory
from pyhocon.config_tree import ConfigTree
from .ext import Extension
from .router import Router
from .filter import Filter


class Request(webob.Request):
    def json(self):
        return json.loads(self.body.decode())


class Application:
    def __init__(self, routers=None, **kwargs):
        self.extensions = {}
        self.kwargs = kwargs
        default_config_file = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'application.conf')
        config_file = self.kwargs.pop('config', default_config_file)
        if os.path.exists(config_file):
            self.config = ConfigFactory.parse_file(config_file)
        else:
            self.config = ConfigTree()
        if routers is None:
            routers = []
        self.routers = routers
        self.filters = []

    def add_router(self, r):
        if isinstance(r, Router):
            self.routers.append(r)

    def register_extension(self, instance, name=None):
        if isinstance(instance, Extension):
            if name is None:
                name = instance.__class__.__name__
            instance.initialize(self)
            self.extensions[name] = instance

    def add_filter(self, fl):
        if isinstance(fl, Filter):
            self.filters.append(fl)
    
    def __getattr__(self, name):
        if name in self.extensions.keys():
            return self.extensions[name]
        if name in self.kwargs.keys():
            return self.kwargs[name]
        raise AttributeError(name)
            

    @wsgify(RequestClass=Request)
    def __call__(self, request):
        for r in self.routers:
            handler = r.match(request)
            if handler:
                for fl in self.filters:
                    request = fl.before_request(self, request)
                res = handler(self, request)
                for fl in reversed(self.filters):
                    res = fl.after_request(self, request, res)
                return res
        raise HTTPNotFound(detail='no handler match')


