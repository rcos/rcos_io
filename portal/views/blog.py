"""Views related to external organizations."""
from typing import Any
from django.db import models
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from portal.forms import BlogPostCreateForm, BlogPostEditForm

from ..models import BlogPost

class BlogPostListView(ListView):
    model = BlogPost
    paginate_by = 10
    template_name = "portal/blog/index.html"
    
class BlogPostView(DetailView):
    model = BlogPost
    template_name = "portal/blog/post.html"
    
def edit_blog_post(request: HttpRequest, pk: int) -> HttpResponse:
    post: BlogPost = get_object_or_404(BlogPost, pk=pk)
    
    if request.method == "POST":
        form = BlogPostEditForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect(post.get_absolute_url())
    else:
        form = BlogPostEditForm(instance=post)

    return TemplateResponse(request, "portal/blog/edit.html", {
        "post": post,
        "form": form,
    })