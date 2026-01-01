from django_rest_opaque.models import OpaqueCredential
from django.contrib import admin


class OpaqueCredentialAdmin(admin.ModelAdmin):
    """
    Admin interface for OpaqueCredential model.
    """
    list_display = ('user', 'created_at', 'updated_at', 'invalidated')
    search_fields = ('user__email',)
    list_filter = ('invalidated', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
admin.site.register(OpaqueCredential, OpaqueCredentialAdmin)