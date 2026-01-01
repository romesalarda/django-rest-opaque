
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

OPAQUEURLPATTERNS = urlpatterns