from django import forms


class UploadSubmittyDataForm(forms.Form):
    submitty_csv = forms.FileField()
