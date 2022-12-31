from django import forms
from portal.models import User


class UserProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].widget.attrs.update({"class": "input"})
        self.fields["last_name"].widget.attrs.update({"class": "input"})
        self.fields["graduation_year"].widget.attrs.update({"class": "input"})

    class Meta:
        model = User
        fields = ["first_name", "last_name", "graduation_year"]


class UploadSubmittyDataForm(forms.Form):
    submitty_csv = forms.FileField()
