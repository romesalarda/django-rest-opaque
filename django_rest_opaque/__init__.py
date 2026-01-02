__version__ = "0.1.0"

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

OPAQUE_SETTINGS = getattr(settings, "OPAQUE_SETTINGS", {
    
    "USER_QUERY_FIELD": "email",
    "USER_ID_FIELD": "id",
    
    "OPAQUE_SERVER_SETUP": None,
})
