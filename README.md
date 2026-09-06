# Nivra

Privat, lokalt hostad mailprovider i Python — GTK-desktopklient plus lokal SMTP/IMAP.

## Struktur

```
nivra/
├── main.py           # Startar GUI + SMTP/IMAP på localhost
├── gui.py            # GTK-gränssnitt (login, inkorg, skicka)
├── database.py       # SQLite
├── auth.py           # Konton + PBKDF2-lösenord
├── mail.py           # Skicka / hämta / mappar
├── smtp_server.py    # SMTP på 127.0.0.1:2525
├── imap_server.py    # Enkel IMAP på 127.0.0.1:1143
├── config.py         # Domän, portar, sökvägar
└── data/
    └── mail.db       # Skapas automatiskt
```

## Krav

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
```

## Starta

```bash
python3 main.py
```

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
