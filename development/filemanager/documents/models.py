from django.db import models


class Document(models.Model):
    STATUS_CHOICES = [
        ("processing", "Traitement en cours"),
        ("saved", "Enregistré"),
        ("duplicate", "Doublon refusé"),
        ("pending_validation", "En attente de validation"),
        ("error", "Erreur"),
    ]

    file = models.FileField(upload_to="documents/")
    filename = models.CharField(max_length=255)
    file_hash = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    content = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="processing",
        db_index=True
    )

    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.filename


class PendingDocument(models.Model):
    STATUS_CHOICES = [
        ("pending", "En attente"),
        ("validated", "Validé"),
        ("rejected", "Refusé"),
    ]

    old_document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="pending_replacements"
    )

    new_document = models.OneToOneField(
        Document,
        on_delete=models.CASCADE,
        related_name="pending_document"
    )

    similarity_score = models.FloatField()
    comparison_summary = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.new_document.filename} similaire à {self.old_document.filename}"