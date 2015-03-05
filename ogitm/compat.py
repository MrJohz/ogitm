try:
    from types import SimpleNamespace  # pragma: no flakes
except ImportError:

    class SimpleNamespace:
        pass
