from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views 
from quiz import views 

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. 妳們原本的測驗系統路由（把 start_quiz 和 submit_quiz 都完美留下來！）
    path('', views.home, name='home'), 
    path('start/', views.start_quiz, name='start_quiz'), 
    
    # 【就是這一行！請務必補上】
    # ⚠️ 註：後面的 views.submit_quiz 請對照妳們 views.py 裡面負責處理交卷、算分的那個 function 名稱
    path('submit/', views.submit_quiz, name='submit_quiz'), 
    
    # 2. 全新加入的登入、登出、註冊與錯題本路由
    path('login/', auth_views.LoginView.as_view(template_name='quiz/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('register/', views.register_view, name='register'),
    path('wrong-questions/', views.wrong_questions_view, name='wrong_questions'),
    path('review-wrong/', views.review_wrong_questions, name='review_wrong_questions'),
    path('history/', views.history_view, name='history'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
]
