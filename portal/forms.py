from django import forms
from portal.models import User, Project, Semester
from django.core.exceptions import ValidationError


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

    def clean(self):
        if self.instance.owner and not self.instance.owner.is_approved:
            raise ValidationError(
                "Only approved users can propose projects.", code="unapproved-owner"
            )
        return super().clean()

    class Meta:
        model = Project
        fields = ["name", "summary", "tags", "external_chat_url", "homepage_url"]


class UploadSubmittyDataForm(forms.Form):
    semester = forms.ModelChoiceField(queryset=Semester.objects.all())
    submitty_csv = forms.FileField()
