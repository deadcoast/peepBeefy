from __future__ import annotations

import os

from .py import run_py
from .rs import run_rust

if __name__ == '__main__':
    if os.environ.get('HYFETCH_PY', False):
        run_py()
    else:
        run_rust()
