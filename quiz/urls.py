# quiz/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),                     # 測驗首頁
    path('start/', views.start_quiz, name='start_quiz'),   # 開始測驗
    path('submit/', views.submit_quiz, name='submit_quiz'), # 交卷
    path('review/', views.review_wrong_questions, name='review_wrong_questions'), # 錯題本
]