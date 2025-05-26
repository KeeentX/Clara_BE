from django.core.management.base import BaseCommand
from chat.models import Chat

class Command(BaseCommand):
    help = 'Removes temporary chats that are older than 24 hours'

    def handle(self, *args, **options):
        count = Chat.remove_old_temporary_chats()
        self.stdout.write(
            self.style.SUCCESS(f'Successfully removed {count} old temporary chats')
        )