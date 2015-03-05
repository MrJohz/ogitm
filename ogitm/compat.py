try:  # pragma: no cover
    from types import SimpleNamespace  # pragma: no flakes
except ImportError:  # pragma: no cover

    class SimpleNamespace:
        pass

try:  # pragma: no cover
    from collections.abc import MutableMapping  # pragma: no flakes
except ImportError:  # pragma: no cover
    from collections import MutableMapping  # pragma: no flakes
