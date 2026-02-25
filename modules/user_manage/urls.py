from django.urls import path
from . import views

app_name = 'user_manage'
urlpatterns = [
    path("", views.user_management, name="user_management"),
    path("edit/<int:user_id>/", views.edit_user, name="edit_user"),
    path("add/", views.add_user, name="add_user"),
]