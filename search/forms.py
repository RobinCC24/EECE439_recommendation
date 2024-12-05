from django import forms
from .models import Surgeon

class SurgeonForm(forms.ModelForm):
    class Meta:
        model = Surgeon
        fields = '__all__'

class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(label="Upload CSV")