# Nivra

Privat, lokalt hostad mailprovider i Python — desktopklient (tkinter) plus lokal SMTP/IMAP.
Fungerar på **Windows**, macOS och Linux med vanlig Python.

## Struktur

```
nivra/
├── main.py           # Startar GUI + SMTP/IMAP på localhost
├── gui.py            # Tkinter-gränssnitt (login, inkorg, skicka)
├── database.py       # SQLite
├── auth.py           # Konton + PBKDF2-lösenord
├── mail.py           # Skicka / hämta / mappar
├── smtp_server.py    # SMTP på 127.0.0.1:2525
├── imap_server.py    # Enkel IMAP på 127.0.0.1:1143
├── config.py         # Domän, portar, sökvägar
└── data/
    └── mail.db       # Skapas automatiskt
```

## Krav (Windows)

1. Installera [Python 3.10+](https://www.python.org/downloads/)
2. Under installationen: kryssa i **Add python.exe to PATH**
3. Låt **tcl/tk and IDLE** vara ikryssat (standard) — behövs för GUI

Inga GUI-ramverk utöver det — men **Pillow** behövs för skarpa knappar:

```powershell
py -m pip install -r requirements.txt
```

(`start.bat` installerar det automatiskt.)

## Starta

Dubbelklicka på `start.bat`, eller i PowerShell i projektmappen:

```powershell
py main.py
```

(Alternativt `python main.py` om Python finns i PATH.)

Appen lyssnar bara på **localhost**:

| Tjänst | Adress |
|--------|--------|
| SMTP   | `127.0.0.1:2525` |
| IMAP   | `127.0.0.1:1143` |
| Domän  | `nivra.local` |

## Första användning

1. Starta programmet
2. Skapa två konton, t.ex. `alice` och `bob`
3. Logga in som alice och skicka till `bob@nivra.local`
4. Logga in som bob och läs i inkorgen

Adresser är alltid `användarnamn@nivra.local`.

## Tester (valfritt)

```powershell
python test_smoke.py
python test_servers.py
```

## Funktioner (v1)

- Skapa konto / logga in
- Inkorg och Skickat
- Läsa och skicka mail mellan lokala användare
- Lokal SMTP-server (localhost)
- Minimal IMAP-server (LOGIN / SELECT / FETCH / LOGOUT)
- Lösenord hashas med PBKDF2-SHA256 + salt

## Nästa steg

- Utkast och papperskorg i GUI
- Sökning och bilagor
- Notifikationer och inställningar
- Fullständigare IMAP (UID, SEARCH, FLAGS)
- Starkare SMTP-auth (LOGIN/PLAIN) och TLS för labbmiljö
