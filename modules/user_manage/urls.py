from django.urls import path
from . import views

app_name = 'user_manage'

urlpatterns = [
    
    # Main page
    path("", views.user_management, name="user_management"),
    
    # User CRUD operations
    path("get_user/<int:user_id>/", views.get_user, name="get_user"),
    path("add/", views.add_user, name="add_user"),
    path("edit/<int:user_id>/", views.edit_user, name="edit_user"),
    path("delete/<int:user_id>/", views.delete_user, name="delete_user"),
    
    # Excel operations
    path("download-sample/", views.download_sample_excel, name="download_sample"),
    path("download-users/", views.download_users_excel, name="download_users"),
    path("upload-users/", views.upload_users_excel, name="upload_users"),
]