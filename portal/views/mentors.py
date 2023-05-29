from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import CreateView
from portal.checks import CheckUserCanApplyAsMentor

from portal.forms import MentorApplicationForm

from ..models import Semester
from . import (
    UserRequiresSetupMixin,
)

class MentorApplicationView(
    SuccessMessageMixin, LoginRequiredMixin, UserRequiresSetupMixin, CreateView
):
    form_class = MentorApplicationForm
    template_name = "portal/mentors/application.html"
    success_message = "Your application has been submitted and will be reviwed by the Coordinators and Faculty Advisors shortly."
    success_url = reverse_lazy("users_index")

    def get(self, request, *args, **kwargs):
        active_semester = Semester.get_active()

        check = CheckUserCanApplyAsMentor().check(self.request.user, active_semester)
        if not check["passed"]:
            messages.error(
                self.request, f"You are not currently eligible to propose new projects: {check['error'].reason}"
            )
            return redirect(reverse("users_index"))

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        active_semester = Semester.get_active()
        check = CheckUserCanApplyAsMentor().check(self.request.user, active_semester)
        if not check["passed"]:
            messages.error(
                self.request, f"You are not currently eligible to propose new projects: {check['error'].reason}"
            )
            return redirect(reverse("users_index"))

        form.instance.semester = active_semester
        form.instance.user = self.request.user

        # TODO: message admins on Discord

        return super().form_valid(form)