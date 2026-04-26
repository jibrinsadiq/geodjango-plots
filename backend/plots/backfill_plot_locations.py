from .models import Plot
from .views import assign_plot_location_fields


def run():
    plots = Plot.objects.exclude(polygon__isnull=True).order_by("id")
    updated_count = 0

    for plot in plots:
        assign_plot_location_fields(plot)
        plot.save(update_fields=["town_name", "lga_name", "state_name", "updated_at"])
        updated_count += 1
        print(f"Updated plot {plot.id}: {plot.plot_name}")

    print(f"Done. Updated {updated_count} plots.")