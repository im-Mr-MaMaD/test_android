[app]
# عنوان اپلیکیشن
title = MyRubpyBot
package.name = myrubpybot
package.domain = org.example

# نسخه اپ
version = 0.1

# پوشه سورس
source.dir = .
source.include_exts = py,png,jpg,kv,json

# کتابخانه‌های مورد نیاز
requirements = python3,kivy,rubpy,regex,jdatetime,aiohttp

# جهت نمایش صحیح UI
orientation = portrait
fullscreen = 0

# مجوزهای لازم اندروید
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK,FOREGROUND_SERVICE

# خروجی APK
android.arch = armeabi-v7a
android.api = 33
android.minapi = 21
android.sdk = 33

# کیوی
# این گزینه‌ها برای بهبود اجرای UI و جلوگیری از crash
android.entrypoint = org.kivy.android.PythonActivity
android.allow_backup = True
android.enable_androidx = True

# مسیر فایل خروجی (bin)
# بعد از buildozer android debug فایل APK در bin/ ایجاد می‌شود
