from .models import *
from django.contrib import messages
from django.db.models import Q

def classroom_processor(request):
    if request.user.is_authenticated:
        classroomsAsTeacher = Classroom.objects.filter(teachers__id__contains=request.user.id).all() 
        classroomAsStudent = Classroom.objects.filter(students__id__contains=request.user.id).all()
        return {'classroomsAsTeacher': classroomsAsTeacher, 'classroomsAsStudent': classroomAsStudent}
    return {'classroomsAsTeacher': [], 'classroomsAsStudent': []}