# Generated by Django 5.1 on 2024-09-19 09:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('classroom_manager', '0005_alter_classroomtask_description_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='classroom',
            name='background',
            field=models.CharField(default='img_learnlanguage.jpg', max_length=200),
        ),
    ]