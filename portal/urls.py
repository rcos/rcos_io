from django.urls import path

from .views.index import IndexView
from .views.meetings import MeetingIndexView, MeetingDetailView, meetings_api
from .views.users import UserIndexView, UserDetailView
from .views.projects import ProjectDetailView, ProjectIndexView

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("users/", UserIndexView.as_view(), name="users_index"),
    path("users/<int:pk>", UserDetailView.as_view(), name="users_detail"),
    path("projects/", ProjectIndexView.as_view(), name="projects_index"),
    path("projects/<int:pk>", ProjectDetailView.as_view(), name="projects_detail"),
    path("meetings/", MeetingIndexView.as_view(), name="meetings_index"),
    path("api/meetings", meetings_api, name="meetings_api"),
    path("meetings/<int:pk>", MeetingDetailView.as_view(), name="meetings_detail"),
]
