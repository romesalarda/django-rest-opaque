'''
URL configurations for django-rest-opaque.
'''

from django.urls import path

from django_rest_opaque.views import (
    opaque_registration, 
    opaque_registration_finish,
    opaque_login,
    opaque_login_finish,
    verify_session,
    logout_session,
    session_redirect,
    check_opaque_support,
)


urlpatterns = [
    # OPAQUE API endpoints
    path('registration', opaque_registration, name="opaque_registration"),
    path('registration/finish', opaque_registration_finish, name="opaque_registration_finish"),
    path('login', opaque_login, name="opaque_login"),
    path('login/finish', opaque_login_finish, name="opaque_login_finish"),
    
    # Session management endpoints
    path('session/verify', verify_session, name="opaque_session_verify"),
    path('session/logout', logout_session, name="opaque_session_logout"),
    path('session/redirect', session_redirect, name="opaque_session_redirect"),
    
    path('check', check_opaque_support, name="opaque_support_check"),
]

def get_url_patterns():
    '''
    Validates OPAQUE settings and returns the urlpatterns.
    '''

    from django.conf import settings
    from django.core.exceptions import ImproperlyConfigured

    OPAQUE_SETTINGS = getattr(settings, "OPAQUE_SETTINGS", None)

    if not OPAQUE_SETTINGS:
        raise ImproperlyConfigured(
            "OPAQUE_SETTINGS is not configured in your Django settings. Please add it to configure django-rest-opaque."
        )

    if OPAQUE_SETTINGS["OPAQUE_SERVER_SETUP"] is None:
        raise ImproperlyConfigured(
            "OPAQUE_SETTINGS must include 'OPAQUE_SERVER_SETUP' with the server setup key. Run 'python manage.py generate_opaque_setup' to create one."
        )

    return urlpatterns