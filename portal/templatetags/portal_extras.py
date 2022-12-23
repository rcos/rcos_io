from django import template

register = template.Library()


@register.simple_tag
def project_leads(project, semester):
    return project.enrollments.filter(semester=semester, is_project_lead=True)


@register.simple_tag
def user_enrollment(user, semester):
    if semester:
        return user.enrollments.filter(semester=semester).get()
    return None


@register.simple_tag
def enrollment_count(enrollments, semester) -> int:
    return enrollments.filter(semester=semester).count()


@register.simple_tag(takes_context=True)
def target_semester_query(context):
    if context["target_semester"]:
        return "?semester=" + context["target_semester"].id
    return ""
