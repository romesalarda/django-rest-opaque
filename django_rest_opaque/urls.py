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
    path('registration', opaque_registration, name="o-reg"),
    path('registration/finish', opaque_registration_finish, name="o-reg-terminate"),
    path('login', opaque_login, name="o-login"),
    path('login/finish', opaque_login_finish, name="o-login-finish"),
    
    # Session management endpoints
    path('session/verify', verify_session, name="o-session-verify"),
    path('session/logout', logout_session, name="o-session-logout"),
    path('session/redirect', session_redirect, name="o-session-redirect"),
    
    path('check', check_opaque_support, name="o-support-check"),
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