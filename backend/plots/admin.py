from django.contrib import admin
from .models import Owner, Plot, Marker, PlotMedia


@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "other_name",
        "surname",
        "phone_number",
        "email",
        "id_type",
        "id_number",
        "created_at",
    )
    search_fields = (
        "first_name",
        "other_name",
        "surname",
        "phone_number",
        "email",
        "id_number",
    )
    list_filter = ("id_type", "created_at")


@admin.register(Plot)
class PlotAdmin(admin.ModelAdmin):
    list_display = (
        "plot_name",
        "plot_code",
        "owner",
        "availability_status",
        "cost",
        "amount_paid",
        "is_active",
        "is_subdivided",
        "created_at",
    )
    search_fields = (
        "plot_name",
        "plot_code",
        "owner__first_name",
        "owner__other_name",
        "owner__surname",
    )
    list_filter = (
        "availability_status",
        "is_active",
        "is_subdivided",
        "created_at",
    )


@admin.register(Marker)
class MarkerAdmin(admin.ModelAdmin):
    list_display = (
        "marker_name",
        "plot",
        "marker_order",
        "latitude",
        "longitude",
        "created_at",
    )
    search_fields = (
        "marker_name",
        "plot__plot_name",
    )
    list_filter = ("plot",)


@admin.register(PlotMedia)
class PlotMediaAdmin(admin.ModelAdmin):
    list_display = (
        "plot",
        "media_type",
        "media_role",
        "title",
        "uploaded_at",
    )
    search_fields = (
        "plot__plot_name",
        "title",
    )
    list_filter = (
        "media_type",
        "media_role",
        "uploaded_at",
    )

    


    