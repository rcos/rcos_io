from typing import Any, Dict
from django import template

register = template.Library()


@register.simple_tag
def project_leads(project, semester):
    return project.enrollments.filter(semester=semester, is_project_lead=True)


@register.simple_tag
def user_enrollment(user, semester):
    if semester:
        return user.enrollments.filter(semester=semester).first()
    return None


@register.simple_tag
def enrollment_count(enrollments, semester) -> int:
    return enrollments.filter(semester=semester).count()


@register.simple_tag
def project_documents(project, semester) -> Dict[str, Any]:
    return {
        "pitch": project.pitches.filter(semester=semester).first(),
        "proposal": project.proposals.filter(semester=semester).first(),
        "presentation": project.presentations.filter(semester=semester).first(),
    }


@register.simple_tag(takes_context=True)
def target_semester_query(context):
    if context["target_semester"]:
        return "?semester=" + context["target_semester"].id
    return ""
