from django import forms
from .models import Plot, Marker, Owner, PlotMedia



class MarkerForm(forms.ModelForm):
    class Meta:
        model = Marker
        fields = ["marker_name", "marker_order", "longitude", "latitude"]


class PlotMarkerCoordinatesForm(forms.ModelForm):
    marker_rows = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows": 8,
                "cols": 100,
                "placeholder": "M1,1,3.0000,6.0000\nM2,2,3.1000,6.0000\nM3,3,3.1000,6.1000\nM4,4,3.0000,6.1000",
            }
        ),
        help_text="Enter one marker per line as: marker_name,marker_order,longitude,latitude",
        label="Marker Coordinates",
    )

    class Meta:
        model = Plot
        fields = ["plot_name", "plot_code"]


class PlotMapForm(forms.ModelForm):
    class Meta:
        model = Plot
        fields = ["plot_name", "plot_code"]


class SplitPlotForm(forms.ModelForm):
    class Meta:
        model = Plot
        fields = ["plot_name", "plot_code"]



class OwnerForm(forms.ModelForm):
    class Meta:
        model = Owner
        fields = [
            "first_name",
            "other_name",
            "surname",
            "date_of_birth",
            "phone_number",
            "email",
            "address",
            "id_type",
            "id_number",
            "passport_photo",
            "id_image",
            "notes",
        ]


class PlotOwnerAssignForm(forms.ModelForm):
    class Meta:
        model = Plot
        fields = ["owner", "availability_status", "cost", "amount_paid"]



class PlotMediaForm(forms.ModelForm):
    class Meta:
        model = PlotMedia
        fields = ["media_type", "media_role", "title", "file"]

    def clean(self):
        cleaned_data = super().clean()
        media_type = cleaned_data.get("media_type")
        media_role = cleaned_data.get("media_role")

        if media_type == "image" and media_role == "plot_video":
            raise forms.ValidationError("Images cannot use the Plot Video role.")

        if media_type == "video" and media_role != "plot_video":
            raise forms.ValidationError("Videos must use the Plot Video role.")

        return cleaned_data
    
    



