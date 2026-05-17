from celery import shared_task
from .services import process_uploaded_document


@shared_task(bind=True, max_retries=3)
def process_document_task(self, document_id):
    try:
        process_uploaded_document(document_id)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)