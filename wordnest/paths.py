"""Keep writable user data separate from bundled application resources."""
import os
from pathlib import Path
import sys


def resource_root():
    return Path(__file__).resolve().parent.parent


def desktop_directory():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return resource_root()


def data_directory():
    if os.environ.get('WORDNEST_DATA'):
        return Path(os.environ['WORDNEST_DATA']).expanduser().resolve()
    if getattr(sys, 'frozen', False):
        return desktop_directory() / 'data'
    return resource_root() / 'data'
