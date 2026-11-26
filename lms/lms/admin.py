from django.contrib import admin
from . import models

for m in [models.Profile, models.Course, models.Lesson, models.Enrollment, models.LessonProgress,
          models.Quiz, models.Question, models.Choice, models.QuizAttempt, models.Assignment, models.Submission]:
    admin.site.register(m)
