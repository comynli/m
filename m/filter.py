class Filter:
    def before_request(self, ctx, request):
        return request

    def after_request(self, ctx, request, response):
        return response