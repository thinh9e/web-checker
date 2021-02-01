from django import forms


class SiteForm(forms.Form):
    url = forms.CharField(max_length=300, required=True)
