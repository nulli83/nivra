"""GTK desktop UI for Nivra."""

from __future__ import annotations

import html

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gtk  # noqa: E402

from auth import create_user, login_user
from config import APP_NAME, APP_TAGLINE, DOMAIN
from mail import get_inbox, get_mail, get_sent, send_mail


def escape_markup(text: str) -> str:
    return html.escape(text or "", quote=False)


def make_label(
    text: str,
    size: int = 12,
    bold: bool = False,
    center: bool = False,
) -> Gtk.Label:
    label = Gtk.Label()
    safe = escape_markup(text)
    weight = "bold" if bold else "normal"
    label.set_markup(
        f"<span size='{size * 1000}' weight='{weight}'>{safe}</span>"
    )
    label.set_xalign(0.5 if center else 0.0)
    label.set_line_wrap(True)
    return label


def clear_container(container: Gtk.Container) -> None:
    for child in container.get_children():
        container.remove(child)


def message_dialog(parent: Gtk.Window, message: str, error: bool = False) -> None:
    dialog = Gtk.MessageDialog(
        transient_for=parent,
        flags=0,
        message_type=Gtk.MessageType.ERROR if error else Gtk.MessageType.INFO,
        buttons=Gtk.ButtonsType.OK,
        text=message,
    )
    dialog.run()
    dialog.destroy()


def apply_css() -> None:
    css = b"""
    window {
        background: #f3f6f4;
    }
    .sidebar {
        background: #1f3d34;
        color: #e8f0ec;
    }
    .sidebar label {
        color: #e8f0ec;
    }
    .brand {
        color: #d8efe4;
    }
    button {
        padding: 8px 12px;
    }
    .primary-btn {
        background: #2f6f5e;
        color: white;
        border: none;
        font-weight: bold;
    }
    list {
        background: white;
    }
    row {
        border-bottom: 1px solid #e2e8e4;
    }
    """
    provider = Gtk.CssProvider()
    provider.load_from_data(css)
    screen = Gdk.Screen.get_default()
    Gtk.StyleContext.add_provider_for_screen(
        screen,
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )


class LoginWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title=APP_NAME)
        self.set_default_size(430, 520)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect("destroy", Gtk.main_quit)
        self.mail_window = None
        self.build_ui()

    def build_ui(self) -> None:
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        outer.set_margin_top(55)
        outer.set_margin_bottom(55)
        outer.set_margin_start(55)
        outer.set_margin_end(55)
        self.add(outer)

        outer.pack_start(
            make_label(APP_NAME, 28, True, True), False, False, 0
        )
        outer.pack_start(
            make_label(APP_TAGLINE, 12, False, True), False, False, 10
        )
        outer.pack_start(
            make_label(f"@{DOMAIN}", 10, False, True), False, False, 0
        )

        outer.pack_start(make_label("Användarnamn", 11, True), False, False, 0)
        self.username_entry = Gtk.Entry()
        self.username_entry.set_placeholder_text("alice")
        self.username_entry.set_activates_default(True)
        outer.pack_start(self.username_entry, False, False, 0)

        outer.pack_start(make_label("Lösenord", 11, True), False, False, 0)
        self.password_entry = Gtk.Entry()
        self.password_entry.set_visibility(False)
        self.password_entry.set_placeholder_text("Lösenord")
        self.password_entry.set_activates_default(True)
        outer.pack_start(self.password_entry, False, False, 0)

        login_button = Gtk.Button(label="Logga in")
        login_button.get_style_context().add_class("primary-btn")
        login_button.set_can_default(True)
        self.set_default(login_button)
        login_button.connect("clicked", self.do_login)
        outer.pack_start(login_button, False, False, 15)

        register_button = Gtk.Button(label="Skapa konto")
        register_button.connect("clicked", self.show_register)
        outer.pack_start(register_button, False, False, 0)

        self.username_entry.grab_focus()

    def do_login(self, _button=None) -> None:
        username = self.username_entry.get_text().strip().lower()
        password = self.password_entry.get_text()

        if not username:
            message_dialog(self, "Skriv ett användarnamn.", True)
            return
        if not password:
            message_dialog(self, "Skriv ett lösenord.", True)
            return

        if login_user(username, password):
            self.hide()
            self.mail_window = MailWindow(username, self)
            self.mail_window.show_all()
        else:
            message_dialog(self, "Fel användarnamn eller lösenord.", True)

    def show_register(self, _button=None) -> None:
        dialog = RegisterDialog(self)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            username = dialog.username_entry.get_text().strip().lower()
            password = dialog.password_entry.get_text()
            dialog.destroy()
            success, message = create_user(username, password)
            if success:
                self.username_entry.set_text(username)
                self.password_entry.set_text("")
                message_dialog(
                    self, f"Kontot {username}@{DOMAIN} skapades."
                )
            else:
                message_dialog(self, message, True)
        else:
            dialog.destroy()


class RegisterDialog(Gtk.Dialog):
    def __init__(self, parent: Gtk.Window):
        Gtk.Dialog.__init__(
            self,
            title="Skapa konto",
            transient_for=parent,
            flags=0,
        )
        self.add_buttons(
            "Avbryt",
            Gtk.ResponseType.CANCEL,
            "Skapa konto",
            Gtk.ResponseType.OK,
        )
        self.set_default_size(380, 300)

        area = self.get_content_area()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        box.set_margin_start(20)
        box.set_margin_end(20)
        area.add(box)

        box.pack_start(
            make_label(f"Skapa {APP_NAME}-konto", 17, True), False, False, 5
        )
        box.pack_start(make_label("Användarnamn", 11, True), False, False, 0)
        self.username_entry = Gtk.Entry()
        self.username_entry.set_placeholder_text("alice")
        box.pack_start(self.username_entry, False, False, 0)

        hint = make_label(f"Adressen blir användarnamn@{DOMAIN}", 10)
        box.pack_start(hint, False, False, 0)

        box.pack_start(make_label("Lösenord", 11, True), False, False, 0)
        self.password_entry = Gtk.Entry()
        self.password_entry.set_visibility(False)
        self.password_entry.set_placeholder_text("Minst 4 tecken")
        box.pack_start(self.password_entry, False, False, 0)

        self.set_default_response(Gtk.ResponseType.OK)
        self.show_all()


class MailWindow(Gtk.Window):
    def __init__(self, username: str, login_window: LoginWindow):
        Gtk.Window.__init__(
            self, title=f"{APP_NAME} — {username}@{DOMAIN}"
        )
        self.username = username
        self.login_window = login_window
        self.current_folder = "inbox"
        self.set_default_size(1100, 700)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect("delete-event", self.on_close)
        self.build_ui()

    def build_ui(self) -> None:
        main = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(main)

        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        sidebar.get_style_context().add_class("sidebar")
        sidebar.set_size_request(240, -1)

        side_inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        side_inner.set_margin_top(25)
        side_inner.set_margin_bottom(25)
        side_inner.set_margin_start(15)
        side_inner.set_margin_end(15)
        sidebar.pack_start(side_inner, True, True, 0)
        main.pack_start(sidebar, False, False, 0)

        logo = make_label(APP_NAME, 22, True)
        logo.get_style_context().add_class("brand")
        side_inner.pack_start(logo, False, False, 0)
        side_inner.pack_start(
            make_label(f"{self.username}@{DOMAIN}", 10), False, False, 0
        )
        side_inner.pack_start(
            Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL),
            False,
            False,
            15,
        )

        compose_button = Gtk.Button(label="Skriv mail")
        compose_button.get_style_context().add_class("primary-btn")
        compose_button.connect("clicked", self.compose)
        side_inner.pack_start(compose_button, False, False, 0)

        inbox_button = Gtk.Button(label="Inkorg")
        inbox_button.connect("clicked", lambda *_: self.show_folder("inbox"))
        side_inner.pack_start(inbox_button, False, False, 0)

        sent_button = Gtk.Button(label="Skickat")
        sent_button.connect("clicked", lambda *_: self.show_folder("sent"))
        side_inner.pack_start(sent_button, False, False, 0)

        logout_button = Gtk.Button(label="Logga ut")
        logout_button.connect("clicked", self.logout)
        side_inner.pack_end(logout_button, False, False, 0)

        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.content.set_margin_top(25)
        self.content.set_margin_bottom(25)
        self.content.set_margin_start(20)
        self.content.set_margin_end(25)
        main.pack_start(self.content, True, True, 0)

        self.show_folder("inbox")

    def show_folder(self, folder: str = "inbox", _button=None) -> None:
        self.current_folder = folder
        clear_container(self.content)

        titles = {"inbox": "Inkorg", "sent": "Skickat"}
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header.pack_start(
            make_label(titles.get(folder, folder.title()), 25, True),
            True,
            True,
            0,
        )
        refresh = Gtk.Button(label="Uppdatera")
        refresh.connect("clicked", lambda *_: self.show_folder(folder))
        header.pack_end(refresh, False, False, 0)
        self.content.pack_start(header, False, False, 10)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.content.pack_start(scrolled, True, True, 0)

        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        scrolled.add(list_box)

        mails = get_sent(self.username) if folder == "sent" else get_inbox(self.username)

        if not mails:
            empty = make_label("Inga meddelanden här ännu.", 14)
            empty.set_margin_top(40)
            empty.set_margin_start(20)
            list_box.add(empty)
        else:
            for mail in mails:
                row = Gtk.ListBoxRow()
                row.mail_id = mail["id"]
                row.folder = folder

                box = Gtk.Box(
                    orientation=Gtk.Orientation.HORIZONTAL, spacing=15
                )
                box.set_margin_top(14)
                box.set_margin_bottom(14)
                box.set_margin_start(15)
                box.set_margin_end(15)

                peer = mail["recipient"] if folder == "sent" else mail["sender"]
                unread = folder != "sent" and not bool(mail["is_read"])

                peer_label = make_label(peer, 11, unread)
                peer_label.set_size_request(230, -1)
                subject = make_label(mail["subject"], 11, unread)
                subject.set_hexpand(True)
                date = make_label(mail["created_at"], 10)

                box.pack_start(peer_label, False, False, 0)
                box.pack_start(subject, True, True, 0)
                box.pack_end(date, False, False, 0)
                row.add(box)
                list_box.add(row)

            list_box.connect("row-activated", self.open_mail)

        self.content.show_all()

    def open_mail(self, _list_box, row) -> None:
        if not hasattr(row, "mail_id"):
            return

        folder = getattr(row, "folder", self.current_folder)
        mail = get_mail(row.mail_id, self.username, folder)
        if not mail:
            return

        clear_container(self.content)

        back = Gtk.Button(
            label=(
                "Tillbaka till skickat"
                if folder == "sent"
                else "Tillbaka till inkorg"
            )
        )
        back.connect("clicked", lambda *_: self.show_folder(folder))
        self.content.pack_start(back, False, False, 0)

        self.content.pack_start(
            make_label(mail["subject"], 24, True), False, False, 15
        )
        self.content.pack_start(
            make_label(f"Från: {mail['sender']}", 11), False, False, 0
        )
        self.content.pack_start(
            make_label(f"Till: {mail['recipient']}", 11), False, False, 0
        )
        self.content.pack_start(
            make_label(mail["created_at"], 10), False, False, 0
        )
        self.content.pack_start(
            Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL),
            False,
            False,
            20,
        )

        body_scroll = Gtk.ScrolledWindow()
        body_scroll.set_policy(
            Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC
        )
        body = Gtk.TextView()
        body.set_editable(False)
        body.set_cursor_visible(False)
        body.set_wrap_mode(Gtk.WrapMode.WORD)
        body.get_buffer().set_text(mail["body"] or "")
        body_scroll.add(body)
        self.content.pack_start(body_scroll, True, True, 0)
        self.content.show_all()

    def compose(self, _button=None) -> None:
        dialog = Gtk.Dialog(
            title="Nytt meddelande",
            transient_for=self,
            flags=0,
        )
        dialog.add_buttons(
            "Avbryt",
            Gtk.ResponseType.CANCEL,
            "Skicka",
            Gtk.ResponseType.OK,
        )
        dialog.set_default_size(650, 600)

        area = dialog.get_content_area()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        box.set_margin_start(20)
        box.set_margin_end(20)
        area.add(box)

        box.pack_start(make_label("Till", 11, True), False, False, 0)
        recipient = Gtk.Entry()
        recipient.set_placeholder_text(f"bob@{DOMAIN}")
        box.pack_start(recipient, False, False, 0)

        box.pack_start(make_label("Ämne", 11, True), False, False, 10)
        subject = Gtk.Entry()
        subject.set_placeholder_text("Ämne")
        box.pack_start(subject, False, False, 0)

        box.pack_start(make_label("Meddelande", 11, True), False, False, 10)
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        body = Gtk.TextView()
        body.set_wrap_mode(Gtk.WrapMode.WORD)
        scroll.add(body)
        box.pack_start(scroll, True, True, 0)

        dialog.show_all()
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            to = recipient.get_text().strip()
            subj = subject.get_text().strip()
            buffer = body.get_buffer()
            text = buffer.get_text(
                buffer.get_start_iter(), buffer.get_end_iter(), False
            )

            if not to:
                message_dialog(self, "Ange en mottagare.", True)
            else:
                success, message = send_mail(
                    self.username, to, subj, text
                )
                if success:
                    message_dialog(self, "Meddelandet skickades.")
                    if self.current_folder == "sent":
                        self.show_folder("sent")
                else:
                    message_dialog(self, message, True)

        dialog.destroy()

    def logout(self, _button=None) -> None:
        self.hide()
        self.login_window.username_entry.set_text("")
        self.login_window.password_entry.set_text("")
        self.login_window.show()
        self.destroy()

    def on_close(self, _window, _event):
        Gtk.main_quit()
        return False
