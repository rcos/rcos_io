import datetime
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms

from portal.models import Meeting, MentorApplication, Project, Semester, User

# Inputs



# Base Forms


class SemesterForm(forms.Form):
    semester = forms.ModelChoiceField(queryset=Semester.objects.all())


# Forms


class ExternalUserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "organization"]

class RPIUserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "graduation_year"]

class ProjectCreateForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            "name",
            "description",
            "tags",
            "external_chat_url",
            "logo_url",
            "homepage_url",
        ]

class WorkshopCreateForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = [
            "name",
            "starts_at",
            "ends_at",
            "room",
            "description_markdown",
            "presentation_url"
        ]
    starts_at = forms.DateField(initial=datetime.datetime.now().isoformat(timespec="minutes"),
        widget=forms.widgets.DateTimeInput(attrs={'type': 'datetime-local'}))
    ends_at = forms.DateField(widget=forms.DateTimeInput(attrs={'min': datetime.datetime.now().isoformat(timespec="minutes"), 'type': 'datetime-local'}), required=True)

class SubmitAttendanceForm(forms.Form):
    code = forms.CharField(
        label="Attendance Code",
        help_text="The attendance code your Mentor or meeting host displayed",
    )

    helper = FormHelper()
    helper.add_input(Submit("submit", "Submit", css_class="button"))
    helper.form_method = "POST"
    helper.form_action = "submit_attendance"


class SemesterCSVUploadForm(SemesterForm):
    csv = forms.FileField()

class MentorApplicationForm(forms.ModelForm):
    class Meta:
        model = MentorApplication
        fields = [
            "why",
            "skills",
        ]

