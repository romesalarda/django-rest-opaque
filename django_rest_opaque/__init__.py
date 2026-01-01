__version__ = "0.1.0"

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

OPAQUE_SETTINGS = getattr(settings, "OPAQUE_SETTINGS", {
    
    "USER_QUERY_FIELD": "email",
    "USER_ID_FIELD": "id",
    
    "OPAQUE_SERVER_SETUP": None,
})

print("Initialized OPAQUE settings:", OPAQUE_SETTINGS)

if OPAQUE_SETTINGS["OPAQUE_SERVER_SETUP"] is None:
    raise ImproperlyConfigured(
        "OPAQUE_SETTINGS must include 'OPAQUE_SERVER_SETUP' with the server setup key. Run 'python manage.py generate_opaque_setup' to create one."
    )