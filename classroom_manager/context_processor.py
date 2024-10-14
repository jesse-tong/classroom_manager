from .models import *
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.models import Group, User
from .models import Configuration

def classroom_processor(request):
    if request.user.is_authenticated:
        classroomsAsTeacher = Classroom.objects.filter(teachers__id__contains=request.user.id).all() 
        classroomAsStudent = Classroom.objects.filter(students__id__contains=request.user.id).all()
        user = User.objects.filter(id=request.user.id, is_staff=True).first()
        jitsiInstance = Configuration.objects.filter(key="jitsiInstance").first()
        if user:
            isAdmin = True
        else:
            isAdmin = False

        if jitsiInstance is None:
            jitsiInstance = ''
        else:
            jitsiInstance = jitsiInstance.value

        jitsiInstanceWithoutScheme = jitsiInstance.replace('https://', '').replace('http://', '')
        route = request.path
        return {'classroomsAsTeacher': classroomsAsTeacher, 'classroomsAsStudent': classroomAsStudent, 
                'route': route, 'isAdmin': isAdmin, 'jitsiInstance': jitsiInstance, 'jitsiInstanceWithoutScheme': jitsiInstanceWithoutScheme}
    return {'classroomsAsTeacher': [], 'classroomsAsStudent': []}

def configuration_processor(request):
    siteName = Configuration.objects.filter(key='siteName').first()
    siteDescription = Configuration.objects.filter(key='siteDescription').first()

    if siteName is None:
        siteName = 'EduAll'
    else:
        siteName = siteName.value
    
    if siteDescription is None:
        siteDescription = 'EduAll is a platform for managing classrooms and learning groups.'
    else:
        siteDescription = siteDescription.value
    return {'siteName': siteName, 'siteDescription': siteDescription}