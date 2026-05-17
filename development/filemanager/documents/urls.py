from django.urls import path

from .views import (
    upload_document,
    documents_status_api,
    validate_pending_document,
    reject_pending_document,
    delete_document,
)


urlpatterns = [
    path("", upload_document, name="upload_document"),
    path("api/status/", documents_status_api, name="documents_status_api"),
    path("pending/<int:pending_id>/validate/", validate_pending_document, name="validate_pending_document"),
    path("pending/<int:pending_id>/reject/", reject_pending_document, name="reject_pending_document"),
    path("delete/<int:document_id>/", delete_document, name="delete_document"),
]