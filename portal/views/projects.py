"""Views related to projects."""
import logging
import re
from collections import defaultdict
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.cache import cache
from django.core.paginator import EmptyPage, InvalidPage, PageNotAnInteger, Paginator
from django.db.models.functions import Lower
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
)
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.generic.edit import CreateView
from gql.transport.exceptions import TransportServerError

from portal.checks import (
    CheckUserCanCreateProject,
    CheckUserCanEnroll,
    CheckUserCanPitchProject,
    CheckUserCanSubmitProjectProposal,
    CheckUserIsProjectLeadOrOwner,
)
from portal.forms import ProjectCreateForm, ProjectEditForm
from portal.services import github

from ..models import (
    Enrollment,
    Organization,
    Project,
    ProjectPitch,
    ProjectProposal,
    ProjectRepository,
    Semester,
    User,
)
from . import (
    OrganizationFilteredListView,
    SearchableListView,
    SemesterFilteredListView,
    UserRequiresSetupMixin,
    target_semester_context,
)

logger = logging.getLogger(__name__)

@login_required
def project_lead_index(request: HttpRequest) -> HttpResponse:
    """Shows users options to either start a new project or continue an owned project."""

    check = CheckUserCanCreateProject().check(
        request.user, semester=cache.get("active_semester")
    )

    if not check.passed:
        messages.error(
            request,
            f"You cannot lead a project at this time: {check.fail_reason} {check.fix}",
        )
        return redirect(reverse("projects_index"))

    return TemplateResponse(request, "portal/projects/lead_index.html", {})


class ProjectIndexView(
    SearchableListView, OrganizationFilteredListView, SemesterFilteredListView
):
    template_name = "portal/projects/index.html"
    context_object_name = "projects"
    paginate_by = 25

    # Default to all approved projects
    queryset = (
        Project.objects.filter(is_approved=True)
        .prefetch_related("tags", "pitches")
        .select_related("owner", "organization")
    )
    semester_filter_key = "enrollments__semester"
    search_fields = (
        "name",
        "owner__first_name",
        "owner__last_name",
        "owner__rcs_id",
        "description",
        "tags__name",
    )

    def get_queryset(self):
        """Apply filters (semester is already handled)."""
        queryset = super().get_queryset()

        self.is_seeking_members = self.request.GET.get("is_seeking_members") == "yes"
        if self.is_seeking_members:
            queryset = queryset.filter(pitches__semester=self.target_semester)
            self.is_seeking_members = True

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["organizations"] = Organization.objects.all()
        data["is_seeking_members"] = self.is_seeking_members

        queryset = self.get_queryset()
        data["total_count"] = queryset.count()
        paginator = Paginator(queryset, self.paginate_by)

        page = self.request.GET.get("page")
        if page is None:
            page = 1

        try:
            projects = paginator.page(page)
        except PageNotAnInteger:
            projects = paginator.page(1)
        except (EmptyPage, InvalidPage):
            projects = paginator.page(paginator.num_pages)

        projects_rows = []
        enrollments = Enrollment.objects.filter(project__in=projects).select_related(
            "user", "semester"
        )
        if self.target_semester:
            enrollments = enrollments.filter(semester=self.target_semester)

            if self.request.user.is_authenticated:
                data["can_create_project_check"] = CheckUserCanCreateProject().check(
                    self.request.user, self.target_semester
                )

        enrollments_by_project: dict[int, list[Enrollment]] = defaultdict(list)
        leads_by_project: dict[int, list[Enrollment]] = defaultdict(list)
        for enrollment in enrollments:
            enrollments_by_project[enrollment.project_id].append(enrollment)
            if self.target_semester and enrollment.is_project_lead:
                leads_by_project[enrollment.project_id].append(enrollment)

        for project in projects:
            projects_row = {
                "project": project,
                "enrollments": len(enrollments_by_project.get(project.pk, [])),
            }
            if self.target_semester:
                projects_row["leads"] = leads_by_project.get(project.pk, [])
                projects_row["pitch"] = next(
                    (
                        pitch
                        for pitch in project.pitches.all()
                        if pitch.semester_id == self.target_semester.pk
                    ),
                    None,
                )
            projects_rows.append(projects_row)

        data["projects_rows"] = projects_rows

        return data


def project_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """Fetches a project and its details either at the semester level or aggregated across all semesters."""

    project: Project = get_object_or_404(
        Project.objects.approved()
        .prefetch_related("tags", "pitches")
        .select_related("owner", "organization"),
        slug=slug,
    )
    context: dict[str, Any] = {"project": project} | target_semester_context(request)

    active_enrollment = None
    if request.user.is_authenticated:
        active_enrollment = request.user.get_active_enrollment()
        context["active_enrollment"] = active_enrollment
        
        if active_enrollment and active_enrollment.project == project and active_enrollment.is_project_lead:
            is_owner_or_lead = True
        elif project.owner == request.user:
            is_owner_or_lead = True
        else:
            is_owner_or_lead = False

        context["is_owner_or_lead"] = is_owner_or_lead

        # Populate all enrolled students RCS IDs for easy adding team members
        if is_owner_or_lead and active_enrollment:
            context[
                "enrolled_rcs_ids"
            ] = active_enrollment.semester.students.values_list("rcs_id", flat=True)

    # Fetch enrollments for either target semester or teams across semesters
    if "target_semester" in context:
        context["target_semester_enrollments"] = project.get_semester_team(
            context["target_semester"]
        )
        context["can_enroll"] = CheckUserCanEnroll().passes(request.user, context["target_semester"], None) and (active_enrollment is None or active_enrollment.project is None)
    else:
        context["enrollments_by_semester"] = project.get_all_teams()

    # Fetch project repositories
    try:
        context["repositories"] = project.get_repositories(github.client_factory())
    except Exception as e:
        logger.error(e)
        context["repositories"] = []

    return TemplateResponse(request, "portal/projects/detail.html", context)


@login_required
def edit_project(request: HttpRequest, slug: str) -> HttpResponse:
    """Allows project owners and active leads to edit project metadata."""
    context = {}

    # Fetch project
    project: Project = get_object_or_404(
        Project.objects.approved()
        .prefetch_related("tags", "pitches")
        .select_related("owner", "organization"),
        slug=slug,
    )
    context: dict[str, Any] = {"project": project}

    # Check permission to edit project
    check = CheckUserIsProjectLeadOrOwner().check(request.user, Semester.get_active(), project)
    if not check.passed:
        messages.error(request, f"You cannot edit this project: {check.fail_reason} {check.fix}")
        return redirect(project.get_absolute_url())

    # Handle form
    if request.method == "POST":
        form = ProjectEditForm(request.POST, instance=project)

        # Attempt to parse repository URLs
        repository_urls = [url.strip().lower() for url in request.POST.get("repositories", "").split(",")]
        ProjectRepository.objects.filter(project=project).exclude(url__in=repository_urls).delete()
        for url in repository_urls:
            if url:
                # Check if valid GitHub repository URL
                if github.GITHUB_REPO_REGEX.match(url):
                    try:
                        ProjectRepository.objects.get_or_create(url=url, project=project)
                    except:
                        messages.warning(request, f"Couldn't add repository '{url}'")
                else:
                    messages.warning(request, f"Invalid GitHub repository url, ignoring!")

        if form.is_valid():
            messages.success(request, f"{project.name} was updated.")
            form.save()
            return redirect(project.get_absolute_url())
    else:
        form = ProjectEditForm(instance=project)

    context["form"] = form

    return TemplateResponse(request, "portal/projects/edit.html", context)

@login_required
def modify_project_team(request: HttpRequest, slug: str) -> HttpResponse:
    """Add/remove team members for a project."""

    project: Project = get_object_or_404(Project.objects.approved(), slug=slug)

    semester_id = request.GET["semester"]
    semester = get_object_or_404(Semester.objects.all(), pk=semester_id)

    # Logged in user must be project lead to modify team
    try:
        Enrollment.objects.get(
            semester_id=semester.pk,
            user_id=request.user.pk,
            project_id=project.pk,
            is_project_lead=True,
        )
    except Enrollment.DoesNotExist:
        return HttpResponseForbidden()

    if request.method == "POST":
        action = request.GET["action"]
        rcs_id = request.POST.get("rcs_id", None)
        user_id = request.POST.get("user_id", None)

        if not rcs_id and not user_id:
            raise HttpResponseBadRequest("No RCS ID or user ID provided.")
        
        # Find user either by RCS ID or ID
        if rcs_id:
            user: User = get_object_or_404(User.rpi, rcs_id=rcs_id)
        else:
            user: User = get_object_or_404(User.objects.approved(), pk=user_id)

        if action == "add":
            Enrollment.objects.update_or_create(
                user=user,
                semester=semester,
                defaults={"project": project},
            )
            messages.success(request, f"{user} was added to the team for {semester}.")
            # Notify user
            user.send_message(f"{request.user.discord_mention} added you to the **{project}** team on RCOS IO! {settings.PUBLIC_BASE_URL}{project.get_absolute_url()}?semester={semester_id}")
        elif action == "remove":
            user.enrollments.filter(semester=semester_id).update(project=None)
            # Notify user
            user.send_message(f"{request.user.discord_mention} removed you from the **{project}** team on RCOS IO.")
            messages.info(request, f"{user} was removed from the team for {semester}.")
        else:
            raise HttpResponseBadRequest()

    return redirect(
        reverse("projects_detail", args=(slug,)) + "?semester=" + semester_id
    )


class ProjectCreateView(
    SuccessMessageMixin, LoginRequiredMixin, UserRequiresSetupMixin, CreateView
):
    form_class = ProjectCreateForm
    template_name = "portal/projects/create.html"
    success_message = (
        "Your project has been created and you've been enrolled as Project Lead!"
    )

    def get(self, request, *args, **kwargs):
        active_semester = Semester.get_active()

        check = CheckUserCanCreateProject().check(self.request.user, active_semester)

        if not check.passed:
            messages.error(
                self.request,
                f"You are not currently eligible to create new projects: {check.fail_reason} {check.fix}",
            )
            return redirect(reverse("projects_index"))

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        active_semester = Semester.get_active()
        if not CheckUserCanCreateProject().passes(self.request.user, active_semester, None):
            messages.error(
                self.request, "You are not currently eligible to create new projects."
            )
            return redirect(reverse("projects_index"))

        form.instance.owner = self.request.user
        form.instance.organization = self.request.user.organization

        # Enroll user in project as lead

        response = super().form_valid(form)
        Enrollment.objects.update_or_create(
            semester=active_semester,
            user=self.request.user,
            defaults={"is_project_lead": True, "project": form.instance},
        )
        return response


class ProjectAddPitch(CreateView, LoginRequiredMixin, SuccessMessageMixin):
    model = ProjectPitch
    template_name = "portal/projects/pitch.html"
    fields = ["url"]
    success_url = "/"
    success_message = "You project pitch was submitted!"

    def get_context_data(self, **kwargs: Any):
        data = super().get_context_data(**kwargs)
        data["project"] = self.project
        data["semester"] = self.semester
        return data

    def get(self, request, *args: str, **kwargs: Any):
        self.semester = Semester.get_active()
        self.project = Project.objects.get(slug=self.kwargs["slug"])

        check = CheckUserCanPitchProject().check(
            self.request.user, self.semester, self.project
        )
        if not check.passed:
            messages.error(
                self.request,
                f"You are not currently eligible to pitch this project: {check.fail_reason} {check.fix}",
            )
            return redirect(reverse("projects_index"))

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        self.semester = Semester.get_active()
        self.project = Project.objects.get(slug=self.kwargs["slug"])

        check = CheckUserCanPitchProject().check(
            self.request.user, self.semester, self.project
        )
        if not check.passed:
            messages.error(
                self.request,
                f"You are not currently eligible to pitch this project: {check.fail_reason} {check.fix}",
            )
            return redirect(reverse("projects_index"))

        form.instance.semester = self.semester
        form.instance.project = self.project
        return super().form_valid(form)


class ProjectAddProposal(CreateView, LoginRequiredMixin, SuccessMessageMixin):
    model = ProjectProposal
    template_name = "portal/projects/proposal.html"
    fields = ["url"]
    success_url = "/"
    success_message = "Your project proposal document was submitted!"

    def get_context_data(self, **kwargs: Any):
        data = super().get_context_data(**kwargs)
        data["project"] = self.project
        data["semester"] = self.semester
        return data

    def get(self, request, *args: str, **kwargs: Any):
        self.semester = Semester.get_active()
        self.project = Project.objects.get(slug=self.kwargs["slug"])

        # Check permission to submit proposal
        check = CheckUserCanSubmitProjectProposal().check(
            self.request.user, self.semester, self.project
        )
        if not check.passed:
            messages.error(
                self.request,
                f"You are not currently eligible to submit a project proposal: {check.fail_reason} {check.fix}",
            )
            return redirect(reverse("projects_index"))

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        self.semester = Semester.get_active()
        self.project = Project.objects.get(slug=self.kwargs["slug"])

        # Check permission to submit proposal
        check = CheckUserCanSubmitProjectProposal().check(
            self.request.user, self.semester, self.project
        )
        if not check.passed:
            messages.error(
                self.request,
                f"You are not currently eligible to submit a project proposal: {check.fail_reason} {check.fix}",
            )
            return redirect(reverse("projects_index"))

        form.instance.semester = self.semester
        form.instance.project = self.project
        return super().form_valid(form)
