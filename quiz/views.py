from django.contrib import auth
from django.conf import settings
from django.shortcuts import render, redirect
from .models import Question, WrongQuestion
from .models import QuizRecord
from django.db.models import Avg, Count
from django.contrib.auth.models import User
from datetime import date, timedelta
from .models import DailyCheckIn
import random
import django.contrib.auth as auth  # 🎯【核心修正】改用這個，絕對 100% 抓得到登出工具！

# 首頁
def home(request):

    checkin_data = None
    already_checked = False

    if request.user.is_authenticated:

        checkin_data = DailyCheckIn.objects.filter(
            user=request.user
        ).first()

        if (
            checkin_data and
            checkin_data.last_checkin == date.today()
        ):
            already_checked = True

    return render(
        request,
        'quiz/home.html',
        {
            'checkin_data': checkin_data,
            'already_checked': already_checked
        }
    )

# 💡 核心小工具：抽取題目後，幫每題的選項隨機打亂
def prepare_shuffled_options(chosen_questions):
    for q in chosen_questions:
        # 💡 只把有填寫的「內容純文字」放進列表裡
        raw_options = []
        if q.option_a: raw_options.append(q.option_a)
        if q.option_b: raw_options.append(q.option_b)
        if q.option_c: raw_options.append(q.option_c)
        if q.option_d: raw_options.append(q.option_d)
        if q.option_e: raw_options.append(q.option_e)
        
        # 💥 只對內容純文字進行隨機洗牌
        random.shuffle(raw_options)
        
        # 💡 重新配對：按照洗牌後的順序，硬塞回 A、B、C、D、E 的標籤
        letter_labels = ['A', 'B', 'C', 'D', 'E']
        shuffled_result = []
        
        for i, option_text in enumerate(raw_options):
            # 這樣第一個格子一定叫 'A'，第二個一定叫 'B'，但裡面的內容是隨機的！
            shuffled_result.append((letter_labels[i], option_text))
            
        q.shuffled_options = shuffled_result
# 開始測驗（隨機抽題邏輯）
def start_quiz(request):
    num_questions = int(request.GET.get('num', 5))

    all_questions = list(Question.objects.all())

    chosen_questions = []
    wrong_questions = []
    weighted_wrong = []

    # =========================
    # 🧠 1. 錯題邏輯（先算）
    # =========================
    if request.user.is_authenticated:
        wrong_records = WrongQuestion.objects.filter(user=request.user)

        for wq in wrong_records:
            weight = 1

            if wq.memory_level == 0:
                weight = 5
            elif wq.memory_level == 1:
                weight = 3
            elif wq.memory_level == 2:
                weight = 2

            weighted_wrong.extend([wq.question] * weight)

        if weighted_wrong:
            wrong_questions = list(set(random.sample(
                weighted_wrong,
                min(len(weighted_wrong), num_questions // 2)
            )))

    # =========================
    # 🧠 2. 先放錯題
    # =========================
    chosen_questions.extend(wrong_questions)

    # =========================
    # 🧠 3. 再補一般題
    # =========================
    remaining_slots = num_questions - len(chosen_questions)

    pool = [q for q in all_questions if q not in chosen_questions]

    if remaining_slots > 0 and pool:
        new_picks = random.sample(pool, min(len(pool), remaining_slots))
        chosen_questions.extend(new_picks)

    # =========================
    # 🧠 4. 打亂順序
    # =========================
    random.shuffle(chosen_questions)

    # =========================
    # 🎯 5. 隨機選項
    # =========================
    prepare_shuffled_options(chosen_questions)

    # =========================
    # 💾 6. 存 session
    # =========================
    request.session['quiz_question_ids'] = [q.id for q in chosen_questions]

    return render(request, 'quiz/quiz.html', {
        'quiz_data': chosen_questions,
        'question_count': num_questions
    })

from django.shortcuts import render
from django.utils import timezone
from .models import Question, WrongQuestion

# 交卷計算分數與儲存錯題
def submit_quiz(request):
    if request.method == 'POST':
        question_ids = request.session.get('quiz_question_ids', [])
        score = 0
        total = len(question_ids)
        wrong_details = []

        for q_id in question_ids:
            try:
                question = Question.objects.get(id=q_id)
                
                # 1. 抓取前端傳來的「純文字回答」
                input_name = f"question_{question.id}"
                user_ans_text = request.POST.get(input_name)
                
                if not user_ans_text:
                    user_ans_text = '未答'

                # 2. 找出這題正確答案的字母（例如 'A'）與對應的「純文字內容」
                correct_letter = question.correct_answer.upper() # 確保是大寫 A, B, C...
                actual_correct_text = getattr(question, f'option_{correct_letter.lower()}', None)
                
                # 🎯【全新進化】逆向找出學生剛剛選的「純文字」到底對應哪一個英文字母
                user_letter = "未答"
                for letter in ['A', 'B', 'C', 'D', 'E']:
                    opt_text = getattr(question, f'option_{letter.lower()}', None)
                    if opt_text == user_ans_text:
                        user_letter = letter
                        break

                # 3. 完美組合出妳想要的「(字母) 完整文字」格式
                if user_letter != "未答":
                    final_user_display = f"({user_letter}) {user_ans_text}"
                else:
                    final_user_display = "未答"

                final_correct_display = f"({correct_letter}) {actual_correct_text}"

                # 4. 終極對決與計分
                if user_ans_text == actual_correct_text:
                    score += 1

                 # ⭐ 如果以前曾錯過這題
                    if request.user.is_authenticated:
                        try:
                            wrong_obj = WrongQuestion.objects.get(
                            user=request.user,
                                question=question
                            )

                            wrong_obj.correct_count += 1

                            # 提升熟練度
                            if wrong_obj.correct_count >= 2:

                                wrong_obj.memory_level = min(
                                    wrong_obj.memory_level + 1,
                                    3
                                )

                                wrong_obj.correct_count = 0

                            # ⭐ 更新下次複習時間
                            if wrong_obj.memory_level == 0:
                                delay_days = 0
                            elif wrong_obj.memory_level == 1:
                                delay_days = 1
                            elif wrong_obj.memory_level == 2:
                                delay_days = 3
                            else:
                                delay_days = 7

                            wrong_obj.next_review = (
                                timezone.now() +
                                timedelta(days=delay_days)
                            )

                            wrong_obj.save()

                        except WrongQuestion.DoesNotExist:
                            pass
                
                else:

                    # ⭐ 訪客不記錄錯題
                    if request.user.is_authenticated:
                        
                        wrong_obj, created = WrongQuestion.objects.get_or_create(
                            user=request.user,
                            question=question,
                            defaults={
                                'user_answer': final_user_display,
                            }
                        )

                        # 🧠 如果第一次錯
                        if created:
                            wrong_obj.wrong_count = 1
                            wrong_obj.memory_level = 0

                        else:
                            wrong_obj.wrong_count += 1

                        # 答錯重置記憶
                        wrong_obj.memory_level = 0

                        # 間隔學習
                        if wrong_obj.memory_level == 0:
                            delay_days = 0
                        elif wrong_obj.memory_level == 1:
                            delay_days = 1
                        elif wrong_obj.memory_level == 2:
                            delay_days = 3
                        else:
                            delay_days = 7

                        wrong_obj.next_review = (
                            timezone.now() +
                            timedelta(days=delay_days)
                        )

                        wrong_obj.user_answer = final_user_display
                        wrong_obj.save()

                    # ⭐ 不管有沒有登入都顯示錯題分析
                    wrong_details.append({
                        'question': question,
                        'user_ans': final_user_display,
                        'correct_ans': final_correct_display,
                    })
                    
            except Question.DoesNotExist:
                continue

        # 計算百分制分數
        final_score = int((score / total) * 100) if total > 0 else 0
        context = {
            'score': final_score,
            'total': total,
            'correct_count': score,
            'wrong_count': total - score,
            'wrong_details': wrong_details
        }
        from .models import QuizRecord
        if request.user.is_authenticated:
          QuizRecord.objects.create(
            user=request.user,
            score=final_score,
            total=total,
            correct=score
        )
        return render(request, 'quiz/result.html', context)           
    return redirect('home')

# 個人錯題本複習檢視
def review_wrong_questions(request):
    if not request.user.is_authenticated:
        return render(request, 'quiz/home.html', {
            'message': '請先登入才能使用錯題複習'
        })

    from django.utils import timezone

    wrong_list = WrongQuestion.objects.filter(
        user=request.user,
        next_review__lte=timezone.now()   # ⭐ 只顯示「該複習的」
    ).select_related('question').order_by('memory_level', '-wrong_count')

    chosen_questions = [wq.question for wq in wrong_list]
    if not chosen_questions:
        return render(
        request,
            'quiz/home.html',
            {
                'message': '🎉 今天沒有需要複習的錯題！'
            }
        )

    # ⭐ 間隔學習：隨機抽題（避免死背）
    random.shuffle(chosen_questions)

    # ⭐ 你已經有這行，保留
    prepare_shuffled_options(chosen_questions)

    request.session['quiz_question_ids'] = [q.id for q in chosen_questions]

    return render(request, 'quiz/quiz.html', {
        'quiz_data': chosen_questions,
        'is_review': True,
        'question_count': len(chosen_questions)
    })

from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm # Django 內建的註冊表單
from django.contrib.auth.decorators import login_required
from .models import WrongQuestion, Question

# ① 註冊帳號邏輯
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save() # 自動幫密碼加密並存入資料庫
           
            return redirect('/login/') # 註冊成功後跳轉到登入頁
    else:
        form = UserCreationForm()
    return render(request, 'quiz/register.html', {'form': form})

# ② 錯題本檢視邏輯（限定必須登入才能看）
@login_required
def wrong_questions_view(request):
    # 只撈出目前登入的這個學生的錯題紀錄
    user_wrong = WrongQuestion.objects.filter(user=request.user).select_related('question')
    return render(request, 'quiz/wrong_questions.html', {'user_wrong': user_wrong})

# 🎯 請將 quiz/views.py 最底下的 logout_view 精準修改成這樣：
def logout_view(request):
    if request.method == 'POST':
        auth.logout(request)
        # 🎯 改用這行：直接交給 settings.py 設定好的全域路由，最安全！
        return redirect(settings.LOGOUT_REDIRECT_URL) 
        
    return redirect('/')

def history_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    records = QuizRecord.objects.filter(
        user=request.user
    ).order_by('-created_at')

    labels = [r.created_at.strftime("%m/%d") for r in records]
    scores = [r.score for r in records]
    
    return render(request, 'quiz/history.html', {
        "records": records,
        "labels": labels,
        "scores": scores
    })

def leaderboard_view(request):

    leaderboard = User.objects.annotate(
    avg_score=Avg('quizrecord__score'),
    total_quizzes=Count('quizrecord')
    ).filter(
        total_quizzes__gte=3
    ).order_by(
        '-avg_score',
        '-total_quizzes'
    )[:10]

    return render(request,'quiz/leaderboard.html', {'leaderboard': leaderboard})

def daily_checkin(request):

    if not request.user.is_authenticated:
        return redirect('login')

    today = date.today()

    checkin, created = DailyCheckIn.objects.get_or_create(
        user=request.user
    )

    # ======================
    # 已簽到
    # ======================
    if checkin.last_checkin == today:
        return redirect('home')

    # ======================
    # 昨天有簽 → streak +1
    # ======================
    elif (
        checkin.last_checkin and
        checkin.last_checkin == today - timedelta(days=1)
    ):
        checkin.streak_days += 1

    # ======================
    # 中斷 → 重置
    # ======================
    else:
        checkin.streak_days = 1

    # 更新日期
    checkin.last_checkin = today

    # 積分
    checkin.total_points += 10

    checkin.save()

    return redirect('home')
