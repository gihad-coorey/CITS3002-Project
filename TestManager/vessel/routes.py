ROUTE_MAP = {}

def route(path):
    def _route(f):
        ROUTE_MAP[path] = f
        return f
    return _route

