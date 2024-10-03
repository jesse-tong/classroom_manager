from django.contrib import admin
from .models import Classroom, ClassroomTask, TaskFile, Submission, SubmissionFile, TaskComment
# Register your models here.

admin.site.register(Classroom)
admin.site.register(ClassroomTask)
admin.site.register(TaskFile)
admin.site.register(SubmissionFile)
admin.site.register(Submission)
admin.site.register(TaskComment)