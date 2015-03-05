try:  # pragma: no cover
    from types import SimpleNamespace  # pragma: no flakes
except ImportError:  # pragma: no cover

    class SimpleNamespace:
        pass
