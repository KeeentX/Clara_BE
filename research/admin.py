from django.contrib import admin
from .models import Politician, ResearchResult, Chat, Message

@admin.register(Politician)
class PoliticianAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'created_at')
    search_fields = ('name', 'position')
    ordering = ('name',)
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related()
        return queryset
    
    def has_research(self, obj):
        return obj.research_results.exists()
    has_research.boolean = True
    
    def latest_research_date(self, obj):
        latest = obj.get_latest_research()
        return latest.created_at if latest else None
    latest_research_date.short_description = 'Latest Research'


class ResearchInline(admin.TabularInline):
    model = ResearchResult
    fields = ('created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    extra = 0
    max_num = 5
    can_delete = False
    show_change_link = True


@admin.register(ResearchResult)
class ResearchResultAdmin(admin.ModelAdmin):
    list_display = ('politician', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('politician__name', 'summary')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('politician', 'created_at', 'updated_at')
        }),
        ('Research Data', {
            'fields': ('background', 'accomplishments', 'criticisms', 'summary'),
            'classes': ('collapse',),
        }),
        ('Sources', {
            'fields': ('sources',),
            'classes': ('collapse',),
        }),
    )
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('politician')
        return queryset

class MessageInline(admin.TabularInline):
    model = Message
    fields = ('content', 'role', 'timestamp')
    readonly_fields = ('timestamp',)
    extra = 0
    max_num = 10
    can_delete = True
    ordering = ('timestamp',)


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'updated_at', 'message_count')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('title', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [MessageInline]
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('user')
        return queryset


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('chat', 'role', 'content_preview', 'timestamp')
    list_filter = ('role', 'timestamp')
    search_fields = ('content', 'chat__title')
    readonly_fields = ('timestamp',)
    
    def content_preview(self, obj):
        return obj.content[:50] + ('...' if len(obj.content) > 50 else '')
    content_preview.short_description = 'Content'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('chat')
        return queryset