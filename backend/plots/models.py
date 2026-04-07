from django.contrib.gis.db import models


class Plot(models.Model):
    plot_name = models.CharField(max_length=200, unique=True)
    plot_code = models.CharField(max_length=100, unique=True, blank=True, null=True)
    polygon = models.PolygonField(srid=4326, null=True, blank=True)
    area_sqm = models.FloatField(blank=True, null=True)
    area_hectares = models.FloatField(blank=True, null=True)
    parent_plot = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sub_plots'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.plot_name


class Marker(models.Model):
    plot = models.ForeignKey(Plot, on_delete=models.CASCADE, related_name='markers')
    marker_name = models.CharField(max_length=100)
    marker_order = models.PositiveIntegerField()
    point = models.PointField(srid=4326)
    latitude = models.FloatField()
    longitude = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['marker_order']
        constraints = [
            models.UniqueConstraint(fields=['plot', 'marker_order'], name='unique_plot_marker_order'),
            models.UniqueConstraint(fields=['plot', 'marker_name'], name='unique_plot_marker_name'),
        ]

    def __str__(self):
        return f"{self.plot.plot_name} - {self.marker_name}"



