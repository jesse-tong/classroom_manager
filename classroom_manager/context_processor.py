from .models import *
from django.contrib import messages
from django.db.models import Q

def classroom_processor(request):
    if request.user.is_authenticated:
        classroomsAsTeacher = Classroom.objects.filter(teachers__id__contains=request.user.id).all() 
        classroomAsStudent = Classroom.objects.filter(students__id__contains=request.user.id).all()
        route = request.path
        return {'classroomsAsTeacher': classroomsAsTeacher, 'classroomsAsStudent': classroomAsStudent, 'route': route}
    return {'classroomsAsTeacher': [], 'classroomsAsStudent': []}