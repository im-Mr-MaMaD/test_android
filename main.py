from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput


class Calculator(App):
    def build(self):
        main_layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        self.solution = TextInput(
            multiline=False,
            readonly=False,
            halign="right",
            font_size=55,
            size_hint=(1, 0.2)
        )
        main_layout.add_widget(self.solution)

        buttons = [
            ["C", "⌫", "%", "/"],
            ["7", "8", "9", "*"],
            ["4", "5", "6", "-"],
            ["1", "2", "3", "+"],
            ["(", "0", ")", "="],
        ]

        btn_layout = GridLayout(cols=4, spacing=10, size_hint=(1, 0.8))

        for row in buttons:
            for label in row:
                btn = Button(
                    text=label,
                    font_size=32,
                    background_color=(0.2, 0.2, 0.2, 1),
                    color=(1, 1, 1, 1),
                    on_press=self.on_button_press
                )
                btn_layout.add_widget(btn)

        main_layout.add_widget(btn_layout)
        return main_layout

    def on_button_press(self, instance):
        text = instance.text
        current = self.solution.text

        if text == "C":
            self.solution.text = ""
        elif text == "⌫":
            self.solution.text = current[:-1]
        elif text == "=":
            try:
                expression = current.replace("%", "/100")
                result = str(eval(expression))
                self.solution.text = result
            except:
                self.solution.text = "Error"
        else:
            self.solution.text += text


if __name__ == "__main__":
    Calculator().run()
