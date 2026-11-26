from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Course, Lesson, Quiz, Question, Choice, Assignment, Submission, Profile


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=False)
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES, initial='student')

    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            Profile.objects.create(user=user, role=self.cleaned_data['role'])
        return user


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ('title', 'description')


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ('title', 'content', 'video_url', 'file', 'order')


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ('title',)


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ('text',)


class ChoiceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].required = False  # blank choice rows are simply ignored

    class Meta:
        model = Choice
        fields = ('text', 'is_correct')


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ('title', 'description', 'due_date')
        widgets = {'due_date': forms.DateInput(attrs={'type': 'date'})}


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ('file',)


class GradeForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ('grade', 'feedback')
