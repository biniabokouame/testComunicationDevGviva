from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse

from .models import Document, PendingDocument
from .forms import UploadDocumentForm
from .tasks import process_document_task


def upload_document(request):
    form = UploadDocumentForm()

    if request.method == "POST":
        form = UploadDocumentForm(request.POST, request.FILES)

        if form.is_valid():
            uploaded_file = request.FILES["file"]

            document = Document.objects.create(
                file=uploaded_file,
                filename=uploaded_file.name,
                status="processing"
            )

            request.session["last_uploaded_document_id"] = document.id

            process_document_task.delay(document.id)

            messages.success(
                request,
                "Fichier reçu. Traitement lancé en arrière-plan."
            )

            return redirect("upload_document")

    documents = Document.objects.filter(status="saved").order_by("-created_at")
    pending_documents = PendingDocument.objects.filter(status="pending").order_by("-created_at")

    return render(request, "documents/upload.html", {
        "form": form,
        "documents": documents,
        "pending_documents": pending_documents,
    })


def documents_status_api(request):
    documents = Document.objects.filter(status="saved").order_by("-created_at")
    pending_documents = PendingDocument.objects.filter(status="pending").order_by("-created_at")

    latest_status = None
    last_uploaded_document_id = request.session.get("last_uploaded_document_id")

    if last_uploaded_document_id:
        latest_document = Document.objects.filter(id=last_uploaded_document_id).first()

        if latest_document:
            if latest_document.status == "processing":
                latest_status = {
                    "type": "warning",
                    "message": "⏳ Traitement du fichier en cours..."
                }

            elif latest_document.status == "saved":
                latest_status = {
                    "type": "success",
                    "message": "✅ Fichier enregistré avec succès."
                }

            elif latest_document.status == "duplicate":
                latest_status = {
                    "type": "error",
                    "message": "❌ Fichier identique détecté : upload impossible."
                }

            elif latest_document.status == "pending_validation":
                pending = PendingDocument.objects.filter(
                    new_document=latest_document,
                    status="pending"
                ).first()

                if pending:
                    latest_status = {
                        "type": "warning",
                        "message": (
                            f"⚠️ Action requise : fichier similaire détecté "
                            f"({pending.similarity_score}%). "
                            f"Validation administrateur nécessaire."
                        )
                    }
                else:
                    latest_status = {
                        "type": "warning",
                        "message": "⚠️ Action requise : validation administrateur nécessaire."
                    }

            elif latest_document.status == "error":
                latest_status = {
                    "type": "error",
                    "message": f"❌ Erreur de traitement : {latest_document.error_message}"
                }

    return JsonResponse({
        "latest_status": latest_status,

        "documents": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "file_hash": doc.file_hash or "",
                "status": doc.status,
                "file_url": doc.file.url if doc.file else "",
            }
            for doc in documents
        ],

        "pending_documents": [
            {
                "id": pending.id,
                "new_filename": pending.new_document.filename,
                "old_filename": pending.old_document.filename,
                "similarity_score": pending.similarity_score,
                "old_content": pending.old_document.content[:700] if pending.old_document.content else "",
                "new_content": pending.new_document.content[:700] if pending.new_document.content else "",
                "old_file_url": pending.old_document.file.url if pending.old_document.file else "",
                "new_file_url": pending.new_document.file.url if pending.new_document.file else "",
            }
            for pending in pending_documents
        ],
    })


def validate_pending_document(request, pending_id):
    pending = get_object_or_404(PendingDocument, id=pending_id, status="pending")

    if request.method == "POST":
        with transaction.atomic():
            old_document = pending.old_document
            new_document = pending.new_document

            old_document.file.delete(save=False)

            old_document.file = new_document.file
            old_document.filename = new_document.filename
            old_document.file_hash = new_document.file_hash
            old_document.content = new_document.content
            old_document.status = "saved"
            old_document.error_message = ""
            old_document.save()

            pending.status = "validated"
            pending.save(update_fields=["status"])

            new_document.delete()

        messages.success(
            request,
            "Validation acceptée : l'ancien fichier a été remplacé par le nouveau."
        )

    return redirect("upload_document")


def reject_pending_document(request, pending_id):
    pending = get_object_or_404(PendingDocument, id=pending_id, status="pending")

    if request.method == "POST":
        new_document = pending.new_document

        new_document.file.delete(save=False)

        pending.status = "rejected"
        pending.save(update_fields=["status"])

        new_document.delete()

        messages.error(
            request,
            "Validation refusée : le nouveau fichier n'a pas été enregistré."
        )

    return redirect("upload_document")


def delete_document(request, document_id):
    document = get_object_or_404(Document, id=document_id, status="saved")

    if request.method == "POST":
        document.file.delete(save=False)
        document.delete()

        messages.success(request, "Fichier supprimé avec succès.")

    return redirect("upload_document")