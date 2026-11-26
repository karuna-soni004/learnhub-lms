from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    path('courses/new/', views.course_create, name='course_create'),
    path('courses/<int:pk>/', views.course_detail, name='course_detail'),
    path('courses/<int:pk>/enroll/', views.enroll, name='enroll'),
    path('courses/<int:pk>/edit/', views.course_edit, name='course_edit'),
    path('courses/<int:pk>/delete/', views.course_delete, name='course_delete'),
    path('courses/<int:pk>/students/', views.course_students, name='course_students'),
    path('courses/<int:course_id>/lessons/add/', views.lesson_add, name='lesson_add'),
    path('courses/<int:course_id>/quizzes/add/', views.quiz_add, name='quiz_add'),
    path('courses/<int:course_id>/assignments/add/', views.assignment_add, name='assignment_add'),

    path('lessons/<int:pk>/', views.lesson_detail, name='lesson_detail'),
    path('lessons/<int:pk>/complete/', views.mark_complete, name='mark_complete'),

    path('quizzes/<int:pk>/take/', views.take_quiz, name='take_quiz'),
    path('quizzes/<int:quiz_id>/questions/add/', views.question_add, name='question_add'),
    path('results/<int:pk>/', views.quiz_result, name='quiz_result'),

    path('assignments/<int:pk>/submit/', views.submit_assignment, name='submit_assignment'),
    path('assignments/<int:pk>/submissions/', views.submissions_list, name='submissions'),
    path('submissions/<int:pk>/grade/', views.grade_submission, name='grade_submission'),
]
