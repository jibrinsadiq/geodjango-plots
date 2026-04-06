from django.contrib import admin
from .models import Plot, Marker


@admin.register(Plot)
class PlotAdmin(admin.ModelAdmin):
    list_display = ('plot_name', 'plot_code', 'is_active', 'created_at')
    search_fields = ('plot_name', 'plot_code')


@admin.register(Marker)
class MarkerAdmin(admin.ModelAdmin):
    list_display = ('marker_name', 'plot', 'marker_order', 'latitude', 'longitude', 'created_at')
    search_fields = ('marker_name', 'plot__plot_name')
    list_filter = ('plot',)



