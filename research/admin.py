from django.contrib import admin
from .models import Politician, ResearchResult

@admin.register(Politician)
class PoliticianAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'created_at')
    search_fields = ('name', 'position')
    list_filter = ('position', 'created_at')
    date_hierarchy = 'created_at'
    
    # Show research results in the politician detail view
    readonly_fields = ('research_count',)
    
    def research_count(self, obj):
        return obj.research_results.count()
    research_count.short_description = 'Number of research results'


@admin.register(ResearchResult)
class ResearchResultAdmin(admin.ModelAdmin):
    list_display = ('politician', 'created_at', 'updated_at', 'has_background', 'has_accomplishments', 'has_criticisms', 'has_summary')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('politician__name', 'background', 'accomplishments', 'criticisms', 'summary')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Politician', {
            'fields': ('politician',)
        }),
        ('Research Data', {
            'fields': ('background', 'accomplishments', 'criticisms', 'summary'),
        }),
        ('Metadata', {
            'fields': ('sources', 'created_at', 'updated_at'),
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