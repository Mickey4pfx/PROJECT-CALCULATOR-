import tkinter as tk

# ---------- Colors ----------
BG = "#eef1f6"
CARD = "#ffffff"
DISPLAY = "#f4f6fa"
TEXT = "#1b1f2a"
SUB = "#7a8294"
KEY, KEY_H = "#eceff5", "#e0e4ed"
OP, OP_H, OP_T = "#dfe7ff", "#cfdbff", "#2f55d4"
ACC, ACC_H = "#2f55d4", "#2748b5"
DEL, DEL_H, DEL_T = "#ffe3e3", "#ffcccc", "#d03535"

OPS = "+−×÷"


# ---------- Safe expression parser (no eval) ----------
def evaluate(s):
    pos = 0

    def peek():
        return s[pos] if pos < len(s) else ""

    def number():
        nonlocal pos
        start = pos
        while pos < len(s) and (s[pos].isdigit() or s[pos] == "."):
            pos += 1
        text = s[start:pos]
        if not text or text == ".":
            raise ValueError("Invalid")
        return float(text)

    def primary():
        nonlocal pos
        if peek() == "(":
            pos += 1
            v = addsub()
            if peek() != ")":
                raise ValueError("Missing )")
            pos += 1
            return v
        return number()

    def factor():
        nonlocal pos
        if peek() == "−":
            pos += 1
            return -factor()
        if peek() == "+":
            pos += 1
            return factor()
        v = primary()
        while peek() == "%":
            pos += 1
            v /= 100
        return v

    def muldiv():
        nonlocal pos
        v = factor()
        while peek() in ("×", "÷"):
            op = s[pos]
            pos += 1
            r = factor()
            if op == "×":
                v *= r
            else:
                if r == 0:
                    raise ValueError("Cannot divide by 0")
                v /= r
        return v

    def addsub():
        nonlocal pos
        v = muldiv()
        while peek() in ("+", "−"):
            op = s[pos]
            pos += 1
            r = muldiv()
            v = v + r if op == "+" else v - r
        return v

    result = addsub()
    if pos < len(s):
        raise ValueError("Invalid")
    return result


def fmt(n):
    n = float(f"{n:.12g}")
    if n == int(n) and abs(n) < 1e15:
        return f"{int(n):,}"
    return f"{n:,}"


def auto_close(s):
    return s + ")" * (s.count("(") - s.count(")"))


# ---------- App ----------
class Calculator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Calculator")
        self.configure(bg=BG)
        self.resizable(False, False)

        self.expr = ""
        self.just_evaluated = False

        card = tk.Frame(self, bg=CARD, padx=16, pady=16)
        card.pack(padx=20, pady=20)

        # Display
        disp = tk.Frame(card, bg=DISPLAY, padx=14, pady=10)
        disp.pack(fill="x")
        self.expr_var = tk.StringVar()
        self.res_var = tk.StringVar(value="0")
        tk.Label(disp, textvariable=self.expr_var, bg=DISPLAY, fg=SUB,
                 font=("Segoe UI", 13), anchor="e", width=22).pack(fill="x")
        self.res_label = tk.Label(disp, textvariable=self.res_var, bg=DISPLAY,
                                  fg=TEXT, font=("Segoe UI", 30, "bold"),
                                  anchor="e", width=12)
        self.res_label.pack(fill="x")

        # Keys
        keys = tk.Frame(card, bg=CARD)
        keys.pack(pady=(14, 0))

        layout = [
            ["C", "(", ")", "÷"],
            ["7", "8", "9", "×"],
            ["4", "5", "6", "−"],
            ["1", "2", "3", "+"],
            ["%", "0", ".", "⌫"],
        ]
        for r, row in enumerate(layout):
            for c, k in enumerate(row):
                self.make_button(keys, k, r, c)

        self.make_button(keys, "=", 5, 0, span=4)

        # Keyboard bindings
        self.bind("<Key>", self.on_key)
        self.bind("<Return>", lambda e: self.press("="))
        self.bind("<KP_Enter>", lambda e: self.press("="))
        self.bind("<BackSpace>", lambda e: self.press("⌫"))
        self.bind("<Escape>", lambda e: self.press("C"))

    def make_button(self, parent, key, row, col, span=1):
        if key == "=":
            bg, hover, fg = ACC, ACC_H, "#ffffff"
        elif key in ("C", "⌫"):
            bg, hover, fg = DEL, DEL_H, DEL_T
        elif key in OPS or key in "()%":
            bg, hover, fg = OP, OP_H, OP_T
        else:
            bg, hover, fg = KEY, KEY_H, TEXT

        b = tk.Button(parent, text=key, bg=bg, fg=fg, activebackground=hover,
                      activeforeground=fg, relief="flat", bd=0,
                      font=("Segoe UI", 16), width=4, height=1,
                      cursor="hand2", command=lambda: self.press(key))
        b.grid(row=row, column=col, columnspan=span, padx=5, pady=5,
               ipady=8, sticky="nsew")
        b.bind("<Enter>", lambda e: b.config(bg=hover))
        b.bind("<Leave>", lambda e: b.config(bg=bg))

    # ---------- Keyboard ----------
    def on_key(self, event):
        ch = event.char
        mapping = {"-": "−", "*": "×", "x": "×", "/": "÷", ",": "."}
        if ch.isdigit() and len(ch) == 1:
            self.press(ch)
        elif ch in mapping:
            self.press(mapping[ch])
        elif ch in "+.%()" and ch:
            self.press(ch)
        elif ch == "=":
            self.press("=")

    # ---------- Logic ----------
    def current_number(self):
        i = len(self.expr)
        while i > 0 and (self.expr[i - 1].isdigit() or self.expr[i - 1] == "."):
            i -= 1
        return self.expr[i:]

    def show(self, final=False):
        self.expr_var.set(self.expr)
        self.res_label.config(fg=TEXT, font=("Segoe UI", 30, "bold"))
        if not self.expr:
            self.res_var.set("0")
            return
        t = self.expr
        while t and t[-1] in OPS:
            t = t[:-1]
        if not t or t[-1] == "(" or not any(ch.isdigit() for ch in t):
            return
        try:
            self.res_var.set(fmt(evaluate(auto_close(t))))
        except ValueError as e:
            if final:
                self.show_error(str(e))

    def show_error(self, msg):
        self.res_var.set(msg)
        self.res_label.config(fg=DEL_T, font=("Segoe UI", 16, "bold"))

    def press(self, k):
        if k == "C":
            self.expr, self.just_evaluated = "", False
            return self.show()

        if k == "⌫":
            self.expr = "" if self.just_evaluated else self.expr[:-1]
            self.just_evaluated = False
            return self.show()

        if k == "=":
            if not self.expr:
                return
            t = self.expr
            while t and t[-1] in OPS:
                t = t[:-1]
            try:
                t = auto_close(t)
                value = evaluate(t)
                self.expr_var.set(t + " =")
                self.res_label.config(fg=TEXT, font=("Segoe UI", 30, "bold"))
                self.res_var.set(fmt(value))
                text = f"{value:.12g}".replace("-", "−")
                self.expr = "" if "e" in text else text
                self.just_evaluated = True
            except ValueError as e:
                self.show_error(str(e))
            return

        last = self.expr[-1] if self.expr else ""

        if k.isdigit():
            if self.just_evaluated:
                self.expr, self.just_evaluated = "", False
                last = ""
            if last in (")", "%"):
                self.expr += "×"
            if self.current_number() == "0":
                self.expr = self.expr[:-1]
            self.expr += k

        elif k == ".":
            if self.just_evaluated:
                self.expr, self.just_evaluated = "", False
                last = ""
            if "." in self.current_number():
                return
            if not last.isdigit():
                self.expr += "0"
            self.expr += "."

        elif k in OPS:
            self.just_evaluated = False
            if not self.expr:
                if k == "−":
                    self.expr = "−"
                return self.show()
            if last == "(":
                if k == "−":
                    self.expr += k
                return self.show()
            if last in OPS:
                self.expr = self.expr[:-1]
            if not self.expr or self.expr == "−":
                return self.show()
            self.expr += k

        elif k == "%":
            self.just_evaluated = False
            if last and (last.isdigit() or last in ")%"):
                self.expr += "%"

        elif k == "(":
            if self.just_evaluated:
                self.expr, self.just_evaluated = "", False
                last = ""
            if last and (last.isdigit() or last in ")%"):
                self.expr += "×"
            self.expr += "("

        elif k == ")":
            if (self.expr.count("(") > self.expr.count(")")
                    and last and (last.isdigit() or last in ")%")):
                self.expr += ")"

        self.show()


if __name__ == "__main__":
    Calculator().mainloop()
