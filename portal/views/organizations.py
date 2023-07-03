"""Views related to external organizations."""
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse


from ..models import Organization

def organizations_index(request: HttpRequest) -> HttpResponse:
    """Renders a list of the organizations that have users and projects in RCOS."""
    return TemplateResponse(request, "portal/organizations/index.html", {
        "organizations": Organization.objects.all()
    })