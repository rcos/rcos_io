

from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from portal.services import github
from django.core.cache import cache;
from portal.tasks import get_commits;

@login_required
def commits_index(request: HttpRequest) -> HttpResponse:
    active_enrollment = request.user.get_active_enrollment()
    commits = {}
    
    if active_enrollment is not None:
        repos = active_enrollment.project.repositories.all()
        for repo in repos:
            repo_commits = cache.get(f"repo_commits_{repo.url}")
            if repo_commits:
                for url in repo_commits:
                    commits[url] = repo_commits[url]

    return TemplateResponse(request, "portal/commits/index.html", {
        "commits": commits,
        "username": request.user.github_username
    })