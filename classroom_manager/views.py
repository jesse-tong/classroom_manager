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
from datetime import datetime as dt
from dateutil import relativedelta
from dateutil.parser import parse as dateparse
from django.db.models import Count, Sum, F
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
        email = request.POST.get('email')

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
def classroomPage(request: HttpRequest):
    if request.method == 'GET':
        currentUserId = request.user.id
        #Q object represent filter object that can have logical operators like | and &
        #Here is the query to find any classroom where the any student or any teacher in the classroom
        #has current logged in user ID
        classroomsUserIsStudent= Classroom.objects \
            .filter(Q(students__id__contains=currentUserId))
        classroomsUserIsTeacher= Classroom.objects \
            .filter(Q(teachers__id__contains=currentUserId))
        context = {'classroomsUserIsStudent': classroomsUserIsStudent, 
                   'classroomsUserIsTeacher': classroomsUserIsTeacher}
        return render(request, 'classroom.html', context)
    elif request.method == 'POST':
        if request.POST.get('name') == None:
            messages.error(request, 'Classroom must have a name!')
            return redirect(reverse('classroom_create'))
        name = request.POST.get('name')
        description = request.POST.get('description')
        if description == None:
            description = ''
        newClassroom = Classroom.objects.create(name=name, description=description)
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
        if description == None:
            description = ''
        newClassroom = Classroom.objects.create(name=name, description=description)
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
        students = classroom.students.all()
        teachers = classroom.teachers.all()
        isCurrentUserTeacher = isTeacher(request.user.id, classroom.id)
        context = {'classroom': classroom, 'students': students, 'teachers': teachers, 'classroomId': id, 
                     'isTeacher': isCurrentUserTeacher, 'joinPath': request.get_host() + reverse('join_classroom_by_id', args=[classroomId]) }
        return render(request, 'classroom_details_users.html', context)
    else:
        return render(request, '404page.html')

@login_required(login_url='login')
def classroomDetailPage(request: HttpRequest, id):
    if request.method == 'GET':
        classroom = Classroom.objects.filter(id=id).first()
        if classroom != None:
            students = classroom.students.all()
            teachers = classroom.teachers.all()
            tasks = ClassroomTask.objects.filter(classroom=classroom).all()
            isCurrentUserTeacher = isTeacher(request.user.id, classroom.id)
            context = {'classroom': classroom, 'students': students, 'teachers': teachers, 'classroomId': id, 
                       'tasks': tasks, 'isTeacher': isCurrentUserTeacher, 'joinPath': request.get_host() + reverse('join_classroom_by_id', args=[id]) }
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
            if description == None:
                description = ''
            classroom = Classroom.objects.filter(id=id).first()
            if not classroom:
                messages.error(request, 'Classroom with ID ' + id + ' does not exists!')
                return redirect('/classroom')
            
            classroom.name = name; classroom.description = description
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
        tasks = ClassroomTask.objects.filter(classroom=classroom)
        isCurrentUserTeacher = isTeacher(request.user.id, classroomId=classroom.id)
        context = {'classroom': classroom, 'tasks': tasks, 'isTeacher': isCurrentUserTeacher, 'joinPath': request.get_host() + reverse('join_classroom_by_id', args=[classroom.id]) }
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
        editingCommentId = request.GET.get('editingCommentId')

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
        lateTaskScope = now - relativedelta.relativedelta(months=2)
        upcomingTasks = ClassroomTask.objects.filter((Q(classroom__students__id__contains=request.user.id) 
                                                      |Q (classroom__teachers__id__contains=request.user.id) )& Q(deadline__gte=now) ).all()
        lateTasks = ClassroomTask.objects.filter((Q(classroom__students__id__contains=request.user.id) 
                                                      |Q (classroom__teachers__id__contains=request.user.id) )& Q(deadline__gte=lateTaskScope) & Q(deadline__lte=now)).all()

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

        context = {'upcomingTasks': upcomingTasks, 'lateTasks': lateTasks, 
                   'daysArray': daysArray, 'currentDay': currentDay, 'monthString': monthString, 
                   'yearString': yearString, 'daysWithDeadlines': daysWithDeadlines, 'lastMonth': lastMonth, 'nextMonth': nextMonth}    
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