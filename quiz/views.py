from django.contrib import auth
from django.conf import settings
from django.shortcuts import render, redirect
from .models import Question, WrongQuestion
import random
import django.contrib.auth as auth  # 🎯【核心修正】改用這個，絕對 100% 抓得到登出工具！

# 首頁
def home(request):
    return render(request, 'quiz/home.html')

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
    num_questions = int(request.GET.get('num', 5)) # 接收前端選的 5 或 10 題
    
    all_questions = list(Question.objects.all())
    chosen_questions = []

    # 💡 實現間隔學習法：如果學生有登入，先撈出他寫錯過的題目
    if request.user.is_authenticated:
        wrong_records = WrongQuestion.objects.filter(user=request.user)
        wrong_questions = [wq.question for wq in wrong_records]
        
        # 如果有錯題，優先放進考卷裡（最多不超過學生選的總題數）
        if wrong_questions:
            # 隨機挑選錯題混入
            chosen_questions = random.sample(wrong_questions, min(len(wrong_questions), num_questions))

    # 💡 如果錯題不夠（或是沒登入），再從總題庫拿新題目來補滿
    remaining_slots = num_questions - len(chosen_questions)
    if remaining_slots > 0:
        # 排除已經被選中的錯題，避免重複出現
        pool = [q for q in all_questions if q not in chosen_questions]
        if pool:
            new_picks = random.sample(pool, min(len(pool), remaining_slots))
            chosen_questions.extend(new_picks)

    # 💥 最後把整份考卷的題目順序再次打亂
    random.shuffle(chosen_questions)

    # 呼叫我們上一輪寫好的「只洗牌選項、不洗牌字母」的小工具
    prepare_shuffled_options(chosen_questions)

    # 暫存到 Session
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
                else:
                    # 答錯了！存入或更新錯題本資料庫
                    if request.user.is_authenticated:
                        WrongQuestion.objects.update_or_create(
                            user=request.user,
                            question=question,
                            defaults={
                                # 🎯 這裡直接存入極度漂亮的格式，如：(C) 求多項式的根
                                'user_answer': final_user_display, 
                                'created_at': timezone.now()
                            }
                        )
                    
                    # 給當下成績單 result.html 用的資料
                    wrong_details.append({
                        'question': question,
                        'user_ans': final_user_display,       # 帶有括號的漂亮格式
                        'correct_ans': final_correct_display,   # 帶有括號的漂亮格式
                    })
                    
            except Question.DoesNotExist:
                continue

        context = {
            'correct_count': score,
            'total': total,
            'wrong_details': wrong_details,
        }
        return render(request, 'quiz/result.html', context)
    
        # 計算百分制分數
        final_score = int((score / total) * 100) if total > 0 else 0
        
        context = {
            'score': final_score,
            'total': total,
            'correct_count': score,
            'wrong_details': wrong_details
        }
        return render(request, 'quiz/result.html', context)
    return redirect('home')

# 個人錯題本複習檢視
def review_wrong_questions(request):
    if not request.user.is_authenticated:
        # 如果沒登入，就送回首頁並附帶提示訊息
        return render(request, 'quiz/home.html', {'message': '🔒 請先至後端登入帳號，才能啟用個人化弱點複習功能喔！'})
    
    # 撈出目前登入學生的所有錯題紀錄
    wrong_list = WrongQuestion.objects.filter(user=request.user).select_related('question')
    chosen_questions = [wq.question for wq in wrong_list]
    
    # 💡 1. 複習時，也幫錯題的選項隨機打亂！
    prepare_shuffled_options(chosen_questions)
    
    # 💡 2. 把錯題的 ID 也存進 Session，這樣複習完交卷才不會拿到 0 分
    request.session['quiz_question_ids'] = [q.id for q in chosen_questions]
    
    return render(request, 'quiz/quiz.html', {'quiz_data': chosen_questions, 'is_review': True})

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
