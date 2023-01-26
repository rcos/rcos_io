from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout, Submit
from django import forms
from django.core.exceptions import ValidationError

from portal.models import MeetingAttendanceCode, Project, Semester, User


class BulmaTextInput(forms.Widget):
    template_name = "portal/widgets/text_input.html"


class UserProfileForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
    
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
    class Meta:
        model = Project
        fields = [
            "name",
            "description",
            "tags",
            "external_chat_url",
            "homepage_url",
        ]


class SemesterCSVUploadForm(forms.Form):
    semester = forms.ModelChoiceField(queryset=Semester.objects.all())
    csv = forms.FileField()


class SubmitAttendanceForm(forms.Form):
    code = forms.CharField(
        label="Attendance Code",
        help_text="The attendance code your Mentor or meeting host displayed",
    )

    helper = FormHelper()
    helper.add_input(Submit("submit", "Submit", css_class="button"))
    helper.form_method = "POST"
    helper.form_action = "submit_attendance"
