from django.contrib import admin
from .models import PriceUpdate

@admin.register(PriceUpdate)
class PriceUpdateAdmin(admin.ModelAdmin):
    list_display = ('ticker_symbol', 'price', 'timestamp', 'volume', 'exchange')
    list_filter = ('ticker_symbol', 'exchange')
    search_fields = ('ticker_symbol',)
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
