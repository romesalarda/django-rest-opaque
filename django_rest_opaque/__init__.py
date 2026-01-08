__version__ = "0.1.0"

from django.conf import settings

OPAQUE_SETTINGS = getattr(settings, "OPAQUE_SETTINGS", {
    
    "USER_QUERY_FIELD": "email", # defines field to query user during OPAQUE operations
    "USER_ID_FIELD": "id", # defines primary key field of user model
    "OPAQUE_SERVER_SETUP": None, # must be set to server setup key string
})
