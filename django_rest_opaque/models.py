from django.db import models
from django.contrib.auth import get_user_model

class OpaqueCredential(models.Model):
    """
    Model to store OPAQUE credentials associated with a user
    """
    
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='opaque_credential')
    opaque_envelope = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    invalidated = models.BooleanField(default=False)

    def __str__(self):
        return f'OPAQUE Credential for {self.user.email}'