from __future__ import annotations

from . import main
from .color_util import printc


def run_py():
    try:
        main.run()
    except KeyboardInterrupt:
        printc('&cThe program is interrupted by ^C, exiting...')
        exit(0)


if __name__ == '__main__':
    run_py()
