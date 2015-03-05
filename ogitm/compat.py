try:
    from types import SimpleNamespace  # pragma: no flakes
except ImportError:

    class SimpleNamepace:
        pass
