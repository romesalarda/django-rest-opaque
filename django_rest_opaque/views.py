'''
Views for handling OPAQUE registration and login processes.
'''
from rest_framework import decorators, request, response
from rest_framework.permissions import IsAuthenticated, AllowAny
from . import OPAQUE_SETTINGS

from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.contrib.auth import login
from django.contrib.auth import get_user_model

from django_rest_opaque.models import OpaqueCredential

import opaquepy
import uuid
import hashlib

# Initialize server setup once at module load
SERVER_SETUP = OPAQUE_SETTINGS["OPAQUE_SERVER_SETUP"]

@decorators.api_view(["POST"])
@decorators.permission_classes([AllowAny])
def opaque_registration(req:request.HttpRequest):
    '''
    OPAQUE Registration Step 1: Start registration process
    Returns server response to client to continue registration
    
    :param req: The HTTP request containing registration data
    :type req: request.HttpRequest
    '''
    user_id = req.data.get(OPAQUE_SETTINGS["USER_QUERY_FIELD"])
    registration_request = req.data.get("registration_request")
    to_client = opaquepy.register(SERVER_SETUP, registration_request, user_id)
    return response.Response(to_client)

@decorators.api_view(["POST"])
@decorators.permission_classes([AllowAny])
def opaque_registration_finish(req:request.HttpRequest):
    '''
    OPAQUE Registration Step 2: Finish registration process
    Stores the OPAQUE envelope in the database associated with the user
    
    :param req: The HTTP request containing registration data
    :type req: request.HttpRequest
    '''
    user_id = req.data.get(OPAQUE_SETTINGS["USER_QUERY_FIELD"])
    client_request_finish = req.data.get("registration_record")
    
    envelope_to_be_saved = opaquepy.register_finish(client_request_finish)
    
    user, created = get_user_model().objects.get_or_create(**{OPAQUE_SETTINGS["USER_QUERY_FIELD"]: user_id})
    if getattr(user, 'opaque_credential', None):
        user.opaque_credential.delete()
    user.opaque_credential = OpaqueCredential.objects.create(user=user, opaque_envelope=bytes(envelope_to_be_saved, encoding="utf-8"))
    user.save()
    
    return response.Response({"statusText": "new user created!"})

@decorators.api_view(["POST"])
@decorators.permission_classes([AllowAny])
def opaque_login(req:request.HttpRequest):
    """
    OPAQUE Login Step 1: Start login process
    Stores login state in cache and returns server response + cache key to client
    """
    user_id = req.data.get(OPAQUE_SETTINGS["USER_QUERY_FIELD"])
    client_request = req.data.get("client_request")
    
    user = get_object_or_404(get_user_model(), **{OPAQUE_SETTINGS["USER_QUERY_FIELD"]: user_id})
    try:
        envelope = user.opaque_credential.opaque_envelope.decode("utf-8")
    except OpaqueCredential.DoesNotExist:
        return response.Response(
            {"error": "User does not have OPAQUE credentials"},
            status=401
        )
    
    client_response, login_state = opaquepy.login(
        setup=SERVER_SETUP,
        password_file=envelope,
        client_request=client_request,
        credential_id=user_id
    )
    
    cache_key = f"opaque_login_{uuid.uuid4().hex}"
    
    cache_data = {
        'login_state': login_state,
        OPAQUE_SETTINGS["USER_QUERY_FIELD"]: user_id,
        'user_id': getattr(user, OPAQUE_SETTINGS["USER_ID_FIELD"])
    }
    cache.set(cache_key, cache_data, timeout=300)  # 5 minutes
        
    return response.Response({
        "client_response": client_response,
        "cache_key": cache_key
    })

@decorators.api_view(["POST"])
@decorators.permission_classes([AllowAny])
def opaque_login_finish(req:request.HttpRequest):
    """
    OPAQUE Login Step 2: Finish login process
    Retrieves login state from cache and completes authentication
    """
    cache_key = req.data.get("cache_key")
    client_finish_request = req.data.get("client_finish_request")
    
    if not cache_key:
        return response.Response(
            {"error": "cache_key is required"},
            status=400
        )
    
    # Retrieve login state from cache
    cache_data = cache.get(cache_key)
    
    if not cache_data:
        return response.Response(
            {"error": "Login session expired or invalid cache key"},
            status=404
        )
    
    login_state = cache_data.get('login_state')
    user_id = cache_data.get(OPAQUE_SETTINGS["USER_QUERY_FIELD"])
    user_id = cache_data.get('user_id')
    
    session_key = opaquepy.login_finish(
        client_finish_request,
        login_state)
 
    cache.delete(cache_key)
    user = get_object_or_404(get_user_model(), **{OPAQUE_SETTINGS["USER_ID_FIELD"]: user_id})
    
    login(req, user)
    req.session["opaque_key"] = hashlib.sha256(session_key.encode()).hexdigest()
    
    # print(f"Login completed for user: {user_id}")
    # print(f"Session key: {req.session.session_key}")
    # print(f"User authenticated: {req.user.is_authenticated}")
    
    return response.Response({
        "statusText": "Login successful",
        OPAQUE_SETTINGS["USER_QUERY_FIELD"]: user_id,
        "session_active": True
    })
    
@decorators.api_view(["GET"])
@decorators.permission_classes([AllowAny])
def check_opaque_support(req:request.HttpRequest):
    """
    Endpoint to check if OPAQUE is supported on the server
    """
    return response.Response({
        "opaque_supported": True,
        "message": "OPAQUE is supported on this server."})

@decorators.api_view(["GET"])
@decorators.permission_classes([IsAuthenticated])
def verify_session(req:request.HttpRequest):
    """
    Verify that the user's session is active and valid
    """
    return response.Response({
        "authenticated": True,
        OPAQUE_SETTINGS["USER_QUERY_FIELD"]: getattr(req.user, OPAQUE_SETTINGS["USER_QUERY_FIELD"]),
        "user_id": req.user.id
    })

@decorators.api_view(["GET"])
def session_redirect(req:request.HttpRequest):
    """
    Redirect endpoint that transfers the session to browser context.
    Used after OPAQUE login to activate session in main browser.
    """
    from django.shortcuts import redirect
    
    if req.user.is_authenticated:
        # Session is valid, redirect to home
        return redirect('home')
    else:
        # No valid session, redirect to login
        return redirect('login')

@decorators.api_view(["POST"])
@decorators.permission_classes([IsAuthenticated])
def logout_session(req:request.HttpRequest):
    """
    Logout the user and invalidate the session
    """
    from django.contrib.auth import logout
    user_id = getattr(req.user, OPAQUE_SETTINGS["USER_QUERY_FIELD"])
    logout(req)
    
    return response.Response({
        "statusText": "Logout successful",
        OPAQUE_SETTINGS["USER_QUERY_FIELD"]: user_id
    })