from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (SignUpForm, CourseForm, LessonForm, QuizForm, QuestionForm, ChoiceForm,
                    AssignmentForm, SubmissionForm, GradeForm)
from .models import (Course, Lesson, Enrollment, LessonProgress, Quiz, Question, Choice,
                     QuizAttempt, Assignment, Submission)


def is_instructor(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return hasattr(user, 'profile') and user.profile.role == 'instructor'


def _own_course_or_403(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    if not is_instructor(request.user) or (course.instructor != request.user and not request.user.is_superuser):
        return course, False
    return course, True


def home(request):
    q = request.GET.get('q', '').strip()
    courses = Course.objects.select_related('instructor')
    if q:
        courses = courses.filter(title__icontains=q)
    enrolled_ids = set()
    if request.user.is_authenticated:
        enrolled_ids = set(request.user.enrollments.values_list('course_id', flat=True))
    return render(request, 'lms/home.html', {'courses': courses, 'q': q, 'enrolled_ids': enrolled_ids})


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome! Your account has been created.')
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


@login_required
def dashboard(request):
    if is_instructor(request.user):
        courses = Course.objects.filter(instructor=request.user)
        return render(request, 'lms/instructor_dashboard.html', {'courses': courses})
    enrollments = request.user.enrollments.select_related('course')
    data = [{'course': e.course, 'progress': e.course.progress_for(request.user)} for e in enrollments]
    attempts = QuizAttempt.objects.filter(student=request.user).select_related('quiz')[:5]
    return render(request, 'lms/student_dashboard.html', {'data': data, 'attempts': attempts})


def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
    enrolled = request.user.is_authenticated and Enrollment.objects.filter(student=request.user, course=course).exists()
    done_ids = set()
    progress = 0
    if enrolled:
        done_ids = set(LessonProgress.objects.filter(student=request.user, lesson__course=course)
                       .values_list('lesson_id', flat=True))
        progress = course.progress_for(request.user)
    can_manage = is_instructor(request.user) and (course.instructor == request.user or request.user.is_superuser)
    submitted_ids = set()
    if enrolled:
        submitted_ids = set(Submission.objects.filter(student=request.user, assignment__course=course)
                            .values_list('assignment_id', flat=True))
    return render(request, 'lms/course_detail.html', {
        'course': course, 'enrolled': enrolled, 'done_ids': done_ids, 'progress': progress,
        'can_manage': can_manage, 'submitted_ids': submitted_ids,
    })


@login_required
def enroll(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if is_instructor(request.user):
        messages.error(request, 'Instructors cannot enroll in courses.')
    elif request.method == 'POST':
        Enrollment.objects.get_or_create(student=request.user, course=course)
        messages.success(request, f'You are enrolled in "{course.title}".')
    return redirect('course_detail', pk=pk)


@login_required
def lesson_detail(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    course = lesson.course
    manager = is_instructor(request.user) and (course.instructor == request.user or request.user.is_superuser)
    enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
    if not (enrolled or manager):
        messages.error(request, 'Please enroll in the course to view its lessons.')
        return redirect('course_detail', pk=course.pk)
    done = LessonProgress.objects.filter(student=request.user, lesson=lesson).exists()
    return render(request, 'lms/lesson_detail.html', {'lesson': lesson, 'course': course, 'done': done, 'enrolled': enrolled})


@login_required
def mark_complete(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    if request.method == 'POST' and Enrollment.objects.filter(student=request.user, course=lesson.course).exists():
        LessonProgress.objects.get_or_create(student=request.user, lesson=lesson)
        messages.success(request, 'Lesson marked as complete.')
    return redirect('lesson_detail', pk=pk)


@login_required
def take_quiz(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    if not Enrollment.objects.filter(student=request.user, course=quiz.course).exists():
        messages.error(request, 'Enroll in the course to take its quizzes.')
        return redirect('course_detail', pk=quiz.course.pk)
    questions = quiz.questions.prefetch_related('choices')
    if request.method == 'POST':
        score = 0
        total = questions.count()
        for q in questions:
            chosen = request.POST.get(f'q{q.id}')
            if chosen and q.choices.filter(pk=chosen, is_correct=True).exists():
                score += 1
        attempt = QuizAttempt.objects.create(student=request.user, quiz=quiz, score=score, total=total)
        return redirect('quiz_result', pk=attempt.pk)
    return render(request, 'lms/take_quiz.html', {'quiz': quiz, 'questions': questions})


@login_required
def quiz_result(request, pk):
    attempt = get_object_or_404(QuizAttempt, pk=pk, student=request.user)
    percent = int(attempt.score * 100 / attempt.total) if attempt.total else 0
    return render(request, 'lms/quiz_result.html', {'attempt': attempt, 'percent': percent})


@login_required
def submit_assignment(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    if not Enrollment.objects.filter(student=request.user, course=assignment.course).exists():
        messages.error(request, 'Enroll in the course to submit assignments.')
        return redirect('course_detail', pk=assignment.course.pk)
    existing = Submission.objects.filter(assignment=assignment, student=request.user).first()
    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES, instance=existing)
        if form.is_valid():
            sub = form.save(commit=False)
            sub.assignment = assignment
            sub.student = request.user
            sub.save()
            messages.success(request, 'Assignment submitted.')
            return redirect('course_detail', pk=assignment.course.pk)
    else:
        form = SubmissionForm(instance=existing)
    return render(request, 'lms/submit_assignment.html', {'assignment': assignment, 'form': form, 'existing': existing})


# ---------------- Instructor views ----------------

@login_required
def course_create(request):
    if not is_instructor(request.user):
        return HttpResponseForbidden('Instructors only.')
    form = CourseForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        course = form.save(commit=False)
        course.instructor = request.user
        course.save()
        messages.success(request, 'Course created. Now add lessons, quizzes and assignments.')
        return redirect('course_detail', pk=course.pk)
    return render(request, 'lms/form.html', {'form': form, 'title': 'Create course'})


def _manage_form(request, course_id, form_class, title, save_fn, files=False):
    course, ok = _own_course_or_403(request, course_id)
    if not ok:
        return None, HttpResponseForbidden('You do not manage this course.')
    form = form_class(request.POST or None, request.FILES or None) if files else form_class(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        save_fn(course, form)
        return None, redirect('course_detail', pk=course.pk)
    return None, render(request, 'lms/form.html', {'form': form, 'title': title, 'course': course})


@login_required
def course_edit(request, pk):
    course, ok = _own_course_or_403(request, pk)
    if not ok:
        return HttpResponseForbidden('You do not manage this course.')
    form = CourseForm(request.POST or None, instance=course)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('course_detail', pk=pk)
    return render(request, 'lms/form.html', {'form': form, 'title': 'Edit course', 'course': course})


@login_required
def course_delete(request, pk):
    course, ok = _own_course_or_403(request, pk)
    if not ok:
        return HttpResponseForbidden('You do not manage this course.')
    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Course deleted.')
        return redirect('dashboard')
    return render(request, 'lms/confirm_delete.html', {'course': course})


@login_required
def lesson_add(request, course_id):
    def save(course, form):
        lesson = form.save(commit=False)
        lesson.course = course
        lesson.save()
        messages.success(request, 'Lesson added.')
    _, resp = _manage_form(request, course_id, LessonForm, 'Add lesson', save, files=True)
    return resp


@login_required
def quiz_add(request, course_id):
    def save(course, form):
        quiz = form.save(commit=False)
        quiz.course = course
        quiz.save()
        messages.success(request, 'Quiz created. Add questions to it from the course page.')
    _, resp = _manage_form(request, course_id, QuizForm, 'Create quiz', save)
    return resp


@login_required
def question_add(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    course, ok = _own_course_or_403(request, quiz.course_id)
    if not ok:
        return HttpResponseForbidden('You do not manage this course.')
    qform = QuestionForm(request.POST or None, prefix='q')
    choice_forms = [ChoiceForm(request.POST or None, prefix=f'c{i}') for i in range(4)]
    if request.method == 'POST':
        valid = qform.is_valid() and all(cf.is_valid() for cf in choice_forms)
        filled = [cf for cf in choice_forms if valid and cf.cleaned_data.get('text')]
        if valid and len(filled) < 2:
            messages.error(request, 'Provide at least two choices.')
        elif valid and not any(cf.cleaned_data.get('is_correct') for cf in filled):
            messages.error(request, 'Mark at least one choice as correct.')
        elif valid:
            question = qform.save(commit=False)
            question.quiz = quiz
            question.save()
            for cf in filled:
                Choice.objects.create(question=question, text=cf.cleaned_data['text'],
                                      is_correct=cf.cleaned_data.get('is_correct', False))
            messages.success(request, 'Question added.')
            if 'add_another' in request.POST:
                return redirect('question_add', quiz_id=quiz.pk)
            return redirect('course_detail', pk=course.pk)
    return render(request, 'lms/question_form.html', {'quiz': quiz, 'qform': qform, 'choice_forms': choice_forms})


@login_required
def assignment_add(request, course_id):
    def save(course, form):
        a = form.save(commit=False)
        a.course = course
        a.save()
        messages.success(request, 'Assignment created.')
    _, resp = _manage_form(request, course_id, AssignmentForm, 'Create assignment', save)
    return resp


@login_required
def submissions_list(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    course, ok = _own_course_or_403(request, assignment.course_id)
    if not ok:
        return HttpResponseForbidden('You do not manage this course.')
    return render(request, 'lms/submissions.html', {
        'assignment': assignment, 'submissions': assignment.submissions.select_related('student')})


@login_required
def grade_submission(request, pk):
    sub = get_object_or_404(Submission, pk=pk)
    course, ok = _own_course_or_403(request, sub.assignment.course_id)
    if not ok:
        return HttpResponseForbidden('You do not manage this course.')
    form = GradeForm(request.POST or None, instance=sub)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Grade saved.')
        return redirect('submissions', pk=sub.assignment.pk)
    return render(request, 'lms/form.html', {'form': form, 'title': f'Grade {sub.student.username}', 'course': course})


@login_required
def course_students(request, pk):
    course, ok = _own_course_or_403(request, pk)
    if not ok:
        return HttpResponseForbidden('You do not manage this course.')
    rows = [{'student': e.student, 'progress': course.progress_for(e.student), 'enrolled_at': e.enrolled_at}
            for e in course.enrollments.select_related('student')]
    return render(request, 'lms/course_students.html', {'course': course, 'rows': rows})
