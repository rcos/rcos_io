from django import forms
from portal.models import User, Project


class UserProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].widget.attrs.update({"class": "input"})
        self.fields["last_name"].widget.attrs.update({"class": "input"})
        self.fields["graduation_year"].widget.attrs.update({"class": "input"})

    class Meta:
        model = User
        fields = ["first_name", "last_name", "graduation_year"]


class ProposeProjectForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs.update({"class": "input"})
        self.fields["summary"].widget.attrs.update({"class": "input"})
        self.fields["external_chat_url"].widget.attrs.update({"class": "input"})
        self.fields["homepage_url"].widget.attrs.update({"class": "input"})

    class Meta:
        model = Project
        fields = ["name", "summary", "tags", "external_chat_url", "homepage_url"]


class UploadSubmittyDataForm(forms.Form):
    submitty_csv = forms.FileField()
