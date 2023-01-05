from django import forms
from portal.models import User, Project, Semester
from django.core.exceptions import ValidationError


class BulmaTextInput(forms.Widget):
    template_name = "portal/widgets/text_input.html"


class UserProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].widget.attrs.update({"class": "input"})
        self.fields["last_name"].widget.attrs.update({"class": "input"})
        self.fields["graduation_year"].widget.attrs.update({"class": "input"})

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
