# IMPORTANT: 
This is a coursework project and should not be used in practice

# Django REST OPAQUE

A Django REST Framework application implementing the OPAQUE (Oblivious Pseudorandom Function) password-authenticated key exchange protocol. This package provides a passwordless authentication system where password verification occurs without the server ever seeing the plaintext password.

## Features

- **OPAQUE Protocol**: Implements OPAQUE authentication for enhanced security
- **Two-Step Registration**: Secure user credential creation
- **Two-Step Login**: Password verification without server-side plaintext exposure
- **Session Management**: Built-in session handling with Django's session framework
- **RESTful API**: Full REST API endpoints for authentication flow
- **Django Admin Integration**: Manage OPAQUE credentials via Django admin

## Requirements !IMPORTANT
- Project built and developed in Python 3.13

- Python >= 3.8 cannot be larger than Python 3.14
- Django >= 4.2.0
- Django REST Framework >= 3.14.0
- opaquepy == 0.6.0
- opaque == 1.0.0
- pysodium >= 0.7.18

## Installation

Install via pip:

```bash
pip install django-rest-opaque
```

Or install from source:

```bash
git clone https://github.com/romesalarda/django-rest-opaque.git
cd django-rest-opaque
pip install -e .
```

## Quick Start

### 1. Add to Installed Apps

Add `django_rest_opaque` to your `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    # ... other apps
    'rest_framework',
    'django_rest_opaque',
]
```

### 2. Generate OPAQUE Server Setup Key

Run the management command to generate your server's OPAQUE setup key:

```bash
python manage.py generate_opaque_setup
```

This will output a server setup key. **Save this securely** - you'll need it for configuration.

### 3. Configure Settings

Add OPAQUE settings to your `settings.py`:

```python
OPAQUE_SETTINGS = {
    "USER_QUERY_FIELD": "email",  # Field to query users (default: "email")
    "USER_ID_FIELD": "id",        # Field for User model table primary key
    "OPAQUE_SERVER_SETUP": "<your_server_setup_key_here>",  # REQUIRED: From step 2
}
```

### 4. Configure Cache

Django REST OPAQUE uses Django's cache framework for storing intermediate login state. Ensure you have a cache backend configured:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
```

For production, use Redis, Memcached, or another persistent cache backend.

### 5. Add URL Patterns

Include the OPAQUE URLs in your project's `urls.py`:

```python
from django.urls import path, include
from django_rest_opaque.urls import get_url_patterns # checks for correct configuration

urlpatterns = [
    # ... other patterns
    path('o/', include(get_url_patterns())), #! important, do not add name spaces!
]
```

### 6. Run Migrations

Apply the database migrations:

```bash
python manage.py migrate django_rest_opaque
```

## API Endpoints

All endpoints are relative to your configured URL prefix (e.g., `/o/`).

### Registration Flow

#### 1. Start Registration
**POST** `/registration`

Request body:
```json
{
    "email": "user@example.com",
    "registration_request": "<GENERATED_BY_PASSWORD_MANAGER>"
}
```

Response:
```json
{
    "server_response": "<base64_encoded_data>"
}
```

#### 2. Finish Registration
**POST** `/registration/finish`

Request body:
```json
{
    "email": "user@example.com",
    "registration_record": "<base64_encoded_data>"
}
```

Response:
```json
{
    "statusText": "new user created!"
}
```

### Login Flow

#### 1. Start Login
**POST** `/login`

Request body:
```json
{
    "email": "user@example.com",
    "client_request": "<base64_encoded_data>"
}
```

Response:
```json
{
    "cache_key": "<session_cache_key>",
    "client_response": "<base64_encoded_data>"
}
```

#### 2. Finish Login
**POST** `/login/finish`

Request body:
```json
{
    "cache_key": "<session_cache_key>",
    "client_finish_request": "<base64_encoded_data>"
}
```

Response:
```json
{
    "statusText": "Login successful",
    "user_id": 1,
    "session_active": true
}
```

### Session Management

#### Check Session
**GET** `/check`

Requires authentication. Returns session status.
Returns available endpoints

#### Verify Session
**GET** `/verify`

Requires authentication. Verifies current session validity.

#### Redirect
**GET** `/redirect`

Redirects based on authentication status.

#### Logout
**POST** `/logout`

Requires authentication. Logs out the current user.

Response:
```json
{
    "message": "Logout successful"
}
```

## Configuration Options

### OPAQUE_SETTINGS

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `USER_QUERY_FIELD` | string | `"email"` | Field used to query users in the database |
| `USER_ID_FIELD` | string | `"id"` | Field used to identify users |
| `OPAQUE_SERVER_SETUP` | string | **Required** | Server setup key from `generate_opaque_setup` command |

## Management Commands

### generate_opaque_setup

Generates a new OPAQUE server setup key.

```bash
python manage.py generate_opaque_setup
```

**Important**: Run this once during initial setup and securely store the generated key. Use it in your `OPAQUE_SETTINGS`.

## Database Models

### OpaqueCredential

Stores OPAQUE envelope (encrypted credentials) for each user.

Fields:
- `user`: OneToOneField to your User model
- `opaque_envelope`: BinaryField storing the encrypted credential envelope
- `created_at`: DateTime of credential creation
- `updated_at`: DateTime of last credential update

Access via user:
```python
user.opaque_credential.envelope
```

## Development

### Building the Package

```bash
python -m build
```

### Installing Locally for Development

```bash
pip install -e .
```

## Security Considerations

1. **OPAQUE_SERVER_SETUP**: Keep this key secret and secure. Loss of this key means users cannot authenticate.
2. **HTTPS**: Always use HTTPS in production to protect data in transit.
3. **Cache Backend**: Use a secure, persistent cache backend in production (Redis with authentication, etc.).
4. **Session Security**: Configure Django's session security settings appropriately (`SESSION_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`, etc.).

## How OPAQUE Works

OPAQUE (Oblivious Pseudorandom Function) is a password-authenticated key exchange protocol that ensures:

1. The server never sees the user's plaintext password
2. The user's password is never transmitted over the network
3. Resistance to offline dictionary attacks
4. Forward secrecy and security even if the server is compromised

The protocol involves two phases:
- **Registration**: User creates credentials, server stores encrypted envelope
- **Authentication**: User proves knowledge of password without revealing it

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or contributions, please visit:
- GitHub Issues: https://github.com/romesalarda/django-rest-opaque/issues
- Documentation: https://github.com/romesalarda/django-rest-opaque#readme

## Credits

Built with:
- [Django](https://www.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [opaquepy](https://pypi.org/project/opaquepy/) - Python OPAQUE implementation
