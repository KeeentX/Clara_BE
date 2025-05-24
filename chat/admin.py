from django.contrib import admin
from .models import Chat, QandA

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'politician', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('politician', 'user__username')
    date_hierarchy = 'created_at'

@admin.register(QandA)
class QandAAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat', 'question', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('question', 'answer')
    date_hierarchy = 'created_at'