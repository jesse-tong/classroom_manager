from django.urls import path

from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('', views.home, name="homepage"),
    path('login', views.loginPage, name="login"),
    path('register', views.registerPage, name="register"),
    path('logout', views.logoutUser, name='logout'),
    path('classroom', views.classroomPage, name="classroom_list"),
    path('classroom/create', views.classroomCreatePage, name="classroom_create"),
    path('classroom/<int:id>', views.classroomDetailPage, name="classroom_details"),
    path('classroom/<int:classroomId>/users', views.classroomUsers, name="classroom_details_users"),
    path('classroom/edit/<int:id>', views.classroomEditPage, name="classroom_edit"),
    path('classroom/edit/<int:classroomId>/searchUser', views.searchInClassroomEdit, name="classroom_edit_search_user"),
    path('classroom/<int:classroomId>/add-student/<int:studentId>', views.addStudentToClassroom, name="add_student_to_classroom"),
    path('classroom/<int:classroomId>/remove-student/<int:studentId>', views.removeStudentInClassroom, name="remove_student_in_classroom"),
    path('classroom/<int:classroomId>/add-teacher/<int:teacherId>', views.addTeacherToClassroom, name="add_teacher_to_classroom"),
    path('classroom/<int:classroomId>/remove-teacher/<int:teacherId>', views.removeTeacherInClassroom, name="remove_teacher_in_classroom"),
    path('classroom/<int:classroomId>/create-task', views.createTaskPage, name="task_create"),
    path('classroom/join-by-id/<int:classroomId>', views.joinByClassroomId, name="join_classroom_by_id"),
    path('classroom/task/<int:taskId>/submit', views.submitToTask, name="submit_task"),
    path('classroom/task/<int:taskId>', views.getEditDeleteTaskById, name="task_details"),
    path('classroom/submission/<int:submissionId>', views.submissionDetailsPage, name="submission_details"),
    path('classroom/task/<int:taskId>/submissions', views.getSubmissionsByTaskId, name="submissions_by_task_id"),
    path('user/deadlines', views.allTaskDeadlines, name="all_task_deadlines"),
    path('get-deadlines', views.getTaskDeadlines, name="get_deadlines"),
]