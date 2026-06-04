from django.urls import path
from . import views

app_name = 'hod_management'

urlpatterns = [

    path("", views.hod_program_map_management, name="hod_management"),
    # Main page
    path("hod-program-map/", views.hod_program_map_management, name="hod_program_map"),
    
    # CRUD operations
    path("get-mapping/<int:mapping_id>/", views.get_mapping, name="get_mapping"),
    path("add-mapping/", views.add_mapping, name="add_mapping"),
    path("edit-mapping/<int:mapping_id>/", views.edit_mapping, name="edit_mapping"),
    path("delete-mapping/<int:mapping_id>/", views.delete_mapping, name="delete_mapping"),
    
    # Excel operations
    path("download-sample/", views.download_sample_mapping_excel, name="download_sample"),
    path("download-mappings/", views.download_mappings_excel, name="download_mappings"),
    path("upload-mappings/", views.upload_mappings_excel, name="upload_mappings"),
    
    # Helper endpoints
    path("get-hods/", views.get_hods_list, name="get_hods"),
    path("get-programs/", views.get_programs_list, name="get_programs"),
]