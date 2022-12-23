from django import template

register = template.Library()

@register.simple_tag
def project_leads(project, semester):
    return project.enrollments.filter(semester=semester, is_project_lead=True)

@register.simple_tag
def enrollment_count(enrollments, semester) -> int:
    return enrollments.filter(semester=semester).count()