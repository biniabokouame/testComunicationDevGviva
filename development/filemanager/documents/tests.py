import shutil
import tempfile

from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import Document, PendingDocument
from .services import process_uploaded_document


TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class DocumentBusinessRulesTests(TestCase):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def create_document(self, filename, content):
        uploaded_file = SimpleUploadedFile(
            filename,
            content.encode("utf-8"),
            content_type="text/plain"
        )

        return Document.objects.create(
            file=uploaded_file,
            filename=filename,
            status="processing"
        )

    def test_different_file_is_saved(self):
        document = self.create_document(
            "file_unique.txt",
            "Ceci est un contenu totalement unique."
        )

        process_uploaded_document(document.id)

        document.refresh_from_db()

        self.assertEqual(document.status, "saved")
        self.assertIsNotNone(document.file_hash)
        self.assertIn("contenu totalement unique", document.content)

    def test_identical_file_is_rejected_as_duplicate(self):
        first_document = self.create_document(
            "original.txt",
            "Même contenu pour tester le doublon."
        )

        process_uploaded_document(first_document.id)
        first_document.refresh_from_db()

        self.assertEqual(first_document.status, "saved")

        second_document = self.create_document(
            "copy.txt",
            "Même contenu pour tester le doublon."
        )

        process_uploaded_document(second_document.id)
        second_document.refresh_from_db()

        self.assertEqual(second_document.status, "duplicate")
        self.assertEqual(PendingDocument.objects.count(), 0)

    def test_similar_file_goes_to_pending_validation(self):
        original = self.create_document(
            "contrat_original.txt",
            "Ce document contient les conditions générales du contrat client avec les informations principales."
        )

        process_uploaded_document(original.id)
        original.refresh_from_db()

        similar = self.create_document(
            "contrat_modifie.txt",
            "Ce document contient les conditions générales du contrat client avec les informations principales modifiées."
        )

        process_uploaded_document(similar.id)
        similar.refresh_from_db()

        self.assertEqual(similar.status, "pending_validation")
        self.assertEqual(PendingDocument.objects.count(), 1)

        pending = PendingDocument.objects.first()

        self.assertEqual(pending.old_document, original)
        self.assertEqual(pending.new_document, similar)
        self.assertGreaterEqual(pending.similarity_score, 90)

    def test_admin_validation_replaces_old_document(self):
        original = self.create_document(
            "old.txt",
            "Ancien contenu du fichier important pour le client."
        )

        process_uploaded_document(original.id)
        original.refresh_from_db()

        similar = self.create_document(
            "new.txt",
            "Ancien contenu du fichier important pour le client mis à jour."
        )

        process_uploaded_document(similar.id)
        similar.refresh_from_db()

        pending = PendingDocument.objects.first()
        pending_id = pending.id

        old_document = pending.old_document
        new_document = pending.new_document

        old_document.file = new_document.file
        old_document.filename = new_document.filename
        old_document.file_hash = new_document.file_hash
        old_document.content = new_document.content
        old_document.status = "saved"
        old_document.save()

        pending.status = "validated"
        pending.save()

        new_document.delete()

        old_document.refresh_from_db()

        self.assertEqual(old_document.filename, "new.txt")
        self.assertEqual(old_document.status, "saved")
        self.assertFalse(PendingDocument.objects.filter(id=pending_id).exists())

    def test_admin_rejection_refuses_new_file(self):
        original = self.create_document(
            "base.txt",
            "Document de référence contenant toutes les données principales."
        )

        process_uploaded_document(original.id)
        original.refresh_from_db()

        similar = self.create_document(
            "base_new.txt",
            "Document de référence contenant toutes les données principales modifiées."
        )

        process_uploaded_document(similar.id)
        similar.refresh_from_db()

        pending = PendingDocument.objects.first()
        pending_id = pending.id
        new_document_id = pending.new_document.id

        pending.status = "rejected"
        pending.save()

        pending.new_document.delete()

        self.assertFalse(Document.objects.filter(id=new_document_id).exists())
        self.assertFalse(PendingDocument.objects.filter(id=pending_id).exists())

        original.refresh_from_db()
        self.assertEqual(original.status, "saved")