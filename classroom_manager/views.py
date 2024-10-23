from django.shortcuts import render, redirect
#models import
from .models import *

#authentication import
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import Group
from django.http import JsonResponse, HttpResponseForbidden, HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.core.serializers import serialize
from django.urls import reverse

#utils
from math import ceil
from datetime import datetime as dt
from dateutil import relativedelta
from dateutil.parser import parse as dateparse
from django.db.models import Count, Sum, F, Avg
from django.utils import timezone
from . import utils
import json

def isTeacher(userId, classroomId):
    user = User.objects.filter(id=userId).first()
    classroom = Classroom.objects.filter(id=classroomId, teachers__id__contains=userId).first()
    if user == None or classroom == None:
        return False
    return True

def isStudent(userId, classroomId):
    user = User.objects.filter(id=userId).first()
    classroom = Classroom.objects.filter(id=classroomId, students__id__contains=userId).first()
    if user == None or classroom == None:
        return False
    return True

def logoutUser(request):
    logout(request)
    return redirect('/login')

def home(request):
    return render(request, 'index.html')

def registerPage(request):
    if request.method == 'GET':
        return render(request, 'register.html')
    elif request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        reenterPassword = request.POST.get('reenterPassword')
        email = request.POST.get('email')

        if password != reenterPassword:
            messages.error(request, 'Passwords do not match!')
            return redirect(reverse('register'))

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return redirect(reverse('register'))
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists!')
            return redirect(reverse('register'))
        else:
            user = User.objects.create_user(username=username, email=email)
            user.set_password(password)
            group, created = Group.objects.get_or_create(name='student')
            user.groups.add(group)
            user.save()
            return redirect('/login')

# Create your views here.
def loginPage(request):
    if request.method == 'GET':
        return render(request, 'login.html')
    elif request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request=request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/classroom')
        else:
            messages.error(request, 'Login failed: Invalid username or password!')
            return redirect(reverse('login'))

@login_required(login_url='login')
def editProfile(request: HttpRequest):
    if request.method == 'GET':
        return render(request, 'edit_profile.html')
    elif request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        reenterPassword = request.POST.get('reenterPassword')

        if password != reenterPassword:
            messages.error(request, 'Passwords do not match!')
            return redirect(reverse('edit_profile'))
        
        user = User.objects.filter(id=request.user.id).first()
        if user == None:
            messages.error(request, 'User does not exist!')
            return redirect(reverse('edit_profile'))
        if username != None and username != '':
            user.username = username
        if email != None and email != '':
            user.email = email
        if password != None and password != '':
            user.set_password(password)

        user.save()
        messages.success(request, 'Edit profile successfully!')
        return redirect(reverse('edit_profile'))

@login_required(login_url='login')
def classroomPage(request: HttpRequest):
    if request.method == 'GET':
        currentUserId = request.user.id
        #Q object represent filter object that can have logical operators like | and &
        #Here is the query to find any classroom where the any student or any teacher in the classroom
        #has current logged in user ID
        if request.GET.get('searchClassroom'):
            classroomsUserIsStudent= Classroom.objects.filter(Q(students__id__contains=currentUserId) & Q(name__contains=request.GET.get('searchClassroom')))
            classroomsUserIsTeacher= Classroom.objects.filter(Q(teachers__id__contains=currentUserId) & Q(name__contains=request.GET.get('searchClassroom')))
        else:
            classroomsUserIsStudent= Classroom.objects \
                .filter(Q(students__id__contains=currentUserId))
            classroomsUserIsTeacher= Classroom.objects \
                .filter(Q(teachers__id__contains=currentUserId))
            
        context = {'classroomsUserIsStudent': classroomsUserIsStudent, 
                   'classroomsUserIsTeacher': classroomsUserIsTeacher, 'searchClassroom': request.GET.get('searchClassroom')}
        return render(request, 'classroom.html', context)
    elif request.method == 'POST':
        if request.POST.get('name') == None:
            messages.error(request, 'Classroom must have a name!')
            return redirect(reverse('classroom_create'))
        name = request.POST.get('name')
        description = request.POST.get('description')
        if description == None:
            description = ''

        randomImage = get_random_class_image()
        newClassroom = Classroom.objects.create(name=name, description=description, background=randomImage)
        currentUser = User.objects.get(id=request.user.id)

        newClassroom.teachers.add(currentUser)
        newClassroom.save()
        return redirect('/classroom/' + newClassroom.id)

@login_required(login_url='login')
def classroomCreatePage(request: HttpRequest):
    if request.method == 'GET':
        return render(request, 'classroom_create.html')
    elif request.method == 'POST':
        if request.POST.get('name') == None:
            messages.error(request, 'Classroom must have a name!')
            return redirect(reverse('classroom_create'))
        name = request.POST.get('name')
        description = request.POST.get('description')

        isSearchable = request.POST.get('searchable')
        if isSearchable != None:
            isSearchable = True
        else:
            isSearchable = False

        if description == None:
            description = ''
        newClassroom = Classroom.objects.create(name=name, description=description, searchable=isSearchable)
        currentUser = User.objects.get(id=request.user.id)

        newClassroom.teachers.add(currentUser)
        newClassroom.save()
        return redirect(reverse("classroom_details", args=[newClassroom.id])) 

@login_required(login_url='login')
def classroomEditPage(request: HttpRequest, id):
    classroom = Classroom.objects.filter(id=id).first()
    students = classroom.students.all()
    teachers = classroom.teachers.all()
    context={'classroom': classroom, 'classroomId': id, 
             'students': students, 'teachers': teachers}
    return render(request, 'classroom_edit.html', context)

@login_required(login_url='login')
def searchInClassroomEdit(request: HttpRequest, classroomId: int):
    if request.method == 'GET':
        query = request.GET.get('searchQuery', default='')
    else:
        query = request.POST.get('searchQuery', default='')
    searchResult = User.objects.filter(Q(username__contains=query) | Q(email__contains=query))[0:10]
    classroom = Classroom.objects.filter(id=classroomId).first()
    students = classroom.students.all()
    teachers = classroom.teachers.all()
    context={'searchResult': searchResult, 'classroom': classroom, 'classroomId': classroomId, 
             'students': students, 'teachers': teachers}
    return render(request, 'classroom_edit.html', context)


@login_required(login_url='login')
def addTeacherToClassroom(request: HttpRequest, classroomId: int, teacherId: int):
    isCurrentUserTeacher = isTeacher(request.user.id, classroomId)
    if not isCurrentUserTeacher:
        messages.error(request, "Non-teacher of this class cannot add/remove students!")
        return redirect('/classroom/edit/' + str(classroomId))
    
    teacher = User.objects.filter(id=teacherId).first()
    classroom = Classroom.objects.filter(id=classroomId).first()
    if teacher != None and classroom != None:
        classroom.students.remove(teacher)
        classroom.teachers.add(teacher)
        messages.success(request, "Add teacher successfully!")
        return redirect('/classroom/edit/' + str(classroomId))
    else:
        messages.error(request, "Teacher or classroom does not exist!")
        return redirect('/classroom/edit/' + str(classroomId))

@login_required(login_url='login')
def removeTeacherInClassroom(request: HttpRequest, classroomId: int, teacherId: int):
    if teacherId == request.user.id:
        messages.error(request, "A teacher cannot remove themselves in a class!")
        return redirect(reverse('classroom_edit', args=[classroomId]))

    isCurrentUserTeacher = isTeacher(request.user.id, classroomId)
    if not isCurrentUserTeacher:
        messages.error(request, "Non-teacher of this class cannot add/remove teachers!")
        return redirect(reverse('classroom_edit', args=[classroomId]))
    
    teacher = User.objects.filter(id=teacherId).first()
    classroom = Classroom.objects.filter(id=classroomId).first()
    if classroom.teachers.count() == 1:
        messages.error(request, "Cannot remove the last teacher in the class!")
        return redirect(reverse('classroom_edit', args=[classroomId]))
    if teacher != None and classroom != None:
        classroom.teachers.remove(teacher)
        messages.success(request, "Remove teacher successfully!")
        return redirect(reverse('classroom_edit', args=[classroomId]))
    else:
        messages.error(request, "Teacher or classroom does not exist!")
        return redirect(reverse('classroom_edit', args=[classroomId]))


@login_required(login_url='login')
def removeStudentInClassroom(request: HttpRequest, classroomId: int, studentId: int):
    isCurrentUserTeacher = isTeacher(request.user.id, classroomId)
    if not isCurrentUserTeacher:
        messages.error(request, "Non-teacher of this class cannot add/remove students!")
        return redirect(reverse('classroom_edit', args=[classroomId]))

    student = User.objects.filter(id=studentId).first()
    classroom = Classroom.objects.filter(id=classroomId).first()
    if student != None and classroom != None:
        classroom.students.remove(student)
        messages.success(request, "Remove student successfully!")
        return redirect(reverse('classroom_edit', args=[classroomId]))
    else:
        messages.error(request, "Student or classroom does not exist!")
        return redirect(reverse('classroom_edit', args=[classroomId]))
        

@login_required(login_url='login')
def addStudentToClassroom(request:HttpRequest, classroomId: int, studentId: int):
    isCurrentUserTeacher = isTeacher(request.user.id, classroomId)
    if not isCurrentUserTeacher:
        messages.error(request, "Non-teacher of this class cannot add/remove students!")
        return redirect(reverse('classroom_edit', args=[classroomId]))

    student = User.objects.filter(id=studentId).first()
    classroom = Classroom.objects.filter(id=classroomId).first()
    if student != None and classroom != None:
        classroom.teachers.remove(student)
        classroom.students.add(student)
        messages.success(request, "Add student successfully!")
        return redirect(reverse('classroom_edit', args=[classroomId]))
    else:
        messages.error(request, "Student or classroom does not exist!")
        return redirect(reverse('classroom_edit', args=[classroomId]))

#Search user by email or username (case sentitive)
@csrf_exempt
def searchUserByEmailOrUsername(request: HttpRequest):
    if request.method == 'GET':
        query = request.GET.get('q', default='')
        searchResult = list(User.objects.filter(Q(username__contains=query) | Q(email__contains=query))[0:10].values())
        return JsonResponse(status=200, data=searchResult)
    else:
        return JsonResponse(status=400, data={'status': 'Invalid HTTP method'})

@login_required(login_url='login')
def classroomUsers(request: HttpRequest, classroomId):
    if request.method == 'GET':
        classroom = Classroom.objects.filter(id=classroomId).first()
    if classroom != None:
        groups = LearnGroup.objects.filter(classroom=classroom).all()
        groupsJoined = LearnGroup.objects.filter(students__id__contains=request.user.id).all()

        try:
            page = int(request.GET.get('page', 1))
        except:
            page = 1
        
        if page <= 0:
            page = 1

        limit = 10
        studentCount = classroom.students.count()
        pageLimit = ceil(studentCount / limit)

        if page > pageLimit:
            page = pageLimit
        
        startPagination = max(1, page - 2)
        endPagination = min(pageLimit, page + 2)
        
        pageRange = list(range(startPagination, endPagination + 1))

        students = classroom.students.order_by("id").all()[(page - 1)*limit : page*limit]
        teachers = classroom.teachers.order_by("id").all()
        isCurrentUserTeacher = isTeacher(request.user.id, classroom.id)
        context = {'classroom': classroom, 'students': students, 'teachers': teachers, 'classroomId': id, 
                     'isTeacher': isCurrentUserTeacher, 'joinPath': request.get_host() + reverse('join_classroom_by_id', args=[classroomId]),
                      'pageRange': pageRange, 'currentPage': page, 'groups': groups, 'joinedGroups': groupsJoined, 'currentClassroom': classroom }
        
        return render(request, 'classroom_details_users.html', context)
    else:
        return render(request, '404page.html')

@login_required(login_url='login')
def classroomDetailPage(request: HttpRequest, id):
    if request.method == 'GET':
        classroom = Classroom.objects.filter(id=id).first()
        if classroom != None:
            tasks = ClassroomTask.objects.filter(classroom=classroom, isAssignment=False).order_by('-deadline').all()
            assignments = ClassroomTask.objects.filter(classroom=classroom, isAssignment=True).order_by('-deadline').all()
            isCurrentUserTeacher = isTeacher(request.user.id, classroom.id)
            context = {'classroom': classroom, 'classroomId': id, 'assignments': assignments,
                       'tasks': tasks, 'isTeacher': isCurrentUserTeacher, 'joinPath': request.get_host() + reverse('join_classroom_by_id', args=[id]),
                         'currentClassroom': classroom }
            return render(request, 'classroom_details.html', context)
        else:
            return render(request, '404page.html')
    elif request.method == 'POST':
        method = request.POST.get('_method', '').lower()
        if method == 'put':
            if request.POST.get('name') == None:
                messages.error(request, 'Classroom must have a name!')
                return redirect('/classroom/create')
            name = request.POST.get('name')
            description = request.POST.get('description')
            isSearchable = request.POST.get('searchable')
            if isSearchable != None:
                isSearchable = True
            else:
                isSearchable = False

            if description == None:
                description = ''
            classroom = Classroom.objects.filter(id=id).first()
            if not classroom:
                messages.error(request, 'Classroom with ID ' + id + ' does not exists!')
                return redirect('/classroom')
            
            classroom.name = name; classroom.description = description; classroom.searchable = isSearchable
            classroom.save()
            messages.success(request, 'Edit classroom successfully')
            return redirect('/classroom')

        elif method == 'delete':
            classroom = Classroom.objects.filter(id=id).first()
            if classroom == None:
                messages.error(request, 'Classroom with ID ' + id + ' does not exists!')
                return redirect('/classroom')
            
            studentCount = classroom.students.count()
            isCurrentUserTeacher = isTeacher(request.user.id, id)
            if not isCurrentUserTeacher:
                messages.error(request, 'You are not a teacher, cannot delete the classroom!')
                return redirect('/classroom')
            if studentCount > 0:
                messages.error(request, 'There are still students left, cannot delete the classroom!')
                return redirect('/classroom')
            deleted_row, _ = Classroom.objects.filter(id=id).delete()
            if deleted_row > 0:
                messages.info(request, 'Delete classroom successfully!')
                return redirect('/classroom')

@login_required(login_url='login')
def classroomAssignmentPage(request: HttpRequest, id):
    classroom = Classroom.objects.filter(id=id).first()
    if classroom != None:
        tasks = ClassroomTask.objects.filter(classroom=classroom, isAssignment=False).order_by('-deadline').all()
        assignments = ClassroomTask.objects.filter(classroom=classroom, isAssignment=True).order_by('-deadline').all()
        isCurrentUserTeacher = isTeacher(request.user.id, classroom.id)
        context = {'classroom': classroom, 'classroomId': id, 'assignments': assignments,
                    'tasks': tasks, 'isTeacher': isCurrentUserTeacher, 'joinPath': request.get_host() + reverse('join_classroom_by_id', args=[id])
                     ,'currentClassroom': classroom }
        return render(request, 'classroom_details.html', context)
    else:
        return render(request, '404page.html')

@login_required(login_url='login')
def getEditDeleteTaskById(request: HttpRequest, taskId: int):
    if request.method == 'GET':
        task = ClassroomTask.objects.filter(id=taskId).first()
        taskFiles = TaskFile.objects.filter(task=task).all()
        userSubmission = Submission.objects.filter(student=request.user, task=task).first()
        if task == None:
            return render(request, '404page.html')
        isUserTeacher = isTeacher(request.user.id, task.classroom.id)
        userSubmissionFiles = SubmissionFile.objects.filter(submission=userSubmission).all()

        comments = TaskComment.objects.filter(task=task).all()
        try:
            editingCommentId = request.GET.get('editingCommentId')
            editingCommentId = int(editingCommentId)
        except:
            editingCommentId = None

        if task.deadline != None:
            now = datetime.now(task.deadline.tzinfo)
            task_due = task.deadline
            isBeforeDue = now < task_due
        else:
            isBeforeDue = False

        context = {'task': task, 'taskFiles': taskFiles, 'isTeacher': isUserTeacher, 'userSubmission': userSubmission, 
                   'submissionFiles': userSubmissionFiles, 'isBeforeDue': isBeforeDue, 'comments': comments, 
                   'currentUser': request.user, 'editingCommentId': editingCommentId}
        return render(request, 'task_details.html', context)
    if request.method == 'POST':
        if request.POST.get('_method') == 'put':
            task = ClassroomTask.objects.filter(id=taskId).first()
            if task == None:
                return render(request, '404page.html')
            title = request.POST.get('title')
            isAssignment = request.POST.get('isAssignment')
            description = request.POST.get('description')
            deadline = request.POST.get('deadline')
            acceptLateSubmission = request.POST.get('acceptLateSubmission')
            weight = request.POST.get('weight')

            if isAssignment == None:
                isAssignment = False
            else:
                isAssignment = True

            if acceptLateSubmission == None:
                acceptLateSubmission = False
            else:
                acceptLateSubmission = True

            files = request.FILES.getlist('file')
            TaskFile.objects.filter(task=task).delete()
            taskfiles = []
            for file in files:
                taskfiles.append(TaskFile(file=file, task=task))
            TaskFile.objects.bulk_create(taskfiles)
            task.title = title
            task.isAssignment = isAssignment
            task.description = description
            task.deadline = dateparse(deadline)
            if task.isAssignment == True:
                task.weight = weight
            else:
                task.weight = 0.0
            task.save()
            taskFiles = TaskFile.objects.filter(task=task).all()
            context = {'task': task, taskFiles: taskFiles}
            messages.success(request, 'Edit task/assignment successfully!')
            return redirect(reverse('task_details', args=[taskId]))
        elif request.POST.get('_method') == 'delete':
            task = ClassroomTask.objects.filter(id=taskId).first()
            if task == None:
                return render(request, '404page.html')
            task.delete()
            messages.success(request, 'Delete classroom task successfully!')
            return redirect('/classroom')
        

@login_required(login_url='login')
def createTaskPage(request: HttpRequest, classroomId: int):
    if request.method == 'GET':
        classroom = Classroom.objects.filter(id=classroomId).first()
        if classroom == None:
            return render(request, '404page.html')
        
        isUserTeacher = isTeacher(request.user.id, classroomId)
        context = {'classroom': classroom, 'isTeacher': isUserTeacher}
        return render(request, 'task_create.html', context)
    if request.method == 'POST':
        classroom = Classroom.objects.filter(id=classroomId).first()
        if not classroom:
            return render(request, '404page.html')
        if not isTeacher(request.user.id, classroomId):
            messages.error(request, 'You are not a teacher of this class!')
            return redirect(reverse('classroom_details', args=[classroomId]))
        isAssignment = request.POST.get('isAssignment')
        description = request.POST.get('description')
        
        title = request.POST.get('title')
        deadline = request.POST.get('deadline')
        weight = request.POST.get('weight')
            
        if isAssignment == None:
            isAssignment = False
        else:
            isAssignment = True

        if classroom == None:
            return render(request, '404page.html')
        newTask = ClassroomTask.objects.create(isAssignment = isAssignment, classroom=classroom, title=title, description=description)
        files = request.FILES.getlist('file')

        taskfiles = []
        for file in files:
            taskfiles.append(TaskFile(file=file, task=newTask))
        TaskFile.objects.bulk_create(taskfiles)
        
        try:
            deadline = dateparse(deadline) if deadline != None and deadline != '' else None
        except:
            messages.error(request, 'Task must have a valid deadline!')
            return redirect(reverse('classroom_details', args=[classroomId]))
        
        newTask.isAssignment = isAssignment
        newTask.description = description
        if isAssignment == True:
            newTask.weight = weight
        else:
            newTask.weight = 0.0

        if deadline != None:
            newTask.deadline = deadline

        newTask.save()

        return redirect('/classroom/task/' + str(newTask.id))

@login_required(login_url='login')
def submitToTask(request: HttpRequest, taskId: int):
    if request.method == 'GET':
        task = ClassroomTask.objects.filter(id=taskId).first()
        if task == None:
            return render(request, '404page.html')
        taskFiles = TaskFile.objects.filter(task=task).all()
        userSubmission = Submission.objects.filter(student=request.user, task=task).first()
        submissionFiles = SubmissionFile.objects.filter(submission=userSubmission).all()

        context = {'task': task, 'taskFiles': taskFiles, 'userSubmission': userSubmission, 'submissionFiles': submissionFiles}
        return render(request, 'task_submit.html', context)
    if request.method == 'POST':
        if request.POST.get('_method') == None or request.POST.get('_method') == 'post':
            task = ClassroomTask.objects.filter(id=taskId).first()
            if task == None:
                return render(request, '404page.html')
            files = request.FILES.getlist('file')

            submissionFiles = []
            currentUser = User.objects.filter(id=request.user.id).first()
            if task.acceptLateSubmission == False and task.deadline < dt.now():
                messages.error(request, 'Cannot submit after deadline!')
                return redirect(reverse('task_details', args=[taskId]))
            submission = Submission.objects.filter(student=currentUser, task=task).first()
            if submission == None:
                submission = Submission.objects.create(student=currentUser, task=task, lastSubmission=dt.now())
            oldSubmissionFiles = SubmissionFile.objects.filter(submission=submission).all()
            deleteCount, objDeleteCount = oldSubmissionFiles.delete()
            for file in files:
                submissionFiles.append(SubmissionFile(file=file, submission=submission))
            SubmissionFile.objects.bulk_create(submissionFiles)
        if request.POST.get('_method') == 'delete':
            task = ClassroomTask.objects.filter(id=taskId).first()
            if task == None:
               return render(request, '404page.html')
            submission = Submission.objects.filter(student=request.user, task=task).first()
            if submission != None:
                submission.delete()
        
        return redirect(reverse('task_details', args=[taskId]))
    
@login_required(login_url='login')
def joinByClassroomId(request: HttpRequest, classroomId: int):
    classroom = Classroom.objects.filter(id=classroomId).first()
    if classroom == None:
        return render(request, '404page.html')
    user = User.objects.filter(id=request.user.id).first()
    classroom.students.add(user)
    return redirect(reverse('classroom_details', args=[classroomId]))

@login_required(login_url='login')
def getSubmissionsByTaskId(request: HttpRequest, taskId: int):
    if request.method == 'GET':
        task = ClassroomTask.objects.filter(id=taskId).first()
        if task == None:
            return render(request, '404page.html')
        if not isTeacher(request.user.id, task.classroom.id):
            return render(request, '403page.html')
        submissions = Submission.objects.filter(task=task).all()
        taskFiles = TaskFile.objects.filter(task=task).all()
        context = {'submissions': submissions, 'task': task, 'taskFiles': taskFiles}
        return render(request, 'submissions.html', context)
    else:
        return render(request, '404page.html')


@login_required(login_url='login')
def submissionDetailsPage(request: HttpRequest, submissionId: int):
    if request.method == 'GET':
        submission = Submission.objects.filter(id=submissionId).first()
        if submission == None:
            return render(request, '404page.html')
        submissionFiles = SubmissionFile.objects.filter(submission=submission).all()
        isUserTeacher = isTeacher(request.user.id, submission.task.classroom.id)
        context = {'submission': submission, 'submissionFiles': submissionFiles, 'isTeacher': isUserTeacher}
        return render(request, 'submission_details.html', context)
    elif request.method == 'POST':
        #Grading submission
        submission = Submission.objects.filter(id=submissionId).first()
        if submission == None:
            return render(request, '404page.html')
        gpa = request.POST.get('gpa')
        try:
            gpa = float(gpa)
        except:
            messages.error(request, 'GPA must be a number!')
            return redirect(reverse('submission_details', args=[submissionId]))
        if gpa < 0:
            messages.error(request, 'GPA must be greater than 0!')
            return redirect(reverse('submission_details', args=[submissionId]))
        submission.gpa = gpa
        submission.save()
        return redirect(reverse('submission_details', args=[submissionId]))
    
@login_required(login_url='login')
def allTaskSchedules(request: HttpRequest):
    if request.method == 'GET':
        now = timezone.now()
        lateTaskScope = now - relativedelta.relativedelta(months=3)

        dateStart = None; dateEnd = None
        if request.GET.get('dateStart'):
            try:
                dateStart = dateparse(request.GET.get('dateStart'))
            except:
                pass
        
        if request.GET.get('dateEnd'):
            try:
                dateEnd = dateparse(request.GET.get('dateEnd'))
            except:
                pass

        
        if dateStart != None and dateEnd == None:
            filterResult = ClassroomTask.objects.filter(Q(classroom__students__id__contains=request.user.id) & Q(deadline__gte=dateStart)).all()
        elif dateEnd != None and dateStart == None:
            filterResult = ClassroomTask.objects.filter(Q(classroom__students__id__contains=request.user.id) & Q(deadline__lte=dateEnd)).all()
        elif dateEnd != None and dateStart != None:
            filterResult = ClassroomTask.objects.filter(Q(classroom__students__id__contains=request.user.id) & Q(deadline__lte=dateEnd) & Q(deadline__gte=dateStart)).all()
        else:
            filterResult = []
        
        upcomingTasks = ClassroomTask.objects.filter((Q(classroom__students__id__contains=request.user.id) )& Q(deadline__gte=now) ).all()
        
        lateTasks = ClassroomTask.objects.filter((Q(classroom__students__id__contains=request.user.id) )& Q(deadline__gte=lateTaskScope)
                                                      & Q(deadline__lte=now)).all()
        
        #Add grades to assignment task
        #If there's a submission from current user, assign the grade to the task of user; else None
        for i in range(len(lateTasks)):
            lateTasks[i].gpa = None
            if lateTasks[i].isAssignment and Submission.objects.filter(task=lateTasks[i], student__id=request.user.id).exists():
                submission = Submission.objects.filter(task=lateTasks[i], student__id=request.user.id).first()
                if submission:
                    lateTasks[i].gpa = submission.gpa

        for i in range(len(upcomingTasks)):
            upcomingTasks[i].gpa = None
            if upcomingTasks[i].isAssignment and Submission.objects.filter(task=upcomingTasks[i], student__id=request.user.id).exists():
                submission = Submission.objects.filter(task=upcomingTasks[i], student__id=request.user.id).first()
                if submission:
                    upcomingTasks[i].gpa = submission.gpa

        for i in range(len(filterResult)):
            filterResult[i].gpa = None
            if filterResult[i].isAssignment and Submission.objects.filter(task=filterResult[i], student__id=request.user.id).exists():
                submission = Submission.objects.filter(task=filterResult[i], student__id=request.user.id).first()
                if submission:
                    filterResult[i].gpa = submission.gpa
        
        #Variables for calendar
        taskDates = [task.deadline for task in upcomingTasks] + [task.deadline for task in lateTasks]
        taskDates = list(set(taskDates))

        lastMonth = False; nextMonth = False

        if request.GET.get('lastMonth') != None:
            now = now - relativedelta.relativedelta(months=1)
            lastMonth = True
        elif request.GET.get('nextMonth') != None:
            now = now + relativedelta.relativedelta(months=1)
            nextMonth = True

        daysWithDeadlines = []
        for taskDate in taskDates:
            if taskDate.month == now.month and taskDate.year == now.year:
                daysWithDeadlines.append(taskDate.day)

        firstDay = now.replace(day=1)
        firstDayWeekday = firstDay.weekday()
        numberDaysOfMonth = (firstDay + relativedelta.relativedelta(months=1) - relativedelta.relativedelta(days=1)).day
        
        if request.GET.get('lastMonth') == None and request.GET.get('nextMonth') == None:
            currentDay = now.day
        else:
            currentDay = None

        daysArray = list(range(1, numberDaysOfMonth + 1))
        daysArray = [''] * firstDayWeekday + daysArray

        monthString = now.strftime("%B")
        yearString = str(now.year)

        # End variables for calendar

        groupsJoined = LearnGroup.objects.filter(students__id__contains=request.user.id).all()

        context = {'upcomingTasks': upcomingTasks, 'lateTasks': lateTasks, 
                   'daysArray': daysArray, 'currentDay': currentDay, 'monthString': monthString, 
                   'yearString': yearString, 'daysWithDeadlines': daysWithDeadlines, 'lastMonth': lastMonth, 
                   'nextMonth': nextMonth, 'joinedGroups': groupsJoined, 'filterResult': filterResult, 'dateStart': request.GET.get('dateStart'),'dateEnd': request.GET.get('dateEnd') }    
        return render(request, 'all_task_schedules.html', context)
    else:
        return render(request, '404page.html')
    
@login_required(login_url='login')
def getTaskDeadlines(request: HttpRequest):
    if request.method == 'GET':
        tasks = ClassroomTask.objects.filter(classroom__students__id__contains=request.user.id).all().values()
        tasks_json = serialize('json', tasks)
        return HttpResponse(tasks_json, content_type='application/json')
    else:
        return render(request, '404page.html')
    
@login_required(login_url='login')
def addCommentToTask(request: HttpRequest, taskId: int):
    if request.method == 'POST':
        task = ClassroomTask.objects.filter(id=taskId).first()
        if task == None:
            return render(request, '404page.html')
        comment = request.POST.get('comment')
        if comment == None:
            messages.error(request, 'Comment cannot be empty!')
            return redirect(reverse('task_details', args=[taskId]))
        newComment = TaskComment.objects.create(commenter=request.user, comment=comment, task=task)
        newComment.save()
        return redirect(reverse('task_details', args=[taskId]))
    else:
        return render(request, '404page.html')
    
@login_required(login_url='login')
def editDeleteComment(request: HttpRequest, commentId: int):
    if request.method == 'POST':
        if request.POST.get('_method') == 'delete':
            comment = TaskComment.objects.filter(id=commentId).first()
            if comment == None:
                return render(request, '404page.html')
            task_id = comment.task.id
            deleted_count, delete_details = TaskComment.objects.filter(id=commentId).delete()
            print(deleted_count)
            if deleted_count > 0:
                messages.success(request, 'Delete comment successfully!')
            
            return redirect(reverse('task_details', args=[comment.task.id]))
        elif request.POST.get('_method') == 'put':
            comment = TaskComment.objects.filter(id=commentId).first()
            if comment == None:
                return render(request, '404page.html')
            newComment = request.POST.get('comment')
            if newComment == None:
                messages.error(request, 'Comment cannot be empty!')
                return redirect(reverse('task_details', args=[comment.task.id]))
            comment.comment = newComment
            comment.save()
            return redirect(reverse('task_details', args=[comment.task.id]))
    else:
        return render(request, '404page.html')
    
@login_required(login_url='login')
def classroomAnalytics(request: HttpRequest, classroomId: int):
    if request.method == 'GET':
        classroom = Classroom.objects.filter(id=classroomId).first()
        if classroom == None:
            return render(request, '404page.html')
        isUserTeacher = isTeacher(request.user.id, classroomId)
        if not isUserTeacher:
            return render(request, '403page.html')
        taskCount = ClassroomTask.objects.filter(classroom=classroom, isAssignment=True).count()
        studentCount = classroom.students.count()
        
        countByGpaGroup = Submission.objects.filter(task__classroom=classroom, task__isAssignment=True).values('gpa').annotate(count=Count('gpa')).order_by('gpa')

        submissionCount = Submission.objects.filter(task__classroom=classroom, task__isAssignment=True).count()
        assignmentCompletion = submissionCount / (taskCount * studentCount) * 100 if taskCount > 0 else 0
        assignmentCompletion = round(assignmentCompletion, 2)

        averageGrade = Submission.objects.filter(task__classroom=classroom, task__isAssignment=True).aggregate(average=Avg('gpa'))['average']
        
        if averageGrade == None:
            averageGrade = 0
        else:
            averageGrade = round(averageGrade, 2)
        

        context = {'classroom': classroom, 'assignmentCount': taskCount, 'studentCount': studentCount,
                    'submissionCount': submissionCount, 'averageGrade': averageGrade, 
                    'assignmentCompletion': assignmentCompletion, 'countByGpaGroup': countByGpaGroup}
        return render(request, 'classroom_analytics.html', context)
    else:
        return render(request, '404page.html')
    
@login_required(login_url='login')
@csrf_exempt
def classroomSubmissionCountByGpa(request: HttpRequest, classroomId: int):
    if request.method == 'GET':
        classroom = Classroom.objects.filter(id=classroomId).first()
        if classroom == None:
            return JsonResponse(status=404, data={'status': 'Not Found'})
        isUserTeacher = isTeacher(request.user.id, classroomId)
        if not isUserTeacher:
            return JsonResponse(status=403, data={'status': 'Forbidden'})
        
        countByGpaGroup = Submission.objects.filter(task__classroom=classroom, task__isAssignment=True).values('gpa').annotate(count=Count('gpa')).order_by('gpa')
        return JsonResponse(status=200, data=list(countByGpaGroup.values('gpa', 'count')), safe=False)
    
@login_required(login_url='login')
def createLearnGroup(request: HttpRequest, classroomId: int):
    if request.method == 'GET':
        return render(request, 'learn_group_create.html')
    elif request.method == 'POST':
        classroom = Classroom.objects.filter(id=classroomId).first()
        if not classroom:
            return render(request, '404page.html')
        
        name = request.POST.get('name')
        newLearnGroup = LearnGroup.objects.create(name=name, classroom=classroom)
        if not isTeacher(request.user.id, classroomId):
            #If user is not a teacher, then add the user to the learning group
            newLearnGroup.students.add(request.user)

        newLearnGroup.save()
        return redirect(reverse('learn_group_details', args=[newLearnGroup.id]))
    
@login_required(login_url='login')
def editDeleteLearnGroup(request: HttpRequest, groupId: int):
    if request.method == 'POST':
        if request.POST.get('_method') == 'put':
            learnGroup = LearnGroup.objects.filter(id=groupId).first()
            if learnGroup == None:
                return render(request, '404page.html')
            if not isTeacher(request.user.id, learnGroup.classroom.id) and not learnGroup.students.filter(id=request.user.id).exists():
                return render(request, '403page.html')
            
            name = request.POST.get('name')
            learnGroup.name = name
            
            learnGroup.save()
            messages.success(request, 'Edit learn group successfully!')
            return redirect(reverse('learn_group_details', args=[groupId]))
        elif request.POST.get('_method') == 'delete':
            learnGroup = LearnGroup.objects.filter(id=groupId).first()
            if learnGroup == None:
                return render(request, '404page.html')
            
            classroomId = learnGroup.classroom.id
            if not isTeacher(request.user.id, learnGroup.classroom.id):
                return render(request, '403page.html')
            
            learnGroup.delete()
            messages.success(request, 'Delete learning group successfully!')
            return redirect(reverse('classroom_details', args=[classroomId]))
    else:
        return render(request, '404page.html')
    
@login_required(login_url='login')
def learnGroupDetails(request: HttpRequest, groupId: int):
    if request.method == 'GET':
        learnGroup = LearnGroup.objects.filter(id=groupId).first()
        if learnGroup == None:
            return render(request, '404page.html')
        
        isUserTeacher = isTeacher(request.user.id, learnGroup.classroom.id)
        if not isUserTeacher and not learnGroup.students.filter(id=request.user.id).exists():
            return render(request, '403page.html')
        
        members = learnGroup.students.all()

        page = request.GET.get('page', 1)
        try:
            page = int(page)
            if page <= 0:
                page = 1
        except:
            page = 1
        
        try:
            editingCommentId = request.GET.get('editingCommentId')
            editingCommentId = int(editingCommentId)
        except:
            editingCommentId = None

        comments = GroupComment.objects.filter(learnGroup=learnGroup).order_by('-creationDate').all()[(page - 1) * 10 : page * 10]

        numberOfComments = GroupComment.objects.filter(learnGroup=learnGroup).count()
        pageLimit = ceil(numberOfComments / 10)
        pageRange = list(range(max(1, page - 2), min(pageLimit + 1, page + 3) ))
        context = {'learnGroup': learnGroup, 'isTeacher': isUserTeacher, 'members': members, 'group': learnGroup,
                    'comments': comments, 'editingCommentId': editingCommentId, 'pageRange': pageRange, 'currentPage': page}
        return render(request, 'learn_group_details.html', context)
    else:
        return render(request, '404page.html')

@login_required(login_url='login')
def addMemberToLearnGroup(request: HttpRequest, groupId: int, memberId: int):
    if request.method == 'GET':
        learnGroupId = groupId
        learnGroup = LearnGroup.objects.filter(id=learnGroupId).first()
        if learnGroup == None:
            return render(request, '404page.html')
        if not isTeacher(request.user.id, learnGroup.classroom.id):
            return render(request, '403page.html')
        
        return redirect(reverse('search_in_group_edit', args=[learnGroupId]))
    elif request.method == 'POST':
        learnGroupId = groupId
        learnGroup = LearnGroup.objects.filter(id=learnGroupId).first()
        if learnGroup == None:
            return render(request, '404page.html')
        if not isTeacher(request.user.id, learnGroup.classroom.id)  and not learnGroup.students.filter(id=request.user.id).exists():
            return render(request, '403page.html')
        
        user = User.objects.filter(id=memberId).first()
        if user == None:
            messages.error(request, 'User does not exist!')
            return redirect(reverse('search_in_group_edit', args=[learnGroupId]))
        learnGroup.students.add(user)
        return redirect(reverse('search_in_group_edit', args=[learnGroupId]))
    else:
        return render(request, '404page.html')
    
@login_required(login_url='login')
def deleteMemberFromLearnGroup(request: HttpRequest, groupId: int, memberId: int):
    if request.method == 'POST':
        learnGroup = LearnGroup.objects.filter(id=groupId).first()
        if learnGroup == None:
            return render(request, '404page.html')
        '''if not isTeacher(request.user.id, learnGroup.classroom.id):
            return render(request, '403page.html')'''
        
        user = User.objects.filter(id=memberId).first()
        if user == None:
            messages.error(request, 'User does not exist!')
            return redirect(reverse('search_in_group_edit', args=[groupId]))
        learnGroup.students.remove(user)

        #Delete group if no student left
        if learnGroup.students.count() == 0:
            learnGroup.delete()
            messages.success(request, 'Remove last student and delete learn group successfully!')
            return redirect(reverse('classroom_details', args=[learnGroup.classroom.id]))

        messages.success(request, 'Remove student successfully!')
        return redirect(reverse('search_in_group_edit', args=[groupId]))
    else:
        return render(request, '404page.html')

@login_required(login_url='login')
def addCommentToLearnGroup(request: HttpRequest, groupId: int):
    if request.method == 'POST':
        learnGroup = LearnGroup.objects.filter(id=groupId).first()
        if learnGroup == None:
            return render(request, '404page.html')
        comment = request.POST.get('comment')
        if comment == None:
            messages.error(request, 'Comment cannot be empty!')
            return redirect(reverse('learn_group_details', args=[groupId]))
        file = request.FILES.get('file')
        newComment = GroupComment.objects.create(commenter=request.user, comment=comment, learnGroup=learnGroup, file=file)
        newComment.save()

        messages.success(request, 'Add comment successfully!')
        return redirect(reverse('learn_group_details', args=[groupId]))
    else:
        return render(request, '404page.html')
    
@login_required
def editDeleteCommentLearnGroup(request: HttpRequest, commentId: int):
    if request.method == 'POST':
        if request.POST.get('_method') == 'delete':
            comment = GroupComment.objects.filter(id=commentId).first()
            if comment == None:
                return render(request, '404page.html')
            if not isTeacher(request.user.id, comment.learnGroup.classroom.id) and comment.commenter.id != request.user.id:
                return render(request, '403page.html')
            
            comment.delete()
            messages.success(request, 'Delete comment successfully!')
            return redirect(reverse('learn_group_details', args=[comment.learnGroup.id]))
        elif request.POST.get('_method') == 'put':
            comment = GroupComment.objects.filter(id=commentId).first()
            if comment == None:
                return render(request, '404page.html')
            '''if not isTeacher(request.user.id, comment.learnGroup.classroom.id):
                return render(request, '403page.html')'''
            
            newComment = request.POST.get('comment')
            if newComment == None:
                messages.error(request, 'Comment cannot be empty!')
                return redirect(reverse('learn_group_details', args=[comment.learnGroup.id]))
            
            file = request.FILES.get('file')

            comment.comment = newComment
            comment.file = file
            comment.save()
            messages.success(request, 'Edit comment successfully!')
            return redirect(reverse('learn_group_details', args=[comment.learnGroup.id]))
    else:
        return render(request, '404page.html')
    
@login_required(login_url='login')
def searchInGroupEdit(request: HttpRequest, groupId: int):
    if request.method == 'GET':
        query = request.GET.get('searchQuery', default='')
    else:
        query = request.POST.get('searchQuery', default='')

    if query == None or query == '':
        searchResult = []
    else:
        searchResult = User.objects.filter(Q(username__contains=query) | Q(email__contains=query))[0:10]
    group = LearnGroup.objects.filter(id=groupId).first()
    members = group.students.all()
    context={'searchResult': searchResult, 'group': group, 'groupId': groupId, 
             'members': members}
    return render(request, 'group_edit.html', context)

def getAssignmentNames(classroomId: int):
    tasks = ClassroomTask.objects.filter(isAssignment=True, classroom__id=classroomId).order_by('id').all()
    taskNames = [task.title for task in tasks]
    return taskNames

def getStudentGpa(studentId: int):
    tasks = ClassroomTask.objects.filter(isAssignment=True, classroom__students__id__contains=studentId).order_by('id').all()
    total_gpa = 0
    gpas = []
    student = User.objects.filter(id=studentId).first()
    for task in tasks:
        submission = Submission.objects.filter(student__id=studentId, task=task).first()
        if submission != None:
            if task.weight == None:
                task.weight = 0.0
            total_gpa += submission.gpa * task.weight / 100.0
            gpas.append(submission.gpa)
        else:
            gpas.append(0.0)
    
    return {'totalGpa': total_gpa, 'gpas': gpas, 'student': student}

def getGpaOfAllStudents(request: HttpRequest, classroomId: int):
    assignmentNames = getAssignmentNames(classroomId)
    classroom = Classroom.objects.filter(id=classroomId).first()
    students = classroom.students.order_by('id').all()

    isCurrentUserTeacher = isTeacher(request.user.id, classroomId)

    studentGpas = []
    for student in students:
        studentGpas.append(getStudentGpa(student.id))

    context = {'studentGpas': studentGpas, 'taskNames': assignmentNames, 'classroom': classroom, 'isTeacher': isCurrentUserTeacher}
    return render(request, 'gpa_details.html', context)
    
def registerAdmin(request: HttpRequest):
    if request.method == 'GET':
        return render(request, 'register_admin.html')
    elif request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirmPassword = request.POST.get('confirmPassword')
        if password != confirmPassword:
            messages.error(request, 'Password and confirm password do not match!')
            return redirect(reverse('register_admin'))
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return redirect(reverse('register_admin'))
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists!')
            return redirect(reverse('register_admin'))
        
        user = User.objects.create_user(username=username, email=email, password=password, is_staff=True)
        admin_group = Group.objects.filter(name='admin').get_or_create(name='admin')
        user.groups.add(admin_group)
        user.save()
        messages.success(request, 'Register admin successfully!')
        return redirect(reverse('login'))
    
def isUserAdmin(userId: int):
    return User.objects.filter(id=userId, is_staff=True).exists()

@login_required(login_url='login')
def siteSettings(request: HttpRequest):
    if not isUserAdmin(request.user.id):
        return render(request, '403page.html')
    if request.method == 'GET':
        jitsiInstance = Configuration.objects.filter(key='jitsiInstance').first()
        siteName = Configuration.objects.filter(key='siteName').first()
        siteDescription = Configuration.objects.filter(key='siteDescription').first()
        context = {'jitsiInstance': jitsiInstance.value, 'siteName': siteName.value, 'siteDescription': siteDescription.value }
        return render(request, 'site_settings.html', context)
    
    elif request.method == 'POST':
        jitsiInstance = request.POST.get('jitsiInstance')
        jitsiInstanceSelect = request.POST.get('jitsiInstanceSelect')
        siteName = request.POST.get('siteName')
        siteDescription = request.POST.get('siteDescription')

        if jitsiInstance == None and jitsiInstanceSelect == None:
            messages.error(request, 'Jitsi instance cannot be empty!')
            return redirect(reverse('site_settings'))
        
        if siteName == None:
            messages.error(request, 'Site name cannot be empty!')
            return redirect(reverse('site_settings'))

        if siteDescription == None:
            messages.error(request, 'Site description cannot be empty!')
            return redirect(reverse('site_settings'))

        jitsiInstanceConfig = Configuration.objects.filter(key='jitsiInstance').first()
        siteNameConfig = Configuration.objects.filter(key='siteName').first()
        siteDescriptionConfig = Configuration.objects.filter(key='siteDescription').first()

        if jitsiInstanceConfig == None:
            Configuration.objects.create(key='jitsiInstance', value=jitsiInstance)
        else:
            if jitsiInstanceSelect != None and jitsiInstanceSelect != '':
                jitsiInstanceConfig.value = jitsiInstanceSelect
            elif jitsiInstance != None and jitsiInstance != '':
                jitsiInstanceConfig.value = jitsiInstance
            jitsiInstanceConfig.save()
        
        if siteNameConfig == None:
            Configuration.objects.create(key='siteName', value=siteName)
        else:
            siteNameConfig.value = siteName
            siteNameConfig.save()
        
        if siteDescriptionConfig == None:
            Configuration.objects.create(key='siteDescription', value=siteDescription)
        else:
            siteDescriptionConfig.value = siteDescription
            siteDescriptionConfig.save()

        messages.success(request, 'Update site settings successfully!')
        return redirect(reverse('site_settings'))

@login_required(login_url='login')
def classroomJitsi(request: HttpRequest, classroomId: int):
    classroom = Classroom.objects.filter(id=classroomId).first()
    classroomName = classroom.name
    jitsiRoom = str(classroomId) + '-' + classroomName
    isCurrentUserTeacher = isTeacher(request.user.id, classroomId)
    if classroom == None:
        return render(request, '404page.html')

    context = {'classroom': classroom, 'jitsiRoom': jitsiRoom, 'isTeacher': isCurrentUserTeacher}
    return render(request, 'classroom_jitsi.html', context)

@login_required(login_url='login')
def cloneClassroom(request: HttpRequest, classroomId: int):
    if request.method == 'GET':
        classroom = Classroom.objects.filter(id=classroomId).first()
        if classroom == None:
            return render(request, '404page.html')
        if not isTeacher(request.user.id, classroomId):
            return render(request, '403page.html')
        
        if request.GET.get('name') == None:
            name = classroom.name + ' (Copy)'
        else:
            name = request.GET.get('name')

        if request.GET.get('description') == None:
            description = request.GET.get('description')
        else:
            description = classroom.description
        user = User.objects.filter(id=request.user.id).first()
        newClassroom = Classroom.objects.create(name=name, description=description)
        newClassroom.students.add(user)

        tasks = ClassroomTask.objects.filter(classroom=classroom).all()
        for task in tasks:
            newTask = ClassroomTask.objects.create(isAssignment=task.isAssignment, classroom=newClassroom, title=task.title, description=task.description, deadline=task.deadline, weight=task.weight)
            taskFiles = TaskFile.objects.filter(task=task).all()
            taskfiles = []
            for file in taskFiles:
                taskfiles.append(TaskFile(file=file.file, task=newTask))
            TaskFile.objects.bulk_create(taskfiles)

        messages.success(request, 'Clone classroom successfully!')
        return redirect(reverse('classroom_details', args=[newClassroom.id]))
    
@login_required(login_url='login')
def quizPage(request: HttpRequest, classroomId: int):
    if request.method == 'GET':
        classroom = Classroom.objects.filter(id=classroomId).first()
        if classroom == None:
            return render(request, '404page.html')
        if not isTeacher(request.user.id, classroomId):
            return render(request, '403page.html')
        
        quizes = Quiz.objects.filter(classroom=classroom).all()
        for i in range(len(quizes)):
            quizes[i].questionCount = QuizQuestion.objects.filter(quiz=quizes[i]).count()
            quizes[i].yourSubmission = QuizSubmission.objects.filter(quiz=quizes[i], student=request.user).first()

        isCurrentUserTeacher = isTeacher(request.user.id, classroomId)

        context = {'classroom': classroom, 'quizes': quizes, 'isTeacher': isCurrentUserTeacher}
        return render(request, 'quiz_page.html', context)
    elif request.method == 'POST':
        #Create new quiz
        classroom = Classroom.objects.filter(id=classroomId).first()
        if classroom == None:
            return render(request, '404page.html')
        if not isTeacher(request.user.id, classroomId):
            return render(request, '403page.html')
        
        title = request.POST.get('title')
        description = request.POST.get('description')
        deadline = request.POST.get('deadline')
        try:
            deadline = dateparse(deadline)
        except:
            deadline = None
        
        newQuiz = Quiz.objects.create(classroom=classroom, deadline=deadline, title=title, description=description)
        newQuiz.save()
        messages.success(request, 'Create quiz successfully!')
        return redirect(reverse('quiz_edit', args=[newQuiz.id]))

valid_answer = ['a', 'b', 'c', 'd', 'e']

@login_required(login_url='login')
def editDeleteQuiz(request: HttpRequest, quizId: int):
    if request.method == 'POST':
        if request.POST.get('_method') == 'delete':
            quiz = Quiz.objects.filter(id=quizId).first()
            if quiz == None:
                return render(request, '404page.html')
            if not isTeacher(request.user.id, quiz.classroom.id):
                return render(request, '403page.html')
            
            quiz.delete()
            messages.success(request, 'Delete quiz successfully!')
            return redirect(reverse('classroom_details', args=[quiz.classroom.id]))
        elif request.POST.get('_method') == 'put':
            quiz = Quiz.objects.filter(id=quizId).first()
            if quiz == None:
                return render(request, '404page.html')
            if not isTeacher(request.user.id, quiz.classroom.id):
                return render(request, '403page.html')
            
            title = request.POST.get('title')
            description = request.POST.get('description')
            deadline = request.POST.get('deadline')
            try:
                deadline = dateparse(deadline)
            except:
                deadline = None
            
            quiz.title = title
            quiz.description = description
            quiz.deadline = deadline
            try:
                quiz.save()
            except:
                messages.error(request, 'Error saving quiz details!')
                return redirect(reverse('classroom_details', args=[quiz.classroom.id]))
            messages.success(request, 'Edit quiz successfully!')
            return redirect(reverse('quiz_page', args=[quiz.id]))
    else:
        return render(request, '404page.html')

@login_required(login_url='login')
def addQuestionToQuiz(request: HttpRequest, quizId: int):
    if request.method == 'GET':
        quiz = Quiz.objects.filter(id=quizId).first()
        if quiz == None:
            return render(request, '404page.html')
        if not isTeacher(request.user.id, quiz.classroom.id):
            return render(request, '403page.html')
        
        context = {'quiz': quiz}
        return render(request, 'question_create.html', context)
    elif request.method == 'POST':
        quiz = Quiz.objects.filter(id=quizId).first()
        if quiz == None:
            return render(request, '404page.html')
        if not isTeacher(request.user.id, quiz.classroom.id):
            return render(request, '403page.html')
        
        question = request.POST.get('question')
        a = request.POST.get('a')
        b = request.POST.get('b')
        c = request.POST.get('c')
        d = request.POST.get('d')
        e = request.POST.get('e')
        answer = request.POST.get('answer')
        if answer not in valid_answer:
            messages.error(request, 'Answer must be a, b, c, d or e!')
            return redirect(reverse('quiz_question_edit', args=[quizId]))
        
        image = request.FILES.get('image')
        audio = request.FILES.get('audio')
        video = request.FILES.get('video')
        
        newQuestion = QuizQuestion.objects.create(quiz=quiz, question=question, correct=answer, 
                                                  a=a, b=b, c=c, d=d, e=e, audio=audio, video=video, image=image)
        newQuestion.save()
        messages.success(request, 'Add question successfully!')
        return redirect(reverse('quiz_question_edit', args=[quizId]))
    
@login_required(login_url='login')
def quizDetails(request: HttpRequest, quizId: int):
    if request.method == 'GET':
        quiz = Quiz.objects.filter(id=quizId).first()
        if quiz == None:
            return render(request, '404page.html')

        isCurrentUserTeacher = isTeacher(request.user.id, quiz.classroom.id)
        context = {'quiz': quiz,  'isTeacher': isCurrentUserTeacher}
        return render(request, 'quiz_edit.html', context)
    else:
        return render(request, '404page.html')

@login_required(login_url='login')
def quizQuestionDetails(request: HttpRequest, quizId: int):
    if request.method == 'GET':
        quiz = Quiz.objects.filter(id=quizId).first()
        if quiz == None:
            return render(request, '404page.html')
        
        questions = QuizQuestion.objects.filter(quiz=quiz).all()
        editingQuestionId = request.GET.get('editingQuestionId')
        try:
            editingQuestionId = int(editingQuestionId)
        except:
            editingQuestionId = None

        isCurrentUserTeacher = isTeacher(request.user.id, quiz.classroom.id)
        context = {'quiz': quiz, 'questions': questions, 'editingQuestionId': editingQuestionId, 'isTeacher': isCurrentUserTeacher}
        return render(request, 'quiz_question_edit.html', context)
    else:
        return render(request, '404page.html')

def editDeleteQuestion(request: HttpRequest, questionId: int):
    if request.method == 'POST':
        if request.POST.get('_method') == 'delete':
            question = QuizQuestion.objects.filter(id=questionId).first()
            if question == None:
                return render(request, '404page.html')
            if not isTeacher(request.user.id, question.quiz.classroom.id):
                return render(request, '403page.html')
            
            question.delete()
            messages.success(request, 'Delete question successfully!')
            return redirect(reverse('quiz_question_edit', args=[question.quiz.id]))
        elif request.POST.get('_method') == 'put':
            question = QuizQuestion.objects.filter(id=questionId).first()
            if question == None:
                return render(request, '404page.html')
            if not isTeacher(request.user.id, question.quiz.classroom.id):
                return render(request, '403page.html')
            
            question.question = request.POST.get('question')
            question.a = request.POST.get('a')
            question.b = request.POST.get('b')
            question.c = request.POST.get('c')
            question.d = request.POST.get('d')
            question.e = request.POST.get('e')
            answer = request.POST.get('answer')

            image = request.FILES.get('image')
            audio = request.FILES.get('audio')
            video = request.FILES.get('video')
            if answer not in valid_answer:
                messages.error(request, 'Answer must be a, b, c, d or e!')
                return redirect(reverse('quiz_question_edit', args=[question.quiz.id]))
            question.answer = answer
            question.image = image; question.audio = audio; question.video = video;
            question.save()
            messages.success(request, 'Edit question successfully!')
            return redirect(reverse('quiz_question_edit', args=[question.quiz.id]))
        else:
            return render(request, '404page.html')
    else:
        return render(request, '404page.html')

@login_required(login_url='login')
def answerQuiz(request: HttpRequest, quizId: int):
    if request.method == 'GET':
        quiz = Quiz.objects.filter(id=quizId).first()
              
        if quiz == None:
            return render(request, '404page.html')
        #if isTeacher(request.user.id, quiz.classroom.id):
        #    return render(request, '403page.html')
        
        if quiz.deadline != None and quiz.deadline < datetime.now(tz=quiz.deadline.tzinfo):
            messages.error(request, 'Quiz is expired!')
            return redirect(reverse('quiz_page', args=[quiz.classroom.id]))
        
        questions = QuizQuestion.objects.filter(quiz=quiz).all()
        context = {'quiz': quiz, 'questions': questions}
        return render(request, 'quiz_answer.html', context)
    elif request.method == 'POST':

        quiz = Quiz.objects.filter(id=quizId).first()
        oldSubmission = QuizSubmission.objects.filter(student=request.user, quiz=quiz).first()
        if oldSubmission != None:
            oldSubmission.delete()
        if quiz == None:
            return render(request, '404page.html')
        #if isTeacher(request.user.id, quiz.classroom.id):
        #    return render(request, '403page.html')
        
        questions = QuizQuestion.objects.filter(quiz=quiz).all()
        correctCount = 0
        newSubmission = QuizSubmission.objects.create(student=request.user, quiz=quiz)
        
        answers = []
        for question in questions:
            answer = request.POST.get(str(question.id))
            if answer == question.correct:
                correctCount += 1
            answers.append(QuizSubmissionAnswer(question=question, answer=answer, submission=newSubmission))

        QuizSubmissionAnswer.objects.bulk_create(answers)
        questionCount = QuizQuestion.objects.filter(quiz=quiz).count()
        newSubmission.correctCount = correctCount
        newSubmission.save()

        messages.success(request, 'Answer quiz successfully!\nYou got ' + str(correctCount) + 
                         ' out of ' + str(questionCount) +' correct answers!')
        return redirect(reverse('quiz_page', args=[quiz.classroom.id]))
    
@login_required(login_url='login')
def deleteQuizAnswer(request: HttpRequest, submissionId: int):
    if request.method == 'POST':
        submission = QuizSubmission.objects.filter(id=submissionId).first()
        if submission == None:
            return render(request, '404page.html')
        if not isTeacher(request.user.id, submission.quiz.classroom.id):
            return render(request, '403page.html')
        
        submission.delete()
        messages.success(request, 'Delete quiz answer successfully!')
        return redirect(reverse('student_quiz_submissions', args=[submission.quiz.id]))
    else:
        return render(request, '404page.html')
    
@login_required(login_url='login')
def studentQuizSubmissions(request: HttpRequest, quizId: int):
    if request.method == 'GET':
        quiz = Quiz.objects.filter(id=quizId).first()
        if quiz == None:
            return render(request, '404page.html')
        if not isTeacher(request.user.id, quiz.classroom.id):
            return render(request, '403page.html')
        
        quizQuestionCount = QuizQuestion.objects.filter(quiz=quiz).count()
        submissions = QuizSubmission.objects.filter(quiz=quiz).all()
        context = {'quiz': quiz, 'submissions': submissions, 'questionCount': quizQuestionCount}
        return render(request, 'quiz_submissions.html', context)
    else:
        return render(request, '404page.html')