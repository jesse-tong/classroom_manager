from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
import random

asset_backgrounds = ['img_backtoschool.jpg', 'img_code.jpg', 'img_gamenight.jpg', 'img_hobby.jpg', 'img_learnlanguage.jpg', 'img_violin2.jpg', ]

def get_random_class_image():
    return random.choice(asset_backgrounds)

class Classroom(models.Model):
    name = models.CharField(max_length=200)
    teachers = models.ManyToManyField(User, related_name="classroom_teacher")
    students = models.ManyToManyField(User, related_name="classroom_student")
    description = models.CharField(max_length=3000)
    background = models.CharField(max_length=200, default=get_random_class_image)
    def __str__(self):
        return self.name
    def asjson(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'background': self.background,
        }

class ClassroomTask(models.Model):
    isAssignment = models.BooleanField(default=True)
    title = models.CharField(max_length=200, null=True)
    description = models.CharField(max_length=5000, null=True)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    deadline = models.DateTimeField(null=True)
    acceptLateSubmission = models.BooleanField(default=True)
    weight = models.FloatField(default=0.0)
    def __str__(self):
        return self.description[:50]
    
    def asjson(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'isAssignment': self.isAssignment,
            'classroom': self.classroom.asjson(),
            'deadline': self.deadline,
            'acceptLateSubmission': self.acceptLateSubmission,
        }

class TaskComment(models.Model):
    commenter = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.CharField(max_length=5000)
    task = models.ForeignKey(ClassroomTask, on_delete=models.CASCADE)
    creationDate = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.comment[:50] + '... from user ' + str(self.commenter.username)


class Submission(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(ClassroomTask, on_delete=models.CASCADE)
    lastSubmission = models.DateTimeField(auto_now_add=True)
    gpa = models.FloatField(null=True)
    def __str__(self):
        return self.student.username + '\'s submission on task ' + self.task.description[:30]

def task_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/task_<id>/<filename>
    return "task_{0}/{1}".format(instance.task.id, filename)

def submission_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/submission_<id>/<filename>
    return "submission_{0}/{1}".format(instance.submission.id, filename)

def group_directory_path(instance, filename):
    return "group_{0}/{1}".format(instance.learnGroup.id, filename)

class SubmissionFile(models.Model):
    file = models.FileField(upload_to=submission_directory_path, null=True)
    comment = models.CharField(max_length=3000)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    def __str__(self):
        return self.file.name

class TaskFile(models.Model):
    file = models.FileField(upload_to=task_directory_path,null=True)
    comment = models.CharField(max_length=3000)
    task = models.ForeignKey(ClassroomTask, on_delete=models.CASCADE)
    def __str__(self):
        return self.file.name

class LearnGroup(models.Model):
    students = models.ManyToManyField(User, related_name="learn_group_student")
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)

class GroupComment(models.Model):
    commenter = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.CharField(max_length=5000)
    learnGroup = models.ForeignKey(LearnGroup, on_delete=models.CASCADE)
    creationDate = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='group_comment_files' ,null=True)
    def __str__(self):
        return self.comment[:50] + '... from user ' + str(self.commenter.username)

class GroupCommentFile(models.Model):
    file = models.FileField(upload_to=group_directory_path, null=True)
    comment = models.ForeignKey(GroupComment, on_delete=models.CASCADE)
    def __str__(self):
        return self.file.name
    
class Configuration(models.Model):
    key = models.CharField(max_length=200)
    value = models.CharField(max_length=200)
    def __str__(self):
        return self.key + ' = ' + self.value

