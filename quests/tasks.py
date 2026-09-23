from celery import shared_task
from django.utils import timezone
from .models import Assignment

@shared_task
def expire_overdue_quests():
    overdue = Assignment.objects.filter(status="active", deadline__lt=timezone.now())
    count = overdue.update(status="failed")
    return f"Marked {count} assignment(s) as failed"