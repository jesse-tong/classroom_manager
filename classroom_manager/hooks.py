from .models import *
import os

from django.db.models.signals import pre_delete
from django.dispatch import receiver

@receiver(pre_delete, sender=TaskFile)
@receiver(pre_delete, sender=SubmissionFile)
def delete_file_on_db_taskfile_delete(sender, instance, *args, **kwargs):
    try:
        os.remove(instance.filePath)
    except FileNotFoundError:
        pass