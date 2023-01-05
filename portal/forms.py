from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout, Submit
from django import forms
from django.core.exceptions import ValidationError

from portal.models import MeetingAttendanceCode, Project, Semester, User


class BulmaTextInput(forms.Widget):
    template_name = "portal/widgets/text_input.html"


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "graduation_year"]


class ChangeEmailForm(forms.Form):
    new_email = forms.EmailField(
        help_text="Change the email you use to login. This is useful to avoid the RPI VPN.",
        widget=forms.EmailInput(attrs={"class": "input"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        # Check if user with this email already exists
        try:
            User.objects.get(email=cleaned_data.get("new_email"))
            raise ValidationError("Email is already in use.")
        except User.DoesNotExist:
            pass


class ProposeProjectForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data["owner"] and not cleaned_data["owner"].is_approved:
            raise ValidationError(
                "Only approved users can propose projects.", code="unapproved-owner"
            )

    class Meta:
        model = Project
        fields = ["name", "summary", "tags", "external_chat_url", "homepage_url"]


class UploadSubmittyDataForm(forms.Form):
    semester = forms.ModelChoiceField(queryset=Semester.objects.all())
    submitty_csv = forms.FileField()


class SubmitAttendanceCodeForm(forms.Form):
    code = forms.CharField(
        help_text="The attendance code your Mentor or meeting host displayed"
    )
