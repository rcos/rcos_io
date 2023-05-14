from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms

from portal.models import Project, Semester, User

# Inputs


class BulmaTextInput(forms.Widget):
    template_name = "portal/widgets/text_input.html"


# Base Forms


class SemesterForm(forms.Form):
    semester = forms.ModelChoiceField(queryset=Semester.objects.all())


# Forms


class UserProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

    class Meta:
        model = User
        fields = ["first_name", "last_name", "graduation_year"]


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
