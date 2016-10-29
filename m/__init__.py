import re
import json
import webob
from functools import wraps
from collections import namedtuple
from webob.dec import wsgify
from webob.exc import HTTPNotFound


PATTERNS = {
    'str': '[^/].+',
    'word': '\w+',
    'any': '.+',
    'int': '[+-]?\d+',
    'float': '[+-]?\d+\.\d+'
}

CASTS = {
    'str': str,
    'word': str,
    'any': str,
    'int': int,
    'float': float
}


Route = namedtuple('Route', ['pattern', 'methods', 'casts', 'handler'])


class Router:
    def __init__(self, prefix='', domain=None, filters=None):
        self.routes = []
        self.domain = domain
        self.prefix = prefix
        if filters is None:
            filters = []
        self.filters = []
        for fl in filters:
            if isinstance(fl, Filter):
                self.filters.append(fl)
            else:
                raise Exception('{} is not a Filter'.format(fl))

    def _route(self, rule, methods, handler):
        pattern, casts = self._rule_parse(rule)
        self.routes.append(Route(re.compile(pattern), methods, casts, handler))

    def _rule_parse(self, rule):
        pattern = []
        spec = []
        casts = {}
        is_spec = False
        for c in rule:
            if c == '{' and not is_spec:
                is_spec = True
            elif c == '}' and is_spec:
                is_spec = False
                name, p, c = self._spec_parse(''.join(spec))
                spec = []
                pattern.append(p)
                casts[name] = c
            elif is_spec:
                spec.append(c)
            else:
                pattern.append(c)
        return '{}$'.format(''.join(pattern)), casts

    def _spec_parse(self, src):
        tmp = src.split(':')
        if len(tmp) > 2:
            raise Exception('error pattern')
        name = tmp[0]
        type = 'str'
        if len(tmp) == 2:
            type = tmp[1]
        pattern = '(?P<{}>{})'.format(name, PATTERNS[type])
        return name, pattern, CASTS[type]

    def route(self, rule, methods=None):
        if methods is None:
            methods = ('GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTION')

        def dec(fn):
            self._route(rule, methods, fn)
            return fn
        return dec

    def _domain_match(self, request):
        return self.domain is None or re.match(self.domain, request.host)

    def _prefix_match(self, request):
        return request.path.startswith(self.prefix)

    def _apply_filter(self, handler):
        @wraps(handler)
        def apply(ctx, request):
            for fl in self.filters:
                request = fl.before_request(ctx, request)
            response = handler(ctx, request)
            for fl in reversed(self.filters):
                response = fl.after_request(ctx, request, response)
            return response
        return apply

    def match(self, request):
        if self._domain_match(request) and self._prefix_match(request):
            for route in self.routes:
                if request.method in route.methods:
                    m = route.pattern.match(request.path.replace(self.prefix, '', 1))
                    if m:
                        request.args = {}
                        for k, v in m.groupdict().items():
                            request.args[k] = route.casts[k](v)
                        return self._apply_filter(route.handler)

    def add_filter(self, filter):
        self.filters.append(filter)

    def before_request(self, fn):
        fl = Filter()
        fl.before_request = fn
        self.add_filter(fl)
        return fn

    def after_request(self, fn):
        fl = Filter()
        fl.after_request = fn
        self.add_filter(fl)
        return fn


class Request(webob.Request):
    def json(self):
        return json.loads(self.body.decode())


class Application:
    def __init__(self, routers=None, **attributes):
        if routers is None:
            routers = []
        self.routers = routers
        self.__attrs = attributes

    def add_router(self, router):
        self.routers.append(router)

    def __getattr__(self, name):
        try:
            return self.__attrs[name]
        except KeyError:
            raise AttributeError('no attr name {}'.format(name))

    @wsgify(RequestClass=Request)
    def __call__(self, request):
        for router in self.routers:
            handler = router.match(request)
            if handler:
                # pre process request
                res = handler(self, request)
                # post process response
                return res
        raise HTTPNotFound(detail='no handler match')


class Filter:
    def before_request(self, ctx, request):
        return request

    def after_request(self, ctx, request, response):
        return response
