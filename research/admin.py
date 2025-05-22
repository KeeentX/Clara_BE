from django.contrib import admin
from .models import Politician, ResearchResult
from django.utils.html import format_html

@admin.register(Politician)
class PoliticianAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_image', 'created_at']
    search_fields = ['name']
    readonly_fields = ['display_image_large', 'created_at_display']
    
    def display_image(self, obj):
        """Display thumbnail in list view"""
        if obj.image_url:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 50%;" />', obj.image_url)
        return "No image"
    display_image.short_description = 'Photo'
    
    def display_image_large(self, obj):
        """Display larger image in detail view"""
        if obj.image_url:
            return format_html('<img src="{}" width="200" style="max-height: 300px; object-fit: contain;" />', obj.image_url)
        return "No image available"
    display_image_large.short_description = 'Politician Photo'
    
    def created_at_display(self, obj):
        """Display created_at as read-only"""
        return obj.created_at
    created_at_display.short_description = 'Created At'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'display_image_large')
        }),
        ('Metadata', {
            'fields': ('image_url', 'created_at_display'),
            'classes': ('collapse',),
        }),
    )


@admin.register(ResearchResult)
class ResearchResultAdmin(admin.ModelAdmin):
    list_display = ('politician', 'position', 'display_image', 'created_at', 'has_background', 'has_accomplishments', 'has_criticisms', 'has_summary')
    list_filter = ('position', 'created_at')
    search_fields = ('politician__name', 'position', 'background', 'accomplishments', 'criticisms', 'summary')
    readonly_fields = ('created_at_display', 'updated_at_display', 'display_image_large')
    date_hierarchy = 'created_at'
    
    def display_image(self, obj):
        """Display thumbnail in list view"""
        if hasattr(obj, 'image_url') and obj.image_url:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 50%;" />', obj.image_url)
        elif obj.politician and obj.politician.image_url:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 50%;" />', obj.politician.image_url)
        return "No image"
    display_image.short_description = 'Photo'
    
    def display_image_large(self, obj):
        """Display larger image in detail view"""
        if hasattr(obj, 'image_url') and obj.image_url:
            return format_html('<img src="{}" width="200" style="max-height: 300px; object-fit: contain;" />', obj.image_url)
        elif obj.politician and obj.politician.image_url:
            return format_html('<img src="{}" width="200" style="max-height: 300px; object-fit: contain;" />', obj.politician.image_url)
        return "No image available"
    display_image_large.short_description = 'Politician Photo'
    
    def created_at_display(self, obj):
        """Display created_at as read-only"""
        return obj.created_at
    created_at_display.short_description = 'Created At'
    
    def updated_at_display(self, obj):
        """Display updated_at as read-only"""
        return obj.updated_at if hasattr(obj, 'updated_at') else None
    updated_at_display.short_description = 'Updated At'
    
    def formatted_background(self, obj):
        """Format background text for better readability"""
        if obj.background:
            return format_html('<div style="max-width: 800px;">{}</div>', obj.background.replace('\n', '<br>'))
        return "-"
    formatted_background.short_description = 'Background'
    
    def formatted_accomplishments(self, obj):
        """Format accomplishments text for better readability"""
        if obj.accomplishments:
            return format_html('<div style="max-width: 800px;">{}</div>', obj.accomplishments.replace('\n', '<br>'))
        return "-"
    formatted_accomplishments.short_description = 'Accomplishments'
    
    def formatted_criticisms(self, obj):
        """Format criticisms text for better readability"""
        if obj.criticisms:
            return format_html('<div style="max-width: 800px;">{}</div>', obj.criticisms.replace('\n', '<br>'))
        return "-"
    formatted_criticisms.short_description = 'Criticisms'
    
    def formatted_summary(self, obj):
        """Format summary text for better readability"""
        if obj.summary:
            return format_html('<div style="max-width: 800px;">{}</div>', obj.summary.replace('\n', '<br>'))
        return "-"
    formatted_summary.short_description = 'Summary'
    
    fieldsets = (
        ('Politician Information', {
            'fields': ('politician', 'position', 'display_image_large')
        }),
        ('Research Data', {
            'fields': ('background', 'accomplishments', 'criticisms', 'summary'),
        }),
        ('Metadata', {
            'fields': ('sources', 'image_url', 'image_metadata', 'created_at_display', 'updated_at_display'),
            'classes': ('collapse',)
        }),
    )
    
    # Custom admin methods to show if content exists
    def has_background(self, obj):
        return bool(obj.background)
    has_background.boolean = True  # Display as icon
    has_background.short_description = 'Background'
    
    def has_accomplishments(self, obj):
        return bool(obj.accomplishments)
    has_accomplishments.boolean = True
    has_accomplishments.short_description = 'Accomplishments'
    
    def has_criticisms(self, obj):
        return bool(obj.criticisms)
    has_criticisms.boolean = True
    has_criticisms.short_description = 'Criticisms'

    def has_summary(self, obj):
        return bool(obj.summary)
    has_summary.boolean = True
    has_summary.short_description = 'Summary'