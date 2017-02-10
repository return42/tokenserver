try:
    import os
    if os.environ.get("DEBUG", None):
        from pytest import set_trace
        __builtins__["DEBUG"] = set_trace
except ImportError:
    pass
