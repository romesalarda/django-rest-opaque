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
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from django_rest_opaque.models import OpaqueCredential

import opaquepy
import uuid

import logging

# Initialize server setup once at module load
SERVER_SETUP = OPAQUE_SETTINGS["OPAQUE_SERVER_SETUP"]

@csrf_exempt
@decorators.api_view(["POST"])
@decorators.permission_classes([AllowAny])
def opaque_registration(req:request.HttpRequest):
    '''
    OPAQUE Registration Step 1: Start registration process
    Returns server response to client to continue registration
    
    :param req: The HTTP request containing registration data
    :type req: request.HttpRequest
    '''
    try:    
        user_id = req.data.get(OPAQUE_SETTINGS["USER_QUERY_FIELD"])
    except KeyError:
        return response.Response(
            {"error": f"{OPAQUE_SETTINGS['USER_QUERY_FIELD']} is required"},
            status=400
        )
    try:
        registration_request = req.data["registration_request"]
    except KeyError:
        return response.Response(
            {"error": "registration_request is required"},
            status=400
        )
    if get_user_model().objects.filter(**{OPAQUE_SETTINGS["USER_QUERY_FIELD"]: user_id}).exists():
        return response.Response(
            {"error": "User already exists"},
            status=409
        )

    try:
        to_client = opaquepy.register(SERVER_SETUP, registration_request, user_id)
    except Exception as e:
        logging.error(f"OPAQUE registration error: {e}")
        return response.Response(
            {"error": "Failed to start OPAQUE registration, invalid data provided"},
            status=400
        )
    
    return response.Response(to_client)

@csrf_exempt
@decorators.api_view(["POST"])
@decorators.permission_classes([AllowAny])
def opaque_registration_finish(req:request.HttpRequest):
    '''
    OPAQUE Registration Step 2: Finish registration process
    Stores the OPAQUE envelope in the database associated with the user
    
    :param req: The HTTP request containing registration data
    :type req: request.HttpRequest
    '''
    try:    
        user_id = req.data[OPAQUE_SETTINGS["USER_QUERY_FIELD"]]
    except KeyError:
        return response.Response(
            {"error": f"{OPAQUE_SETTINGS['USER_QUERY_FIELD']} is required"},
            status=400
        )
    try:
        client_request_finish = req.data["registration_record"]
    except KeyError:
        return response.Response(
            {"error": "registration_record is required"},
            status=400
        )
    if get_user_model().objects.filter(**{OPAQUE_SETTINGS["USER_QUERY_FIELD"]: user_id}).exists():
        return response.Response(
            {"error": "User already exists"},
            status=409
        )

    try:
        envelope_to_be_saved = opaquepy.register_finish(client_request_finish)
    except Exception as e:
        logging.error(f"OPAQUE registration finish error: {e}")
        return response.Response(
            {"error": "Failed to finish OPAQUE registration, invalid data provided"},
            status=400
        )
    
    user, created = get_user_model().objects.get_or_create(**{OPAQUE_SETTINGS["USER_QUERY_FIELD"]: user_id})
    if getattr(user, 'opaque_credential', None): # if a user already has credentials, delete them
        # we operate a single-credential policy per user for simplicity
        user.opaque_credential.delete()
    try:
        user.opaque_credential = OpaqueCredential.objects.create(user=user, opaque_envelope=bytes(envelope_to_be_saved, encoding="utf-8"))
        user.save()
    except Exception as e:
        logging.error(f"Failed to save OPAQUE credential: {e}")
        return response.Response(
            {"error": "Failed to save OPAQUE credential"},
            status=500
        )
    
    return response.Response({"statusText": "new user created!"})

@csrf_exempt
@decorators.api_view(["POST"])
@decorators.permission_classes([AllowAny])
def opaque_login(req:request.HttpRequest):
    """
    OPAQUE Login Step 1: Start login process
    Stores login state in cache and returns server response + cache key to client
    """
    try:
        user_id = req.data[OPAQUE_SETTINGS["USER_QUERY_FIELD"]]
    except KeyError:
        return response.Response(
            {"error": f"{OPAQUE_SETTINGS['USER_QUERY_FIELD']} is required"},
            status=400
        )
    try:
        client_request = req.data["client_request"]
    except KeyError:
        return response.Response(
            {"error": "client_request is required"},
            status=400
        )
    user = get_object_or_404(get_user_model(), **{OPAQUE_SETTINGS["USER_QUERY_FIELD"]: user_id})
    try:
        envelope = user.opaque_credential.opaque_envelope.decode("utf-8")
    except OpaqueCredential.DoesNotExist:
        return response.Response(
            {"error": "User does not have OPAQUE credentials"},
            status=401
        )
    try:
        client_response, login_state = opaquepy.login(
            setup=SERVER_SETUP,
            password_file=envelope,
            client_request=client_request,
            credential_id=user_id
        )
    except Exception as e:
        logging.error(f"OPAQUE login start error: {e}")
        return response.Response(
            {"error": "Failed to start OPAQUE login, invalid data provided"},
            status=400
        )
    
    cache_key = f"opaque_login_{uuid.uuid4().hex}"
    
    cache_data = {
        'login_state': login_state,
        OPAQUE_SETTINGS["USER_QUERY_FIELD"]: user_id,
        'user_id': getattr(user, OPAQUE_SETTINGS["USER_ID_FIELD"])
    }
    print("Storing login state in cache with key:", cache_data)
    cache.set(cache_key, cache_data, timeout=300)  # 5 minutes
        
    return response.Response({
        "client_response": client_response,
        "cache_key": cache_key
    })

@csrf_exempt
@decorators.api_view(["POST"])
@decorators.permission_classes([AllowAny])
def opaque_login_finish(req:request.HttpRequest):
    """
    OPAQUE Login Step 2: Finish login process
    Retrieves login state from cache and completes authentication
    """
    try:
        cache_key = req.data["cache_key"]
    except KeyError:
        return response.Response(
            {"error": "cache_key is required"},
            status=400
        )
    
    try:
        client_finish_request = req.data["client_finish_request"]
    except KeyError:
        return response.Response(
            {"error": "client_finish_request is required"},
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
    user_id = cache_data.get("user_id")

    if not user_id or not login_state:
        logging.error("Invalid login state or user ID in cache data")
        return response.Response(
            {"error": "Invalid login state in cache"},
            status=400
        )
    
    try:
        session_key = opaquepy.login_finish(
            client_finish_request,
            login_state)
    except Exception as e:
        logging.error(f"OPAQUE login finish error: {e}")
        return response.Response(
            {"error": "Failed to finish OPAQUE login, invalid data provided"},
            status=400
        )
 
    cache.delete(cache_key)
    user = get_object_or_404(get_user_model(), **{OPAQUE_SETTINGS["USER_ID_FIELD"]: user_id})
    
    login(req, user)

    logging.info(f"User {user_id} logged in successfully via OPAQUE.")    

    return response.Response({
        "statusText": "Login successful",
        OPAQUE_SETTINGS["USER_QUERY_FIELD"]: user_id,
        "session_active": True
    })
    
@csrf_exempt
@decorators.api_view(["GET"])
@decorators.permission_classes([AllowAny])
def check_opaque_support(req:request.HttpRequest):
    """
    Endpoint to check if OPAQUE is supported on the server
    """
    return response.Response({
        "opaque_supported": True,
        "message": "OPAQUE is supported on this server.",
        "endpoints": { # return available endpoints
            "registration": reverse('opaque_registration'),
            "registration_finish": reverse('opaque_registration_finish'),
            "login": reverse('opaque_login'),
            "login_finish": reverse('opaque_login_finish'),
            "session_verify": reverse('opaque_session_verify'),
            "session_logout": reverse('opaque_session_logout'),
            "session_redirect": reverse('opaque_session_redirect'),
            "check": reverse('opaque_support_check'),
        }})

@decorators.api_view(["GET"])
@decorators.permission_classes([IsAuthenticated])
def verify_session(req:request.HttpRequest):
    """
    Verify that the user's session is active and valid - use for OPAQUE session checks
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

    Use case: After OPAQUE login via API, redirect user to home page with active session.
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

    OPAQUE does not have a logout mechanism, so this simply ends the session.
    """
    from django.contrib.auth import logout
    try:
        user_query_field = getattr(req.user, OPAQUE_SETTINGS["USER_QUERY_FIELD"])
    except AttributeError:
        return response.Response(
            {"error": "User not found"},
            status=400
        )

    logout(req)
    
    return response.Response({
        "statusText": "Logout successful",
        OPAQUE_SETTINGS["USER_QUERY_FIELD"]: user_query_field
    })