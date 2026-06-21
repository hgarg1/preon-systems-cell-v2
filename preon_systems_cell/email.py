"""Transactional email via Gmail OAuth2 SMTP.

Required env vars (all optional — falls back to console logging when absent):
  GOOGLE_CLIENT_ID       — OAuth2 client ID
  GOOGLE_CLIENT_SECRET   — OAuth2 client secret
  GOOGLE_REFRESH_TOKEN   — refresh token for the sending account
  GOOGLE_OAUTH_EMAIL     — Gmail address that sends mail (e.g. you@gmail.com)

To obtain GOOGLE_REFRESH_TOKEN, complete the OAuth2 consent flow once:
  python -m preon_systems_cell.email_setup
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import smtplib
import urllib.parse
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

_SMTP_HOST = "smtp.gmail.com"
_SMTP_PORT = 587
_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"


def _configured() -> bool:
    return all(
        os.getenv(k)
        for k in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REFRESH_TOKEN", "GOOGLE_OAUTH_EMAIL")
    )


def _fetch_access_token() -> str:
    data = urllib.parse.urlencode({
        "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
        "refresh_token": os.getenv("GOOGLE_REFRESH_TOKEN", ""),
        "grant_type": "refresh_token",
    }).encode()
    with urllib.request.urlopen(_TOKEN_ENDPOINT, data=data, timeout=10) as resp:
        return json.loads(resp.read())["access_token"]


def _send_sync(to: str, subject: str, html: str, text: str) -> None:
    sender = os.getenv("GOOGLE_OAUTH_EMAIL", "")
    access_token = _fetch_access_token()
    xoauth2 = base64.b64encode(
        f"user={sender}\x01auth=Bearer {access_token}\x01\x01".encode()
    ).decode()

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to
    if text:
        msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT, timeout=15) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.docmd("AUTH", f"XOAUTH2 {xoauth2}")
        smtp.sendmail(sender, [to], msg.as_string())


async def send_email(to: str, subject: str, html: str, text: str = "") -> bool:
    """Send a transactional email. Returns True on success, False when not configured.
    Never raises — SMTP errors are printed and swallowed."""
    if not _configured():
        return False
    try:
        await asyncio.to_thread(_send_sync, to, subject, html, text)
        return True
    except Exception as exc:
        print(f"[email] send to {to!r} failed: {exc}")
        return False


def verification_email(verification_url: str) -> tuple[str, str, str]:
    """Returns (subject, html, text) for the email verification message."""
    subject = "Verify your Preon account email"
    text = f"Verify your Preon account email:\n{verification_url}\n\nLink expires in 2 hours."
    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0a0a0a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="padding:48px 16px;">
  <tr><td align="center">
    <table width="500" cellpadding="0" cellspacing="0" style="max-width:500px;width:100%;background:#111827;border:1px solid rgba(255,255,255,0.08);border-radius:12px;overflow:hidden;">
      <tr><td style="height:4px;background:linear-gradient(90deg,#6ee7b7,#38bdf8,#6ee7b7);"></td></tr>
      <tr><td style="padding:36px 36px 0;">
        <p style="margin:0 0 8px;font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#6ee7b7;">Preon Systems</p>
        <h1 style="margin:0;font-size:22px;font-weight:600;color:#f5f5f5;">Verify your email</h1>
      </td></tr>
      <tr><td style="padding:20px 36px;">
        <p style="margin:0 0 24px;font-size:15px;line-height:1.6;color:#a3a3a3;">Click the button below to confirm your email address and activate your Preon account.</p>
        <a href="{verification_url}" style="display:inline-block;background:#6ee7b7;color:#0a0a0a;padding:13px 28px;border-radius:8px;text-decoration:none;font-size:15px;font-weight:600;">Verify email address</a>
        <p style="margin:24px 0 0;font-size:12px;color:#525252;">Link expires in 2 hours. If you didn't create a Preon account, you can safely ignore this email.</p>
      </td></tr>
      <tr><td style="padding:20px 36px 28px;border-top:1px solid rgba(255,255,255,0.06);">
        <p style="margin:0;font-size:12px;color:#404040;">Or paste this URL in your browser:<br><span style="color:#6ee7b7;word-break:break-all;">{verification_url}</span></p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body></html>"""
    return subject, html, text


def password_reset_email(reset_url: str) -> tuple[str, str, str]:
    """Returns (subject, html, text) for the password reset message."""
    subject = "Reset your Preon account password"
    text = f"Reset your Preon account password:\n{reset_url}\n\nLink expires in 2 hours. If you didn't request this, ignore it."
    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0a0a0a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="padding:48px 16px;">
  <tr><td align="center">
    <table width="500" cellpadding="0" cellspacing="0" style="max-width:500px;width:100%;background:#111827;border:1px solid rgba(255,255,255,0.08);border-radius:12px;overflow:hidden;">
      <tr><td style="height:4px;background:linear-gradient(90deg,#6ee7b7,#38bdf8,#6ee7b7);"></td></tr>
      <tr><td style="padding:36px 36px 0;">
        <p style="margin:0 0 8px;font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#6ee7b7;">Preon Systems</p>
        <h1 style="margin:0;font-size:22px;font-weight:600;color:#f5f5f5;">Reset your password</h1>
      </td></tr>
      <tr><td style="padding:20px 36px;">
        <p style="margin:0 0 24px;font-size:15px;line-height:1.6;color:#a3a3a3;">Someone requested a password reset for your Preon account. Click below to choose a new password.</p>
        <a href="{reset_url}" style="display:inline-block;background:#6ee7b7;color:#0a0a0a;padding:13px 28px;border-radius:8px;text-decoration:none;font-size:15px;font-weight:600;">Reset password</a>
        <p style="margin:24px 0 0;font-size:12px;color:#525252;">Link expires in 2 hours. If you didn't request a reset, ignore this email — your password is unchanged.</p>
      </td></tr>
      <tr><td style="padding:20px 36px 28px;border-top:1px solid rgba(255,255,255,0.06);">
        <p style="margin:0;font-size:12px;color:#404040;">Or paste this URL in your browser:<br><span style="color:#6ee7b7;word-break:break-all;">{reset_url}</span></p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body></html>"""
    return subject, html, text
