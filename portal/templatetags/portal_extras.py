from typing import Any, Dict
from django import template
from django.utils import timezone
from portal.models import Enrollment
from django.db.models import Q

register = template.Library()


@register.simple_tag
def project_leads(project, semester):
    if semester and project:
        return project.enrollments.filter(semester=semester, is_project_lead=True)
    return []


@register.simple_tag
def project_enrollments(project, semester):
    if semester and project:
        return project.enrollments.filter(semester=semester).order_by(
            "-is_project_lead"
        )
    return []


@register.simple_tag
def semester_admins(semester):
    if semester:
        return semester.get_admins()
    return []


@register.simple_tag
def user_enrollment(user, semester):
    if semester:
        return user.enrollments.filter(semester=semester).first()
    return None


@register.simple_tag
def enrollment_count(enrollments, semester) -> int:
    if semester:
        return enrollments.filter(semester=semester).count()
    return 0


@register.simple_tag
def project_documents(project, semester) -> Dict[str, Any]:
    if semester:
        return {
            "pitch": project.pitches.filter(semester=semester).first(),
            "proposal": project.proposals.filter(semester=semester).first(),
            "presentation": project.presentations.filter(semester=semester).first(),
        }

    return {"pitch": None, "proposal": None, "presentation": None}


@register.simple_tag
def project_small_group(project, semester) -> Dict[str, Any]:
    if semester:
        return project.small_groups.filter(semester=semester).first()
    return None


@register.simple_tag(takes_context=True)
def target_semester_query(context):
    if "target_semester" in context and context["target_semester"]:
        return "?semester=" + context["target_semester"].id
    return ""


@register.simple_tag(takes_context=True)
def active_semester_query(context):
    if "active_semester" in context and context["active_semester"]:
        return "?semester=" + context["active_semester"].id
    return ""


@register.simple_tag(takes_context=True)
def target_or_active_semester_query(context):
    if "target_semester" in context and context["target_semester"]:
        return "?semester=" + context["target_semester"].id
    if "active_semester" in context and context["active_semester"]:
        return "?semester=" + context["active_semester"].id
    return ""


@register.filter(name="to_date")
def to_date(date_string: str):
    return timezone.datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")


@register.filter(name="to_short_repository")
def to_short_repository(repository_url: str):
    return repository_url.removeprefix("https://github.com/").removeprefix(
        "https://www.github.com/"
    )
