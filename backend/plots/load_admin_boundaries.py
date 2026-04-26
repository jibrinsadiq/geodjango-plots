from django.contrib.gis.utils import LayerMapping

from .models import AdminBoundary


admin_boundary_mapping = {
    "LGA": "LGA",
    "STATENAME": "STATENAME",
    "City": "City",
    "STATE": "STATE",
    "geom": "MULTIPOLYGON",
}


def run(strict=True, verbose=True):
    shapefile = "/app/data/admin_boundaries/AdministrativeBoundary.shp"

    lm = LayerMapping(
        AdminBoundary,
        shapefile,
        admin_boundary_mapping,
        transform=True,
        encoding="utf-8",
    )
    lm.save(strict=strict, verbose=verbose)