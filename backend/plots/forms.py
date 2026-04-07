from django import forms
from .models import Plot, Marker


class PlotForm(forms.ModelForm):
    class Meta:
        model = Plot
        fields = ["plot_name", "plot_code"]


class MarkerForm(forms.ModelForm):
    class Meta:
        model = Marker
        fields = ["marker_name", "marker_order", "longitude", "latitude"]


from django import forms
from .models import Plot, Marker


class PlotForm(forms.ModelForm):
    class Meta:
        model = Plot
        fields = ["plot_name", "plot_code"]


class MarkerForm(forms.ModelForm):
    class Meta:
        model = Marker
        fields = ["marker_name", "marker_order", "longitude", "latitude"]


class PlotPolygonForm(forms.ModelForm):
    polygon_text = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 5, "cols": 80}),
        help_text="Enter coordinates as longitude,latitude per line. Example: 3.0,6.0"
    )

    class Meta:
        model = Plot
        fields = ["plot_name", "plot_code"]


class PlotMapForm(forms.ModelForm):
    class Meta:
        model = Plot
        fields = ["plot_name", "plot_code"]        


class ChildPlotForm(forms.ModelForm):
    class Meta:
        model = Plot
        fields = ["plot_name", "plot_code"]



