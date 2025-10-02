# Steam Code Gate

A minimal Flask application that reads Steam-related emails via IMAP and publicly displays only the latest Steam Guard new-device login code. Other Steam emails are counted for basic statistics but are never exposed. No credentials are rendered or returned by any API.

## IMPORTANT WARNING
- This project was refactored by GPT-5 and is provided as reference only.
- Prior deployments ran without issues, but this does not constitute thorough security testing.
- Exposing personal credentials to the public internet is strongly discouraged. If anyone chooses to do so, the author assumes no responsibility for any consequences.

### Background
From May 23, 2024 to Sep 22, 2024, I publicly shared a non-primary Steam family account (linked to my main library) as part of a lighthearted “social experiment.” This app was created to display the latest login code to participants while keeping other information private.

Experiment links:
- Start: https://api.xiaoheihe.cn/v3/bbs/app/api/web/share?link_id=0de16e7f0149
- End:   https://api.xiaoheihe.cn/v3/bbs/app/api/web/share?link_id=11766f1b8c41

### What it does
- Connects to an IMAP inbox (e.g., QQ Mail, Outlook.com, Gmail).
- Filters emails from Steam (default: noreply@steampowered.com).
- Parses messages and classifies types.
- Displays only the latest LOGIN (new-device) code on the page and API.
- Stores non-LOGIN items for stats only; their codes are forcibly cleared server-side.

### Security by design
- Secrets are not exposed via HTML or JSON; use environment variables (IMAP_PASSWORD).
- API returns minimal fields and only for LOGIN messages.
- Non-LOGIN codes are cleared during processing to prevent accidental leakage.

### Tech stack (brief)
- Python 3, Flask 3.x
- IMAP over SSL (imaplib)
- RFC-compliant date parsing (email.utils.parsedate_to_datetime)
- Simple file-based cache

### Quick start
1) Set environment variables:
    - IMAP_USERNAME=your_name@qq.com
    - IMAP_PASSWORD=qq_imap_auth_code
    - (optional) IMAP_HOST / IMAP_PORT / SENDER_FILTER
2) pip install flask
3) python app.py
4) Open http://127.0.0.1:1244

### Note
A lightweight, hobby-oriented project; keep deployments simple and private.