from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from lms.models import (Profile, Course, Lesson, Enrollment, LessonProgress, Quiz, Question, Choice, Assignment)


class Command(BaseCommand):
    help = 'Create demo users, a sample course, a quiz and an assignment'

    def handle(self, *args, **opts):
        inst, _ = User.objects.get_or_create(username='instructor1')
        inst.set_password('demo12345'); inst.save()
        Profile.objects.update_or_create(user=inst, defaults={'role': 'instructor'})
        stu, _ = User.objects.get_or_create(username='student1')
        stu.set_password('demo12345'); stu.save()
        Profile.objects.update_or_create(user=stu, defaults={'role': 'student'})

        course, created = Course.objects.get_or_create(
            title='Python for Beginners', instructor=inst,
            defaults={'description': 'Learn Python from scratch: variables, control flow, functions and more.'})
        if created:
            Lesson.objects.create(course=course, order=1, title='Introduction to Python',
                                  content='Python is a popular, beginner-friendly programming language.\nIn this lesson we set up Python and run our first program.',
                                  video_url='https://www.youtube.com/embed/kqtD5dpn9C8')
            Lesson.objects.create(course=course, order=2, title='Variables and Data Types',
                                  content='Variables store data. Common types: int, float, str, bool, list, dict.')
            Lesson.objects.create(course=course, order=3, title='Control Flow',
                                  content='Use if/elif/else for decisions and for/while for loops.')
            quiz = Quiz.objects.create(course=course, title='Python Basics Quiz')
            q1 = Question.objects.create(quiz=quiz, text='Which keyword defines a function in Python?')
            for t, ok in [('def', True), ('func', False), ('function', False), ('lambda only', False)]:
                Choice.objects.create(question=q1, text=t, is_correct=ok)
            q2 = Question.objects.create(quiz=quiz, text='Which of these is a mutable data type?')
            for t, ok in [('tuple', False), ('str', False), ('list', True)]:
                Choice.objects.create(question=q2, text=t, is_correct=ok)
            Assignment.objects.create(course=course, title='Write a calculator script',
                                      description='Upload a .py file with a simple command-line calculator.')
        Enrollment.objects.get_or_create(student=stu, course=course)
        first = course.lessons.first()
        if first:
            LessonProgress.objects.get_or_create(student=stu, lesson=first)
        self.stdout.write(self.style.SUCCESS('Demo data ready. Logins: instructor1 / student1, password: demo12345'))
