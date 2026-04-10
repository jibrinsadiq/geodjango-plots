from django.contrib.gis.geos import Polygon, Point, MultiPolygon

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


def validate_plot_overlap(polygon, exclude_plot_ids=None):
    candidate_plots = Plot.objects.filter(
        is_active=True,
        polygon__isnull=False,
        polygon__intersects=polygon,
    )

    if exclude_plot_ids:
        candidate_plots = candidate_plots.exclude(id__in=exclude_plot_ids)

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




def validate_plot_within_parent(child_polygon, parent_plot):
    if not parent_plot.polygon:
        raise ValidationError("Parent plot has no polygon defined.")

    if not child_polygon.within(parent_plot.polygon):
        raise ValidationError(
            f"Child plot must lie fully within parent plot '{parent_plot.plot_name}'."
        )


def split_plot_geometry(source_plot, cut_polygon):
    if not source_plot.polygon:
        raise ValidationError("Source plot has no polygon defined.")

    remainder = source_plot.polygon.difference(cut_polygon)

    if remainder.empty:
        raise ValidationError("Cut polygon removes the entire source plot.")

    if remainder.geom_type != "Polygon":
        raise ValidationError(
            "This split is not supported yet because the remainder becomes multiple polygons."
        )

    if not remainder.valid:
        raise ValidationError("The remainder geometry is not valid.")

    return remainder



from math import sqrt


def snap_polygon_vertices_to_parent(child_polygon, parent_plot, tolerance=0.0001):
    """
    Snap child polygon vertices to parent plot vertices if they are within tolerance.

    tolerance is in degrees because SRID 4326 is being used.
    0.0001 degrees is roughly ~11m at the equator.
    You can reduce it later if needed.
    """
    if not parent_plot.polygon:
        raise ValidationError("Parent plot has no polygon defined.")

    child_coords = list(child_polygon.coords[0])
    parent_coords = list(parent_plot.polygon.coords[0])

    # remove repeated closing coordinate for comparison
    if len(child_coords) > 1 and child_coords[0] == child_coords[-1]:
        child_coords = child_coords[:-1]

    if len(parent_coords) > 1 and parent_coords[0] == parent_coords[-1]:
        parent_coords = parent_coords[:-1]

    snapped_coords = []

    for child_x, child_y in child_coords:
        snapped_x, snapped_y = child_x, child_y

        for parent_x, parent_y in parent_coords:
            distance = sqrt((child_x - parent_x) ** 2 + (child_y - parent_y) ** 2)
            if distance <= tolerance:
                snapped_x, snapped_y = parent_x, parent_y
                break

        snapped_coords.append((snapped_x, snapped_y))

    # close polygon
    if snapped_coords[0] != snapped_coords[-1]:
        snapped_coords.append(snapped_coords[0])

    snapped_polygon = Polygon(snapped_coords, srid=4326)

    if not snapped_polygon.valid:
        raise ValidationError("Snapped child polygon is not valid.")

    return snapped_polygon



    

