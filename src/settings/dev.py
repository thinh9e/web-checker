import sys

try:
    from .common import *
except ImportError:
    sys.exit('Error import common settings')

SECRET_KEY = 'wh5s6*2#86=i^n*ty(haeqc2r4e$u(ss2c-e!+8^$4dhw-ja*+'
DEBUG = True

ALLOWED_HOSTS = []
