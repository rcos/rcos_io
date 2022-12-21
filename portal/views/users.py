from django.views.generic import ListView, DetailView
from ..models import User


class UserIndexView(ListView):
    template_name = "portal/users/index.html"
    context_object_name = "users"

    # Only show approved users
    queryset = User.objects.filter(is_approved=True)


class UserDetailView(DetailView):
    template_name = "portal/users/detail.html"
    model = User
    context_object_name = "user"
