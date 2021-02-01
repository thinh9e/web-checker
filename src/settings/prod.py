import sys

try:
    from .common import *
except ImportError:
    sys.exit('Error import common settings')

SECRET_KEY = 'lii!%c@5&a&2-joo*sj4+e1d8b$ol=&jjr_oqgqasz+w^eam+h'
DEBUG = False

ALLOWED_HOSTS = ['checkseo.top']
