from django import forms
from .models import Plot, Marker, Owner, PlotMedia
from django.contrib.auth.models import User



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
        uploaded_file = cleaned_data.get("file")

        if media_type == "image" and media_role == "plot_video":
            raise forms.ValidationError("Images cannot use the Plot Video role.")

        if media_type == "video" and media_role != "plot_video":
            raise forms.ValidationError("Videos must use the Plot Video role.")

        if not uploaded_file:
            raise forms.ValidationError("Please choose a file to upload.")

        return cleaned_data
    





class BuyerRegistrationForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data


class BuyerLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)



