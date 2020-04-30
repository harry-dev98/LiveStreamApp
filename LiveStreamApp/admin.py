from django.contrib import admin

from .models import Session, Chat, Peer

admin.site.register(Session)
admin.site.register(Chat)
admin.site.register(Peer)
