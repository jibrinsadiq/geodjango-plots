from django.contrib.gis.db import models
from django.core.validators import MinValueValidator
from django.contrib.gis.db import models as gis_models


class Owner(models.Model):
    ID_TYPE_CHOICES = [
        ("national_id", "National ID"),
        ("passport", "Passport"),
        ("drivers_license", "Driver's License"),
        ("voters_card", "Voter's Card"),
        ("other", "Other"),
    ]

    first_name = models.CharField(max_length=100)
    other_name = models.CharField(max_length=100, blank=True, null=True)
    surname = models.CharField(max_length=100)
    date_of_birth = models.DateField(blank=True, null=True)

    phone_number = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    id_type = models.CharField(max_length=30, choices=ID_TYPE_CHOICES, blank=True, null=True)
    id_number = models.CharField(max_length=100, blank=True, null=True)

    passport_photo = models.ImageField(upload_to="owners/passports/", blank=True, null=True)
    id_image = models.ImageField(upload_to="owners/id_cards/", blank=True, null=True)

    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["surname", "first_name", "other_name"]

    def __str__(self):
        name_parts = [self.first_name]
        if self.other_name:
            name_parts.append(self.other_name)
        name_parts.append(self.surname)
        return " ".join(name_parts)


class Plot(models.Model):
    AVAILABILITY_STATUS_CHOICES = [
        ("available", "Available"),
        ("reserved", "Reserved"),
        ("sold", "Sold"),
        ("unavailable", "Unavailable"),
    ]

    plot_name = models.CharField(max_length=200, unique=True)
    plot_code = models.CharField(max_length=100, unique=True, blank=True, null=True)

    polygon = models.PolygonField(srid=4326, null=True, blank=True)
    area_sqm = models.FloatField(blank=True, null=True)
    area_hectares = models.FloatField(blank=True, null=True)

    town_name = models.CharField(max_length=255, blank=True, null=True)
    lga_name = models.CharField(max_length=255, blank=True, null=True)
    state_name = models.CharField(max_length=255, blank=True, null=True)


    parent_plot = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sub_plots",
    )

    owner = models.ForeignKey(
        Owner,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="plots",
    )

    availability_status = models.CharField(
        max_length=20,
        choices=AVAILABILITY_STATUS_CHOICES,
        default="available",
    )

    cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
    )

    amount_paid = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
    )

    is_active = models.BooleanField(default=True)
    is_subdivided = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["plot_name"]

    def __str__(self):
        return self.plot_name

    @property
    def balance(self):
        if self.cost is None:
            return None
        paid = self.amount_paid or 0
        return self.cost - paid

    @property
    def image_count(self):
        return self.media_files.filter(media_type="image").count()

    @property
    def video_count(self):
        return self.media_files.filter(media_type="video").count()


class Marker(models.Model):
    plot = models.ForeignKey(Plot, on_delete=models.CASCADE, related_name="markers")
    marker_name = models.CharField(max_length=100)
    marker_order = models.PositiveIntegerField()
    point = models.PointField(srid=4326)
    latitude = models.FloatField()
    longitude = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["marker_order"]
        constraints = [
            models.UniqueConstraint(fields=["plot", "marker_order"], name="unique_plot_marker_order"),
            models.UniqueConstraint(fields=["plot", "marker_name"], name="unique_plot_marker_name"),
        ]

    def __str__(self):
        return f"{self.plot.plot_name} - {self.marker_name}"


class PlotMedia(models.Model):
    MEDIA_TYPE_CHOICES = [
        ("image", "Image"),
        ("video", "Video"),
    ]

    MEDIA_ROLE_CHOICES = [
        ("front_view", "Front View"),
        ("back_view", "Back View"),
        ("left_view", "Left Side View"),
        ("right_view", "Right Side View"),
        ("other_view", "Other View"),
        ("plot_video", "Plot Video"),
    ]

    plot = models.ForeignKey(
        Plot,
        on_delete=models.CASCADE,
        related_name="media_files",
    )
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    media_role = models.CharField(max_length=30, choices=MEDIA_ROLE_CHOICES)
    file = models.FileField(upload_to="plots/media/")
    title = models.CharField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.plot.plot_name} - {self.media_role} - {self.media_type}"
    





class PlotDocument(models.Model):
    SALES_AGREEMENT = "sales_agreement"
    DEED_OF_ASSIGNMENT = "deed_of_assignment"
    POWER_OF_ATTORNEY = "power_of_attorney"
    OTHER_DOCUMENT = "other_document"

    DOCUMENT_TYPE_CHOICES = [
        (SALES_AGREEMENT, "Sales Agreement"),
        (DEED_OF_ASSIGNMENT, "Deed of Assignment"),
        (POWER_OF_ATTORNEY, "Power of Attorney"),
        (OTHER_DOCUMENT, "Other Document"),
    ]

    plot = models.ForeignKey(
        "Plot",
        on_delete=models.CASCADE,
        related_name="documents",
    )
    document_type = models.CharField(
        max_length=50,
        choices=DOCUMENT_TYPE_CHOICES,
    )
    title = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    file = models.FileField(
        upload_to="plot_documents/%Y/%m/%d/"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.plot.plot_name}"





class TownBoundary(gis_models.Model):
    fid = gis_models.IntegerField(blank=True, null=True)
    TOWN_NAME = gis_models.CharField(max_length=255, blank=True, null=True)
    TOWN_CATEG = gis_models.CharField(max_length=255, blank=True, null=True)
    PARENT_TOW = gis_models.CharField(max_length=255, blank=True, null=True)
    PARENT_T_1 = gis_models.CharField(max_length=255, blank=True, null=True)
    STATE = gis_models.CharField(max_length=255, blank=True, null=True)
    Town_rank = gis_models.IntegerField(blank=True, null=True)
    Town_cat = gis_models.CharField(max_length=255, blank=True, null=True)
    Update_Ver = gis_models.CharField(max_length=255, blank=True, null=True)

    geom = gis_models.MultiPolygonField(srid=4326)

    created_at = gis_models.DateTimeField(auto_now_add=True)
    updated_at = gis_models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["TOWN_NAME"]

    def __str__(self):
        return self.TOWN_NAME if self.TOWN_NAME else "Unnamed Location"


from django.contrib.gis.db import models as gis_models


class AdminBoundary(gis_models.Model):
    LGA = gis_models.CharField(max_length=255, blank=True, null=True)
    STATENAME = gis_models.CharField(max_length=255, blank=True, null=True)
    City = gis_models.CharField(max_length=255, blank=True, null=True)
    STATE = gis_models.CharField(max_length=255, blank=True, null=True)

    geom = gis_models.MultiPolygonField(srid=4326)

    created_at = gis_models.DateTimeField(auto_now_add=True)
    updated_at = gis_models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["STATENAME", "LGA"]

    def __str__(self):
        if self.LGA and self.STATENAME:
            return f"{self.LGA} ({self.STATENAME})"
        return self.LGA or self.STATENAME or "Unnamed Admin Boundary"
    

