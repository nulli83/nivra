"""Tkinter desktop UI for Nivra (works on Windows, macOS, Linux)."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from auth import create_user, login_user
from config import APP_NAME, APP_TAGLINE, DOMAIN
from mail import get_inbox, get_mail, get_sent, send_mail
from ui_draw import rounded_photo


# Visual tokens
BG = "#f3f6f4"
SIDEBAR_BG = "#1f3d34"
SIDEBAR_FG = "#e8f0ec"
BRAND_FG = "#d8efe4"
PRIMARY = "#2f6f5e"
PRIMARY_HOVER = "#3a8571"
PRIMARY_PRESS = "#265a4c"
PRIMARY_FG = "#ffffff"
ROW_BORDER = "#e2e8e4"
WHITE = "#ffffff"
TEXT = "#1a2e28"
MUTED = "#5a6f68"
SECONDARY_BORDER = "#c5d4ce"
SECONDARY_HOVER = "#eaf1ee"
SECONDARY_PRESS = "#dce7e2"
SIDE_HOVER = "#2a4f43"
SIDE_PRESS = "#173028"
SIDE_ACTIVE = "#2a4f43"
PANEL_BORDER = "#d5e0db"


FIELD_BORDER = "#b7c7c0"
PLACEHOLDER = "#9aada5"


def _center(win: tk.Toplevel | tk.Tk, width: int, height: int) -> None:
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = max(0, (sw - width) // 2)
    y = max(0, (sh - height) // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")


def _clear(frame: tk.Widget) -> None:
    for child in frame.winfo_children():
        child.destroy()


def _field_label(parent, text: str) -> None:
    tk.Label(
        parent,
        text=text,
        font=("Segoe UI", 10, "bold"),
        bg=parent.cget("bg"),
        fg=TEXT,
        anchor="w",
    ).pack(fill=tk.X, pady=(0, 6))


class RoundedField(tk.Frame):
    """Rounded text field with focus ring (Pillow antialiased chrome)."""

    def __init__(
        self,
        master,
        *,
        show: str = "",
        placeholder: str = "",
        height: int = 44,
        radius: int = 12,
        font: tuple = ("Segoe UI", 11),
        **kwargs,
    ) -> None:
        try:
            parent_bg = master.cget("bg")
        except tk.TclError:
            parent_bg = BG

        super().__init__(master, bg=parent_bg, height=height, **kwargs)
        self.pack_propagate(False)
        self._parent_bg = parent_bg
        self._radius = radius
        self._show = show
        self._placeholder = placeholder
        self._showing_placeholder = bool(placeholder)
        self._outline = FIELD_BORDER
        self._photo: tk.PhotoImage | None = None
        self._last_key: tuple | None = None

        self._bg_label = tk.Label(self, bg=parent_bg, bd=0, highlightthickness=0)
        self._bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.entry = tk.Entry(
            self,
            font=font,
            bd=0,
            highlightthickness=0,
            relief=tk.FLAT,
            bg=WHITE,
            fg=PLACEHOLDER if placeholder else TEXT,
            insertbackground=TEXT,
            show="" if placeholder else show,
        )
        self.entry.place(x=14, rely=0.5, anchor="w")

        self.bind("<Configure>", self._redraw)
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self._bg_label.bind("<Button-1>", lambda _e: self.focus_set())

        if placeholder:
            self.entry.insert(0, placeholder)

    def _redraw(self, _event=None) -> None:
        w = max(self.winfo_width(), 2)
        h = max(self.winfo_height(), 2)
        if w < 4 or h < 4:
            return
        key = (w, h, self._outline)
        if key == self._last_key:
            return
        self._last_key = key
        self._photo = rounded_photo(
            self,
            w,
            h,
            self._radius,
            WHITE,
            self._outline,
            self._parent_bg,
            outline_width=1,
        )
        self._bg_label.configure(image=self._photo)
        self.entry.place_configure(x=14, rely=0.5, anchor="w", width=max(w - 28, 40))

    def _on_focus_in(self, _event=None) -> None:
        if self._showing_placeholder:
            self.entry.delete(0, tk.END)
            self.entry.configure(fg=TEXT, show=self._show)
            self._showing_placeholder = False

    def _on_focus_out(self, _event=None) -> None:
        if self._placeholder and not self.entry.get():
            self._showing_placeholder = True
            self.entry.configure(fg=PLACEHOLDER, show="")
            self.entry.insert(0, self._placeholder)

    def get(self) -> str:
        if self._showing_placeholder:
            return ""
        return self.entry.get()

    def delete(self, first, last=None) -> None:
        self.entry.delete(first, last)
        if self._placeholder and self.focus_get() != self.entry:
            self._showing_placeholder = True
            self.entry.configure(fg=PLACEHOLDER, show="")
            self.entry.delete(0, tk.END)
            self.entry.insert(0, self._placeholder)

    def insert(self, index, text: str) -> None:
        if self._showing_placeholder:
            self.entry.delete(0, tk.END)
            self.entry.configure(fg=TEXT, show=self._show)
            self._showing_placeholder = False
        self.entry.insert(index, text)

    def focus_set(self) -> None:
        self.entry.focus_set()

    def bind(self, sequence=None, func=None, add=None):
        return self.entry.bind(sequence, func, add)


class RoundedButton(tk.Frame):
    """Antialiased rounded button with hover/press states."""

    def __init__(
        self,
        master,
        text: str,
        command=None,
        *,
        variant: str = "primary",
        font: tuple = ("Segoe UI", 11),
        height: int = 42,
        radius: int = 10,
        anchor: str = "center",
        padx: int = 18,
        **kwargs,
    ) -> None:
        parent_bg = kwargs.pop("bg", None)
        if parent_bg is None:
            try:
                parent_bg = master.cget("bg")
            except tk.TclError:
                parent_bg = BG

        styles = {
            "primary": {
                "fg": PRIMARY_FG,
                "bg": PRIMARY,
                "hover": PRIMARY_HOVER,
                "press": PRIMARY_PRESS,
                "outline": PRIMARY,
            },
            "secondary": {
                "fg": PRIMARY,
                "bg": WHITE,
                "hover": SECONDARY_HOVER,
                "press": SECONDARY_PRESS,
                "outline": PRIMARY,
            },
            "ghost": {
                "fg": TEXT,
                "bg": BG,
                "hover": SECONDARY_HOVER,
                "press": SECONDARY_PRESS,
                "outline": SECONDARY_BORDER,
            },
            "sidebar": {
                "fg": SIDEBAR_FG,
                "bg": SIDEBAR_BG,
                "hover": SIDE_HOVER,
                "press": SIDE_PRESS,
                "outline": SIDEBAR_BG,
            },
            "sidebar_primary": {
                "fg": PRIMARY_FG,
                "bg": PRIMARY,
                "hover": PRIMARY_HOVER,
                "press": PRIMARY_PRESS,
                "outline": PRIMARY,
            },
        }
        style = styles.get(variant, styles["primary"])

        tw = int(master.tk.call("font", "measure", font, text))
        min_w = tw + padx * 2

        super().__init__(master, bg=parent_bg, height=height, width=min_w, **kwargs)
        self.pack_propagate(False)
        self.command = command
        self._text = text
        self._font = font
        self._radius = radius
        self._anchor = tk.W if anchor == "w" else tk.CENTER
        self._padx = padx
        self._parent_bg = parent_bg
        self._colors = dict(style)
        self._fill = style["bg"]
        self._pressed = False
        self._photo: tk.PhotoImage | None = None
        self._last_key: tuple | None = None

        self._label = tk.Label(
            self,
            text=text,
            font=font,
            fg=style["fg"],
            bg=parent_bg,
            cursor="hand2",
            bd=0,
            highlightthickness=0,
            compound="center",
            padx=padx if anchor == "w" else 0,
            anchor=self._anchor,
        )
        self._label.pack(fill=tk.BOTH, expand=True)

        for widget in (self, self._label):
            widget.bind("<Configure>", self._redraw)
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
            widget.bind("<ButtonPress-1>", self._on_press)
            widget.bind("<ButtonRelease-1>", self._on_release)

    def _redraw(self, _event=None) -> None:
        w = max(self.winfo_width(), 2)
        h = max(self.winfo_height(), 2)
        if w < 4 or h < 4:
            return
        key = (w, h, self._fill, self._colors["outline"])
        if key == self._last_key:
            return
        self._last_key = key
        self._photo = rounded_photo(
            self,
            w,
            h,
            self._radius,
            self._fill,
            self._colors["outline"],
            self._parent_bg,
            outline_width=1,
        )
        # Keep a strong reference — Tk drops PhotoImage without one.
        self._label.image = self._photo
        self._label.configure(
            image=self._photo,
            text=self._text,
            fg=self._colors["fg"],
            font=self._font,
            compound="center",
            anchor=self._anchor,
        )

    def _set_fill(self, color: str) -> None:
        self._fill = color
        self._last_key = None
        self._redraw()

    def _on_enter(self, _event=None) -> None:
        if not self._pressed:
            self._set_fill(self._colors["hover"])

    def _on_leave(self, _event=None) -> None:
        self._pressed = False
        self._set_fill(self._colors["bg"])

    def _on_press(self, _event=None) -> None:
        self._pressed = True
        self._set_fill(self._colors["press"])

    def _on_release(self, event=None) -> None:
        was_pressed = self._pressed
        self._pressed = False
        x = event.x if event else 0
        y = event.y if event else 0
        # Coordinates are relative to the widget that received the event
        widget = event.widget if event else self
        inside = 0 <= x <= widget.winfo_width() and 0 <= y <= widget.winfo_height()
        self._set_fill(self._colors["hover"] if inside else self._colors["bg"])
        if was_pressed and inside and self.command:
            self.command()


def _brand_mark(parent, size: int = 48) -> tk.Label:
    photo = rounded_photo(
        parent, size, size, 14, PRIMARY, PRIMARY, parent.cget("bg"), outline_width=1
    )
    label = tk.Label(
        parent,
        text="N",
        image=photo,
        compound="center",
        fg=WHITE,
        font=("Segoe UI", 18, "bold"),
        bg=parent.cget("bg"),
        bd=0,
        highlightthickness=0,
    )
    label.image = photo
    return label


def _domain_chip(parent) -> tk.Label:
    text = f"@{DOMAIN}"
    font = ("Segoe UI", 9)
    tw = int(parent.tk.call("font", "measure", font, text))
    w, h = tw + 24, 28
    photo = rounded_photo(
        parent, w, h, 10, SECONDARY_HOVER, SECONDARY_BORDER, parent.cget("bg")
    )
    label = tk.Label(
        parent,
        text=text,
        image=photo,
        compound="center",
        fg=MUTED,
        font=font,
        bg=parent.cget("bg"),
        bd=0,
        highlightthickness=0,
    )
    label.image = photo
    return label


class LoginWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.configure(bg=BG)
        self.mail_window: MailWindow | None = None
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.minsize(400, 620)
        _center(self, 440, 640)
        self._build()

    def _build(self) -> None:
        outer = tk.Frame(self, bg=BG, padx=60, pady=28)
        outer.pack(fill=tk.BOTH, expand=True)

        form = tk.Frame(outer, bg=BG)
        form.pack(expand=True)

        _brand_mark(form).pack()

        tk.Label(
            form,
            text=APP_NAME,
            font=("Segoe UI", 28, "bold"),
            bg=BG,
            fg=TEXT,
        ).pack(pady=(14, 0))
        tk.Label(
            form,
            text=APP_TAGLINE,
            font=("Segoe UI", 11),
            bg=BG,
            fg=MUTED,
        ).pack(pady=(4, 8))

        _domain_chip(form).pack(pady=(0, 22))

        fields = tk.Frame(form, bg=BG)
        fields.pack()

        _field_label(fields, "Användarnamn")
        self.username_entry = RoundedField(
            fields, placeholder="t.ex. alice", height=44, radius=12
        )
        self.username_entry.configure(width=320)
        self.username_entry.pack(fill=tk.X, pady=(0, 16))

        _field_label(fields, "Lösenord")
        self.password_entry = RoundedField(
            fields, show="•", height=44, radius=12
        )
        self.password_entry.configure(width=320)
        self.password_entry.pack(fill=tk.X)
        self.username_entry.bind("<Return>", lambda _e: self.password_entry.focus_set())
        self.password_entry.bind("<Return>", lambda _e: self.do_login())

        RoundedButton(
            fields,
            text="Logga in",
            command=self.do_login,
            variant="primary",
            font=("Segoe UI", 11, "bold"),
            height=46,
            radius=12,
        ).pack(fill=tk.X, pady=(26, 16))

        register = tk.Label(
            fields,
            text="Skapa konto",
            font=("Segoe UI", 11, "bold"),
            fg=PRIMARY,
            bg=BG,
            cursor="hand2",
        )
        register.pack()
        register.bind("<Button-1>", lambda _e: self.show_register())
        register.bind("<Enter>", lambda _e: register.configure(fg=PRIMARY_HOVER))
        register.bind("<Leave>", lambda _e: register.configure(fg=PRIMARY))
        self.register_link = register

        self.username_entry.focus_set()

    def do_login(self) -> None:
        username = self.username_entry.get().strip().lower()
        password = self.password_entry.get()

        if not username:
            messagebox.showerror(APP_NAME, "Skriv ett användarnamn.", parent=self)
            return
        if not password:
            messagebox.showerror(APP_NAME, "Skriv ett lösenord.", parent=self)
            return

        if login_user(username, password):
            self.withdraw()
            self.mail_window = MailWindow(self, username)
        else:
            messagebox.showerror(
                APP_NAME, "Fel användarnamn eller lösenord.", parent=self
            )

    def show_register(self) -> None:
        dialog = RegisterDialog(self)
        self.wait_window(dialog)
        if dialog.result is None:
            return
        username, password = dialog.result
        success, message = create_user(username, password)
        if success:
            self.username_entry.delete(0, tk.END)
            self.username_entry.insert(0, username)
            self.password_entry.delete(0, tk.END)
            messagebox.showinfo(
                APP_NAME, f"Kontot {username}@{DOMAIN} skapades.", parent=self
            )
        else:
            messagebox.showerror(APP_NAME, message, parent=self)


class RegisterDialog(tk.Toplevel):
    def __init__(self, parent: LoginWindow) -> None:
        super().__init__(parent)
        self.title("Skapa konto")
        self.configure(bg=BG)
        self.result: tuple[str, str] | None = None
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        box = tk.Frame(self, bg=BG, padx=28, pady=28)
        box.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            box,
            text=f"Skapa {APP_NAME}-konto",
            font=("Segoe UI", 16, "bold"),
            bg=BG,
            fg=TEXT,
        ).pack(anchor="w", pady=(0, 6))
        tk.Label(
            box,
            text=f"Adressen blir användarnamn@{DOMAIN}",
            font=("Segoe UI", 9),
            bg=BG,
            fg=MUTED,
            anchor="w",
        ).pack(fill=tk.X, pady=(0, 20))

        _field_label(box, "Användarnamn")
        self.username_entry = RoundedField(
            box, placeholder="t.ex. alice", height=44, radius=12
        )
        self.username_entry.pack(fill=tk.X, pady=(0, 14))

        _field_label(box, "Lösenord")
        self.password_entry = RoundedField(
            box, show="•", placeholder="Minst 4 tecken", height=44, radius=12
        )
        self.password_entry.pack(fill=tk.X, pady=(0, 28))
        self.username_entry.bind("<Return>", lambda _e: self.password_entry.focus_set())
        self.password_entry.bind("<Return>", lambda _e: self._ok())

        buttons = tk.Frame(box, bg=BG, height=42)
        buttons.pack(fill=tk.X)
        buttons.pack_propagate(False)

        RoundedButton(
            buttons,
            text="Avbryt",
            command=self.destroy,
            variant="secondary",
            font=("Segoe UI", 10),
            height=42,
            radius=10,
            padx=16,
        ).pack(side=tk.RIGHT)

        RoundedButton(
            buttons,
            text="Skapa konto",
            command=self._ok,
            variant="primary",
            font=("Segoe UI", 10, "bold"),
            height=42,
            radius=10,
            padx=16,
        ).pack(side=tk.RIGHT, padx=(0, 8))

        self.update_idletasks()
        width = max(420, self.winfo_reqwidth())
        height = max(460, self.winfo_reqheight() + 24)
        _center(self, width, height)
        self.after_idle(self.username_entry.focus_set)
    def _ok(self) -> None:
        username = self.username_entry.get().strip().lower()
        password = self.password_entry.get()
        self.result = (username, password)
        self.destroy()


class MailWindow(tk.Toplevel):
    def __init__(self, login_window: LoginWindow, username: str) -> None:
        super().__init__(login_window)
        self.login_window = login_window
        self.username = username
        self.current_folder = "inbox"
        self.title(f"{APP_NAME} — {username}@{DOMAIN}")
        self.configure(bg=BG)
        self.protocol("WM_DELETE_WINDOW", self._quit_app)
        _center(self, 1100, 700)
        self._build()
        self.show_folder("inbox")

    def _quit_app(self) -> None:
        self.login_window.destroy()

    def _build(self) -> None:
        main = tk.Frame(self, bg=BG)
        main.pack(fill=tk.BOTH, expand=True)

        sidebar = tk.Frame(main, bg=SIDEBAR_BG, width=240)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        side_inner = tk.Frame(sidebar, bg=SIDEBAR_BG, padx=15, pady=25)
        side_inner.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            side_inner,
            text=APP_NAME,
            font=("Segoe UI", 20, "bold"),
            bg=SIDEBAR_BG,
            fg=BRAND_FG,
            anchor="w",
        ).pack(fill=tk.X)
        tk.Label(
            side_inner,
            text=f"{self.username}@{DOMAIN}",
            font=("Segoe UI", 9),
            bg=SIDEBAR_BG,
            fg=SIDEBAR_FG,
            anchor="w",
        ).pack(fill=tk.X, pady=(0, 18))

        tk.Frame(side_inner, bg="#2d5246", height=1).pack(fill=tk.X, pady=(0, 16))

        RoundedButton(
            side_inner,
            text="Skriv mail",
            command=self.compose,
            variant="sidebar_primary",
            font=("Segoe UI", 10, "bold"),
            height=40,
            radius=10,
            anchor="w",
            padx=14,
        ).pack(fill=tk.X, pady=(0, 10))

        self._nav_btns: dict[str, RoundedButton] = {}
        for key, label in (("inbox", "Inkorg"), ("sent", "Skickat")):
            btn = RoundedButton(
                side_inner,
                text=label,
                command=lambda k=key: self.show_folder(k),
                variant="sidebar",
                font=("Segoe UI", 10),
                height=40,
                radius=10,
                anchor="w",
                padx=14,
            )
            btn.pack(fill=tk.X, pady=3)
            self._nav_btns[key] = btn

        RoundedButton(
            side_inner,
            text="Logga ut",
            command=self.logout,
            variant="sidebar",
            font=("Segoe UI", 10),
            height=40,
            radius=10,
            anchor="w",
            padx=14,
        ).pack(side=tk.BOTTOM, fill=tk.X)

        self.content = tk.Frame(main, bg=BG, padx=24, pady=24)
        self.content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _set_active_nav(self, folder: str) -> None:
        for key, btn in self._nav_btns.items():
            fill = SIDE_ACTIVE if key == folder else SIDEBAR_BG
            btn._colors = {
                "fg": SIDEBAR_FG,
                "bg": fill,
                "hover": SIDE_HOVER,
                "press": SIDE_PRESS,
                "outline": fill,
            }
            btn._fill = fill
            btn._last_key = None
            btn._redraw()

    def show_folder(self, folder: str = "inbox") -> None:
        self.current_folder = folder
        self._set_active_nav(folder)
        _clear(self.content)

        titles = {"inbox": "Inkorg", "sent": "Skickat"}
        empty_hints = {
            "inbox": "När någon skickar mail hit dyker de upp här.",
            "sent": "Mail du skickar sparas under Skickat.",
        }
        header = tk.Frame(self.content, bg=BG)
        header.pack(fill=tk.X, pady=(0, 16))

        tk.Label(
            header,
            text=titles.get(folder, folder.title()),
            font=("Segoe UI", 22, "bold"),
            bg=BG,
            fg=TEXT,
            anchor="w",
        ).pack(side=tk.LEFT)

        RoundedButton(
            header,
            text="Uppdatera",
            command=lambda: self.show_folder(folder),
            variant="secondary",
            font=("Segoe UI", 10),
            height=34,
            radius=9,
            padx=14,
        ).pack(side=tk.RIGHT)

        panel = tk.Frame(
            self.content,
            bg=WHITE,
            highlightbackground=PANEL_BORDER,
            highlightthickness=1,
            bd=0,
        )
        panel.pack(fill=tk.BOTH, expand=True)

        mails = get_sent(self.username) if folder == "sent" else get_inbox(self.username)

        if not mails:
            empty = tk.Frame(panel, bg=WHITE)
            empty.place(relx=0.5, rely=0.45, anchor="center")
            tk.Label(
                empty,
                text="Inga meddelanden här ännu",
                font=("Segoe UI", 14),
                bg=WHITE,
                fg=TEXT,
            ).pack()
            tk.Label(
                empty,
                text=empty_hints.get(folder, ""),
                font=("Segoe UI", 11),
                bg=WHITE,
                fg=MUTED,
            ).pack(pady=(6, 0))
            return

        canvas = tk.Canvas(panel, bg=WHITE, highlightthickness=0)
        scrollbar = ttk.Scrollbar(panel, orient=tk.VERTICAL, command=canvas.yview)
        list_frame = tk.Frame(canvas, bg=WHITE)

        list_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        window_id = canvas.create_window((0, 0), window=list_frame, anchor="nw")

        def _sync_width(event: tk.Event) -> None:
            canvas.itemconfigure(window_id, width=event.width)

        canvas.bind("<Configure>", _sync_width)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def _on_mousewheel(event: tk.Event) -> None:
            if getattr(event, "delta", 0):
                canvas.yview_scroll(int(-event.delta / 120), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        for mail in mails:
            peer = mail["recipient"] if folder == "sent" else mail["sender"]
            unread = folder != "sent" and not bool(mail["is_read"])
            weight = "bold" if unread else "normal"

            row = tk.Frame(list_frame, bg=WHITE, cursor="hand2")
            row.pack(fill=tk.X)
            tk.Frame(list_frame, bg=ROW_BORDER, height=1).pack(fill=tk.X)

            inner = tk.Frame(row, bg=WHITE, padx=18, pady=14)
            inner.pack(fill=tk.X)

            tk.Label(
                inner,
                text=peer,
                font=("Segoe UI", 10, weight),
                bg=WHITE,
                fg=TEXT,
                width=28,
                anchor="w",
            ).pack(side=tk.LEFT)
            tk.Label(
                inner,
                text=mail["subject"] or "(inget ämne)",
                font=("Segoe UI", 10, weight),
                bg=WHITE,
                fg=TEXT,
                anchor="w",
            ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
            tk.Label(
                inner,
                text=mail["created_at"],
                font=("Segoe UI", 9),
                bg=WHITE,
                fg=MUTED,
                anchor="e",
            ).pack(side=tk.RIGHT)

            mail_id = mail["id"]

            def open_this(_event=None, mid=mail_id, f=folder) -> None:
                self.open_mail(mid, f)

            for widget in (row, inner, *inner.winfo_children()):
                widget.bind("<Button-1>", open_this)

    def open_mail(self, mail_id: int, folder: str) -> None:
        mail = get_mail(mail_id, self.username, folder)
        if not mail:
            return

        _clear(self.content)

        back_label = (
            "Tillbaka till skickat" if folder == "sent" else "Tillbaka till inkorg"
        )
        RoundedButton(
            self.content,
            text=back_label,
            command=lambda: self.show_folder(folder),
            variant="ghost",
            font=("Segoe UI", 10),
            height=34,
            radius=9,
            padx=14,
        ).pack(anchor="w")

        tk.Label(
            self.content,
            text=mail["subject"],
            font=("Segoe UI", 20, "bold"),
            bg=BG,
            fg=TEXT,
            anchor="w",
            wraplength=800,
            justify=tk.LEFT,
        ).pack(fill=tk.X, pady=(15, 8))

        for line in (
            f"Från: {mail['sender']}",
            f"Till: {mail['recipient']}",
            mail["created_at"],
        ):
            tk.Label(
                self.content,
                text=line,
                font=("Segoe UI", 10),
                bg=BG,
                fg=MUTED,
                anchor="w",
            ).pack(fill=tk.X)

        ttk.Separator(self.content, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=16)

        body_frame = tk.Frame(self.content, bg=WHITE)
        body_frame.pack(fill=tk.BOTH, expand=True)

        body = tk.Text(
            body_frame,
            font=("Segoe UI", 11),
            wrap=tk.WORD,
            bg=WHITE,
            fg=TEXT,
            relief=tk.FLAT,
            padx=12,
            pady=12,
        )
        body.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(body_frame, command=body.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        body.configure(yscrollcommand=scroll.set)
        body.insert("1.0", mail["body"] or "")
        body.configure(state=tk.DISABLED)

    def compose(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Nytt meddelande")
        dialog.configure(bg=BG)
        dialog.transient(self)
        dialog.grab_set()
        _center(dialog, 650, 600)

        box = tk.Frame(dialog, bg=BG, padx=20, pady=20)
        box.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            box, text="Till", font=("Segoe UI", 11, "bold"), bg=BG, fg=TEXT, anchor="w"
        ).pack(fill=tk.X)
        recipient = tk.Entry(box, font=("Segoe UI", 11))
        recipient.pack(fill=tk.X, pady=(2, 4), ipady=4)
        tk.Label(
            box,
            text=f"t.ex. bob@{DOMAIN}",
            font=("Segoe UI", 9),
            bg=BG,
            fg=MUTED,
            anchor="w",
        ).pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            box, text="Ämne", font=("Segoe UI", 11, "bold"), bg=BG, fg=TEXT, anchor="w"
        ).pack(fill=tk.X)
        subject = tk.Entry(box, font=("Segoe UI", 11))
        subject.pack(fill=tk.X, pady=(2, 10), ipady=4)

        tk.Label(
            box,
            text="Meddelande",
            font=("Segoe UI", 11, "bold"),
            bg=BG,
            fg=TEXT,
            anchor="w",
        ).pack(fill=tk.X)
        body = tk.Text(box, font=("Segoe UI", 11), wrap=tk.WORD, height=16)
        body.pack(fill=tk.BOTH, expand=True, pady=(2, 12))

        buttons = tk.Frame(box, bg=BG)
        buttons.pack(fill=tk.X)

        def do_send() -> None:
            to = recipient.get().strip()
            subj = subject.get().strip()
            text = body.get("1.0", tk.END).rstrip("\n")
            if not to:
                messagebox.showerror(APP_NAME, "Ange en mottagare.", parent=dialog)
                return
            success, message = send_mail(self.username, to, subj, text)
            if success:
                messagebox.showinfo(APP_NAME, "Meddelandet skickades.", parent=dialog)
                dialog.destroy()
                if self.current_folder == "sent":
                    self.show_folder("sent")
            else:
                messagebox.showerror(APP_NAME, message, parent=dialog)

        RoundedButton(
            buttons,
            text="Avbryt",
            command=dialog.destroy,
            variant="ghost",
            font=("Segoe UI", 10),
            height=36,
            radius=9,
            padx=16,
        ).pack(side=tk.RIGHT)
        RoundedButton(
            buttons,
            text="Skicka",
            command=do_send,
            variant="primary",
            font=("Segoe UI", 10, "bold"),
            height=36,
            radius=9,
            padx=16,
        ).pack(side=tk.RIGHT, padx=(0, 8))

        recipient.focus_set()

    def logout(self) -> None:
        self.destroy()
        self.login_window.username_entry.delete(0, tk.END)
        self.login_window.password_entry.delete(0, tk.END)
        self.login_window.deiconify()
        self.login_window.username_entry.focus_set()
