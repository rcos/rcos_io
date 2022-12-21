from django.urls import path

from .views.meetings import MeetingIndexView, MeetingDetailView, meetings_api
from .views.users import UserIndexView, UserDetailView

urlpatterns = [
    path("users/", UserIndexView.as_view(), name="users_index"),
    path("users/<int:pk>", UserDetailView.as_view(), name="users_detail"),
    path("meetings/", MeetingIndexView.as_view(), name="meetings_index"),
    path("meetings/api", meetings_api, name="meetings_api"),
    path("meetings/<int:pk>", MeetingDetailView.as_view(), name="meetings_detail"),
]
