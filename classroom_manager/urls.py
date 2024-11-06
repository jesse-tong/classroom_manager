from django.urls import path

from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('', views.home, name="homepage"),
    path('login', views.loginPage, name="login"),
    path('register', views.registerPage, name="register"),
    path('register_admin', views.registerAdmin, name="register_admin"),
    path('site_settings', views.siteSettings, name="site_settings"),
    path('logout', views.logoutUser, name='logout'),

    path('classroom', views.classroomPage, name="classroom_list"),
    path('classroom/create', views.classroomCreatePage, name="classroom_create"),
    path('classroom/<int:classroomId>/copy', views.cloneClassroom, name="classroom_copy"),
    path('classroom/<int:id>', views.classroomDetailPage, name="classroom_details"),
    path('classroom/<int:classroomId>/analytics', views.classroomAnalytics, name="classroom_analytics"),
    path('classroom/<int:classroomId>/gpaCount', views.classroomSubmissionCountByGpa, name="classroom_gpa_count"),
    path('classroom/<int:classroomId>/users', views.classroomUsers, name="classroom_details_users"),
    path('classroom/<int:classroomId>/jitsi', views.classroomJitsi, name="classroom_jitsi"),
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
    path('classroom/task/<int:taskId>/add-comment', views.addCommentToTask, name="add_comment"),
    path('classroom/comment/<int:commentId>', views.editDeleteComment, name="edit_delete_comment"),
    path('classroom/gpa/<int:classroomId>', views.getGpaOfAllStudents, name="gpa_by_classroom_id"),

    path('classroom/<int:classroomId>/createGroup', views.createLearnGroup, name="create_learn_group"),
    path('classroom/group/<int:groupId>/search', views.searchInGroupEdit, name="search_in_group_edit"),
    path('classroom/group/<int:groupId>/edit', views.editDeleteLearnGroup, name="edit_delete_learn_group"),
    path('classroom/group/<int:groupId>', views.learnGroupDetails, name="learn_group_details"),
    path('classroom/group/<int:groupId>/addComment', views.addCommentToLearnGroup, name="add_comment_to_learn_group"),
    path('classroom/group/comment/<int:commentId>', views.editDeleteCommentLearnGroup, name="edit_delete_group_comment"),
    path('classroom/group/<int:groupId>/addStudent/<int:memberId>', views.addMemberToLearnGroup, name="add_student_to_learn_group"),
    path('classroom/group/<int:groupId>/removeStudent/<int:memberId>', views.deleteMemberFromLearnGroup, name="remove_student_from_learn_group"),

    path('classroom/<int:classroomId>/quiz', views.quizPage, name="quiz_page"),
    path('classroom/quiz/<int:quizId>', views.quizDetails, name="quiz_edit"),
    path('classroom/quiz/<int:quizId>/questions', views.quizQuestionDetails, name="quiz_question_edit"),
    path('classroom/quiz/<int:quizId>/answer', views.answerQuiz, name="answer_quiz"),
    path('classroom/quiz/<int:quizId>/edit', views.editDeleteQuiz, name="edit_delete_quiz"),
    path('classroom/quiz/<int:quizId>/add', views.addQuestionToQuiz, name="add_question_to_quiz"),
    path('classroom/quiz/question/<int:questionId>', views.editDeleteQuestion, name="edit_delete_question"),
    path('classroom/quiz/answer/<int:submissionId>/delete', views.deleteQuizAnswer, name="delete_quiz_answer"),
    path('classroom/quiz/<int:quizId>/answers', views.studentQuizSubmissions, name="student_quiz_submissions"),
    
    path('user/schedule', views.allTaskSchedules, name="all_task_schedules"),
    path('user/change-password', views.changePassword, name="change_password"),
    path('user/profile/<int:userId>', views.profilePage, name="profile_page"),
    path('user/profile/edit', views.editProfile, name="edit_profile"),
]