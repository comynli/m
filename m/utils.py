import json
from webob import Response


def jsonfy(**kwargs):
    return Response(json.dumps(kwargs), content_type='application/json')
