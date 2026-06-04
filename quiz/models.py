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
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="學生")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="錯題")
    user_answer = models.CharField(max_length=1, verbose_name="學生選的錯誤答案")

    def __str__(self):
        return f"{self.user.username} - {self.question.content[:20]}"
    
    from django.db import models
from django.contrib.auth.models import User # 引入 Django 內建的使用者模型

# 妳原本的 Question 類別保持不變...

class WrongQuestion(models.Model):
    # 使用外鍵 (ForeignKey) 串接使用者與題目
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="學生")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="錯題內容")
    
    user_answer = models.CharField(max_length=255, null=True, blank=True, verbose_name="學生的錯誤答案")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="記錄時間")

    class Meta:
        # 防止同一位學生重複記錄同一道錯題
        unique_together = ('user', 'question')

    def __str__(self):
      return f"{self.user.username} - {self.question.content[:20]}"
