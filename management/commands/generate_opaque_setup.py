from django.core.management.base import BaseCommand
import opaquepy

class Command(BaseCommand):
    help = "Generate a new OPAQUE server setup key"

    def handle(self, *args, **kwargs):
        
        setup = opaquepy.create_setup()
        self.stdout.write(self.style.SUCCESS("OPAQUE server setup (store securely):"))
        self.stdout.write("")
        self.stdout.write(f'OPAQUE_SERVER_SETUP="{setup}"')
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("Make sure to add this to your environment variables or settings!"))