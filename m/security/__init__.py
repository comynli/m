from functools import wraps
from .. import Filter
from webob.exc import HTTPUnauthorized, HTTPForbidden


class AuthenticationProvider:
    def __init__(self, request):
        self.request = request

    @property
    def principal(self):
        raise HTTPUnauthorized()

    def has_permissions(self, permissions=None):
        if self.principal is None:
            raise HTTPUnauthorized()
        if not permissions:
            return True
        if set(getattr(self.principal, 'roles', [])).intersection(permissions):
            return True
        raise HTTPForbidden()


class AuthenticationFilter(Filter):
    def __init__(self, cls):
        self.provider_cls = cls

    def before_request(self, ctx, request):
        request.security = self.provider_cls(request)
        return request


class Require:
    def __init__(self, permissions=None, request=None):
        self.request = request
        self.permissions = permissions

    def __call__(self, fn):
        @wraps(fn)
        def wrap(ctx, request):
            if not getattr(request, 'security'):
                raise HTTPUnauthorized()
            if request.security.has_permissions(self.permissions):
                return fn(ctx, request)
        return wrap

    def __enter__(self):
        if not getattr(self.request, 'security'):
            raise HTTPUnauthorized()
        self.request.security.has_permissions(self.permissions)

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass