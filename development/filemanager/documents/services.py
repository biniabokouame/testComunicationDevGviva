from django.utils import timezone
from django.db import transaction

from .models import Document, PendingDocument
from .utils import (
    generate_sha256_from_path,
    extract_text_from_path,
    similarity_percent,
)


SIMILARITY_THRESHOLD = 90


def process_uploaded_document(document_id):
    document = Document.objects.get(id=document_id)

    try:
        document.status = "processing"
        document.save(update_fields=["status"])

        file_path = document.file.path

        file_hash = generate_sha256_from_path(file_path)
        content = extract_text_from_path(file_path)

        # Cas 2 : fichier identique
        duplicate = Document.objects.filter(
            file_hash=file_hash,
            status="saved"
        ).exclude(id=document.id).first()

        if duplicate:
            document.file_hash = file_hash
            document.content = ""
            document.status = "duplicate"
            document.processed_at = timezone.now()
            document.save(update_fields=[
                "file_hash",
                "content",
                "status",
                "processed_at"
            ])

            document.file.delete(save=False)
            return

        # Cas 3 : fichier similaire >= 90%
        saved_documents = Document.objects.filter(status="saved").exclude(id=document.id)

        for old_document in saved_documents:
            score = similarity_percent(content, old_document.content or "")

            if score >= SIMILARITY_THRESHOLD:
                with transaction.atomic():
                    document.file_hash = file_hash
                    document.content = content
                    document.status = "pending_validation"
                    document.processed_at = timezone.now()
                    document.save(update_fields=[
                        "file_hash",
                        "content",
                        "status",
                        "processed_at"
                    ])

                    PendingDocument.objects.create(
                        old_document=old_document,
                        new_document=document,
                        similarity_score=round(score, 2),
                        comparison_summary="Fichier fortement similaire détecté."
                    )

                return

        # Cas 1 : fichier différent
        document.file_hash = file_hash
        document.content = content
        document.status = "saved"
        document.processed_at = timezone.now()
        document.save(update_fields=[
            "file_hash",
            "content",
            "status",
            "processed_at"
        ])

    except Exception as e:
        document.status = "error"
        document.error_message = str(e)
        document.processed_at = timezone.now()
        document.save(update_fields=[
            "status",
            "error_message",
            "processed_at"
        ])