from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.clock import mainthread
import subprocess
import threading

class BotUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)

        # نمایش خروجی ربات
        self.output_label = Label(text="درحال اجرای ربات...", size_hint_y=0.6)
        self.add_widget(self.output_label)

        # ورودی برای input ربات
        self.input_box = TextInput(hint_text="پیام برای ربات...", size_hint_y=None, height=50)
        self.add_widget(self.input_box)

        self.send_btn = Button(text="ارسال به ربات", size_hint_y=None, height=50)
        self.send_btn.bind(on_release=self.send_to_bot)
        self.add_widget(self.send_btn)

        # شروع ربات
        threading.Thread(target=self.run_bot, daemon=True).start()
        self.process = None

    def run_bot(self):
        # اجرای bot.py با subprocess
        self.process = subprocess.Popen(
            ["python3", "bot.py"],  # مسیر ربات اصلی
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        # خواندن خروجی ربات و نمایش روی UI
        for line in self.process.stdout:
            self.update_output(line)

    @mainthread
    def update_output(self, text):
        self.output_label.text += "\n" + text

    def send_to_bot(self, *args):
        txt = self.input_box.text.strip()
        if txt and self.process:
            self.process.stdin.write(txt + "\n")
            self.process.stdin.flush()
            self.input_box.text = ""

class MainApp(App):
    def build(self):
        # فقط UI و اجرای bot.py
        return BotUI()

if __name__ == "__main__":
    MainApp().run()

