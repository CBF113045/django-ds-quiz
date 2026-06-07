from django.db import models
from django.contrib.auth.models import User

# 1. 題目資料庫
class Question(models.Model):
    content = models.TextField(verbose_name="題目內容")
    option_a = models.CharField(max_length=255, verbose_name="選項 A")
    option_b = models.CharField(max_length=255, verbose_name="選項 B")
    option_c = models.CharField(max_length=255, verbose_name="選項 C")
    option_d = models.CharField(max_length=255, verbose_name="選項 D", blank=True, null=True)
    option_e = models.CharField(max_length=255, verbose_name="選項 E", blank=True, null=True)
    
    correct_answer = models.CharField(
        max_length=1, 
        choices=[('A','A'),('B','B'),('C','C'),('D','D'),('E','E')], 
        verbose_name="正確答案"
    )

    # 💡 修正這裡：改成只顯示題目內容前 20 個字，乾乾淨淨！
    def __str__(self):
        return self.content[:20]

# 2. 錯題本資料庫（進階加分項）
class WrongQuestion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    user_answer = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    # 🧠 AI 記憶核心欄位（新增）
    wrong_count = models.IntegerField(default=1)   # 錯幾次
    correct_count = models.IntegerField(default=0) # 答對幾次

    memory_level = models.IntegerField(default=0)   
    # 0 = 新錯題
    # 1 = 已複習過
    # 2 = 熟練
    # 3 = 幾乎記住

    next_review = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'question')

    def __str__(self):
        return f"{self.user.username} - {self.question.content[:20]}"

class QuizRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField()
    total = models.IntegerField()
    correct = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.score}"
