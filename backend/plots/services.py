
from django.contrib.gis.geos import Polygon, Point
from django.core.exceptions import ValidationError
from .models import Marker


def build_polygon_from_markers(plot):
    markers = list(plot.markers.order_by("marker_order"))

    if len(markers) < 3:
        raise ValidationError("A plot must have at least 3 markers.")

    coords = [(marker.longitude, marker.latitude) for marker in markers]

    if coords[0] != coords[-1]:
        coords.append(coords[0])

    polygon = Polygon(coords, srid=4326)

    if not polygon.valid:
        raise ValidationError("The marker coordinates do not form a valid polygon.")

    return polygon




def extract_markers_from_polygon(plot):
    if not plot.polygon:
        raise ValidationError("Plot has no polygon to extract markers from.")

    coords = list(plot.polygon.coords[0])

    # remove closing coordinate if repeated
    if len(coords) > 1 and coords[0] == coords[-1]:
        coords = coords[:-1]

    created_markers = []

    for index, (longitude, latitude) in enumerate(coords, start=1):
        marker = Marker.objects.create(
            plot=plot,
            marker_name=f"temp{index}",
            marker_order=index,
            longitude=longitude,
            latitude=latitude,
            point=Point(longitude, latitude, srid=4326),
        )
        created_markers.append(marker)

    return created_markers


from django.db import connection


def compute_plot_area(plot):
    if not plot.polygon:
        return None, None

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                ST_Area(%s::geography) AS area_sqm
            """,
            [plot.polygon.ewkt],
        )
        row = cursor.fetchone()

    area_sqm = float(row[0]) if row and row[0] is not None else None
    area_hectares = area_sqm / 10000 if area_sqm is not None else None

    return area_sqm, area_hectares

from .models import Plot


def validate_plot_overlap(polygon, exclude_plot_id=None):
    candidate_plots = Plot.objects.filter(
        is_active=True,
        polygon__isnull=False,
        polygon__intersects=polygon,
    )

    if exclude_plot_id:
        candidate_plots = candidate_plots.exclude(id=exclude_plot_id)

    bad_plots = []

    for existing_plot in candidate_plots:
        existing_polygon = existing_plot.polygon

        # Allow boundary-only contact
        if existing_polygon.touches(polygon):
            continue

        # Anything else that intersects is not allowed
        bad_plots.append(existing_plot.plot_name)

    if bad_plots:
        names = ", ".join(bad_plots)
        raise ValidationError(
            f"Polygon overlaps or conflicts with existing plot(s): {names}"
        )
    
    
    

