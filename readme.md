Markdown
# 資料結構第 4 章－陣列測驗網站

這是一個專為資料結構「陣列」章節設計的線上測驗系統，支援後台管理、題目與選項隨機化、即時閱卷回饋，以及錯題重複出現的間隔學習法。

## 🛠️ 系統功能

* **題庫後台管理**：可透過 Django Admin 進行題目與選項的「新增、刪除、修改」。
* **隨機化機制**：測驗時隨機抽題，且每題的選項順序內容皆隨機洗牌，避免學生死背答案位置。
* **即時回饋**：學生交卷後，系統會明確顯示錯題、學生作答以及該題的正確答案。
* **測驗題數設定**：允許學生自行選擇每次測驗題數（5 題、10 題或全部）。
* **間隔學習法**：系統會優先抽取學生之前答錯的題目（錯題本），重複出現以加強記憶。

---

## 🚀 專案安裝與執行步驟

如果使用 Git指令下載，請先在終端機輸入以下指令複製儲存庫，並進入專案資料夾：

輸入指令: git clone https://github.com/CBF113045/django-ds-quiz.git


重要前提：切換至專案根目錄
請確保您的終端機（Terminal）路徑已切換至含有 manage.py 的核心專案資料夾內。若路徑不正確，請使用 cd 指令切換

cd django-ds-quiz-main

( 提示：如果是從網頁下載 ZIP 檔，請解壓縮後直接用 VS Code 的「開啟資料夾」打開該目錄即可。)

請在 VS Code 終端機中，依序執行以下步驟：

1. 安裝必要開發套件
在專案根目錄下執行，依據 requirements.txt 安裝 Django 及相關相依套件：

python -m pip install -r requirements.txt

2. 建立 Migration

若看到 models 有變更提示，請先執行：
python manage.py makemigrations

3. 執行資料庫遷移（Migration）
同步 SQLite 資料庫結構，確保題庫與資料表完整：

python manage.py migrate

4. 啟動 Django 開發伺服器
執行以下指令啟動在地端伺服器：

python manage.py runserver

#如何開啟網站
當終端機顯示 Starting development server at http://127.0.0.1:8000/ 後：

打开瀏覽器（建議使用 Chrome 或 Edge）。

在網址列輸入：http://127.0.0.1:8000/

按下 Enter 即可進入「資料結構隨機測驗網站」首頁。

💡 小提示：如需停止伺服器運作，請在終端機視窗中按下鍵盤的 Ctrl + C 即可關閉。
