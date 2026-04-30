"""
冒险岛翻译小工具 - 中英文互译
"""
import tkinter as tk
from tkinter import ttk, messagebox
import urllib.request
import urllib.parse
import json
import threading
import re

APP_TITLE = "冒险岛翻译小工具"


def has_chinese(text):
    return bool(re.search(r'[一-鿿]', text))


def translate_google(text, source, target):
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        'client': 'gtx',
        'sl': source,
        'tl': target,
        'dt': 't',
        'q': text,
    }
    full_url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(full_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=8) as r:
        data = json.loads(r.read().decode('utf-8'))
    return ''.join(seg[0] for seg in data[0] if seg[0])


def translate_mymemory(text, source, target):
    lang_map = {'zh-CN': 'zh-CN', 'en': 'en'}
    sl = lang_map.get(source, source)
    tl = lang_map.get(target, target)
    url = "https://api.mymemory.translated.net/get"
    params = {'q': text, 'langpair': f"{sl}|{tl}"}
    full_url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(full_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=8) as r:
        data = json.loads(r.read().decode('utf-8'))
    return data['responseData']['translatedText']


def translate(text):
    text = text.strip()
    if not text:
        return ""
    if has_chinese(text):
        sl, tl = 'zh-CN', 'en'
    else:
        sl, tl = 'en', 'zh-CN'

    errors = []
    for fn, name in [(translate_google, 'Google'), (translate_mymemory, 'MyMemory')]:
        try:
            result = fn(text, sl, tl)
            if result:
                return result
        except Exception as e:
            errors.append(f"{name}: {e}")
    raise RuntimeError("翻译失败，请检查网络：\n" + "\n".join(errors))


class App:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("560x460")
        self.root.minsize(420, 360)
        self.always_on_top = tk.BooleanVar(value=True)
        self.root.attributes('-topmost', True)
        self._build_ui()

    def _build_ui(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill='x', padx=8, pady=(8, 4))
        ttk.Checkbutton(
            toolbar, text="窗口置顶（游戏内不被遮挡）",
            variable=self.always_on_top,
            command=self._toggle_topmost
        ).pack(side='left')
        ttk.Button(toolbar, text="清空", command=self._clear, width=8).pack(side='right')

        ttk.Label(self.root, text="输入（中文 或 English）：").pack(anchor='w', padx=8)
        self.input = tk.Text(self.root, height=6, wrap='word', font=('Microsoft YaHei', 11))
        self.input.pack(fill='both', expand=True, padx=8, pady=4)
        self.input.bind('<Control-Return>', lambda e: (self._do_translate(), 'break'))
        self.input.focus_set()

        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill='x', padx=8, pady=4)
        self.translate_btn = ttk.Button(
            btn_frame, text="翻译 (Ctrl+Enter)", command=self._do_translate
        )
        self.translate_btn.pack(side='left')
        ttk.Button(btn_frame, text="复制结果", command=self._copy_result).pack(side='left', padx=4)
        ttk.Button(btn_frame, text="复制并粘到游戏 ↑", command=self._copy_to_clipboard_only).pack(side='left')
        self.status = ttk.Label(btn_frame, text="就绪", foreground='gray')
        self.status.pack(side='right')

        ttk.Label(self.root, text="结果：").pack(anchor='w', padx=8)
        self.output = tk.Text(self.root, height=6, wrap='word', font=('Microsoft YaHei', 11))
        self.output.pack(fill='both', expand=True, padx=8, pady=(4, 8))

    def _toggle_topmost(self):
        self.root.attributes('-topmost', self.always_on_top.get())

    def _clear(self):
        self.input.delete('1.0', 'end')
        self.output.delete('1.0', 'end')
        self.status.config(text="就绪", foreground='gray')
        self.input.focus_set()

    def _do_translate(self):
        text = self.input.get('1.0', 'end').strip()
        if not text:
            return
        self.status.config(text="翻译中...", foreground='orange')
        self.translate_btn.config(state='disabled')
        threading.Thread(target=self._worker, args=(text,), daemon=True).start()

    def _worker(self, text):
        try:
            result = translate(text)
            self.root.after(0, self._on_success, result)
        except Exception as e:
            self.root.after(0, self._on_error, str(e))

    def _on_success(self, result):
        self.output.delete('1.0', 'end')
        self.output.insert('1.0', result)
        self.status.config(text="完成", foreground='green')
        self.translate_btn.config(state='normal')

    def _on_error(self, msg):
        self.status.config(text="失败", foreground='red')
        self.translate_btn.config(state='normal')
        messagebox.showerror("翻译失败", msg)

    def _copy_result(self):
        text = self.output.get('1.0', 'end').strip()
        if not text:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status.config(text="结果已复制", foreground='blue')

    def _copy_to_clipboard_only(self):
        text = self.output.get('1.0', 'end').strip()
        if not text:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status.config(text="已复制，游戏里 Ctrl+V 粘贴", foreground='blue')


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
