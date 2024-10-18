from .base import *

DEBUG = True

STATIC_ROOT = None


# Static files (CSS, JavaScript, Images)
STATICFILES_DIRS = [
    os.path.join(BASE_DIR.parent, "api", "static"),
]