from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
import tempfile

from .models import Course, Enrollment, LessonProgress, QuizAttempt, Submission, Quiz, Question, Choice


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class LMSFlowTests(TestCase):
    def setUp(self):
        call_command('seed_demo', verbosity=0)
        self.course = Course.objects.get(title='Python for Beginners')

    def test_public_pages(self):
        self.assertEqual(self.client.get(reverse('home')).status_code, 200)
        self.assertEqual(self.client.get(reverse('course_detail', args=[self.course.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('login')).status_code, 200)

    def test_signup_and_enroll_and_progress(self):
        r = self.client.post(reverse('signup'), {'username': 'newbie', 'email': 'n@x.com', 'role': 'student',
                                                 'password1': 'Str0ngPass!234', 'password2': 'Str0ngPass!234'})
        self.assertRedirects(r, reverse('dashboard'))
        self.client.post(reverse('enroll', args=[self.course.pk]))
        self.assertTrue(Enrollment.objects.filter(student__username='newbie').exists())
        lesson = self.course.lessons.first()
        self.assertEqual(self.client.get(reverse('lesson_detail', args=[lesson.pk])).status_code, 200)
        self.client.post(reverse('mark_complete', args=[lesson.pk]))
        self.assertEqual(self.course.progress_for(User.objects.get(username='newbie')), 33)

    def test_lesson_requires_enrollment(self):
        User.objects.create_user('outsider', password='x12345678')
        self.client.login(username='outsider', password='x12345678')
        lesson = self.course.lessons.first()
        r = self.client.get(reverse('lesson_detail', args=[lesson.pk]))
        self.assertEqual(r.status_code, 302)

    def test_quiz_scoring(self):
        self.client.login(username='student1', password='demo12345')
        quiz = Quiz.objects.get(course=self.course)
        data = {}
        for q in quiz.questions.all():
            data[f'q{q.id}'] = q.choices.get(is_correct=True).pk
        r = self.client.post(reverse('take_quiz', args=[quiz.pk]), data)
        attempt = QuizAttempt.objects.get()
        self.assertEqual((attempt.score, attempt.total), (2, 2))
        self.assertRedirects(r, reverse('quiz_result', args=[attempt.pk]))
        self.assertEqual(self.client.get(reverse('quiz_result', args=[attempt.pk])).status_code, 200)

    def test_assignment_submit_and_grade(self):
        self.client.login(username='student1', password='demo12345')
        a = self.course.assignments.first()
        f = SimpleUploadedFile('calc.py', b'print(1+1)')
        self.client.post(reverse('submit_assignment', args=[a.pk]), {'file': f})
        sub = Submission.objects.get()
        self.client.logout()
        self.client.login(username='instructor1', password='demo12345')
        self.assertEqual(self.client.get(reverse('submissions', args=[a.pk])).status_code, 200)
        self.client.post(reverse('grade_submission', args=[sub.pk]), {'grade': 'A', 'feedback': 'Nice'})
        sub.refresh_from_db()
        self.assertEqual(sub.grade, 'A')

    def test_instructor_flows(self):
        self.client.login(username='instructor1', password='demo12345')
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 200)
        r = self.client.post(reverse('course_create'), {'title': 'Django Basics', 'description': 'Web dev'})
        c = Course.objects.get(title='Django Basics')
        self.assertRedirects(r, reverse('course_detail', args=[c.pk]))
        self.client.post(reverse('lesson_add', args=[c.pk]), {'title': 'L1', 'content': 'hi', 'order': 1})
        self.assertEqual(c.lessons.count(), 1)
        self.client.post(reverse('quiz_add', args=[c.pk]), {'title': 'Q'})
        quiz = c.quizzes.get()
        self.client.post(reverse('question_add', args=[quiz.pk]), {
            'q-text': 'Capital of France?', 'c0-text': 'Paris', 'c0-is_correct': 'on',
            'c1-text': 'Rome', 'c2-text': '', 'c3-text': ''})
        self.assertEqual(Question.objects.filter(quiz=quiz).count(), 1)
        self.assertEqual(Choice.objects.filter(question__quiz=quiz).count(), 2)
        self.client.post(reverse('assignment_add', args=[c.pk]), {'title': 'A1', 'description': 'd'})
        self.assertEqual(c.assignments.count(), 1)
        self.assertEqual(self.client.get(reverse('course_students', args=[self.course.pk])).status_code, 200)

    def test_student_cannot_manage(self):
        self.client.login(username='student1', password='demo12345')
        self.assertEqual(self.client.get(reverse('course_create')).status_code, 403)
        self.assertEqual(self.client.get(reverse('lesson_add', args=[self.course.pk])).status_code, 403)
