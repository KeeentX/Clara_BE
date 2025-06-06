from django.contrib import admin
from .models import PoliticianPicks

class PoliticianPicksAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_politicians')
    search_fields = ('user__username', 'user__email')
    
    def get_politicians(self, obj):
        return ", ".join([p.name for p in obj.politicians.all()[:5]])
    
    get_politicians.short_description = 'Politicians'

admin.site.register(PoliticianPicks, PoliticianPicksAdmin)

# We're using Django's built-in User model, which is already registered with the admin site.