import json
from webob import Response


def jsonify(**kwargs):
    return Response(json.dumps(kwargs), content_type='application/json')
