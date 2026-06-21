/**
 * Server-only transactional email utility using Nodemailer + Gmail OAuth2.
 *
 * Required env vars (all optional — logs to console when absent):
 *   GOOGLE_CLIENT_ID       — OAuth2 client ID
 *   GOOGLE_CLIENT_SECRET   — OAuth2 client secret
 *   GOOGLE_REFRESH_TOKEN   — refresh token for the sending account
 *   GOOGLE_OAUTH_EMAIL     — Gmail address that sends mail (e.g. you@gmail.com)
 */
import "server-only";

import nodemailer from "nodemailer";
import type { Transporter } from "nodemailer";

let _transporter: Transporter | null = null;

function configured(): boolean {
  return !!(
    process.env.GOOGLE_CLIENT_ID &&
    process.env.GOOGLE_CLIENT_SECRET &&
    process.env.GOOGLE_REFRESH_TOKEN &&
    process.env.GOOGLE_OAUTH_EMAIL
  );
}

function getTransporter(): Transporter {
  if (!_transporter) {
    _transporter = nodemailer.createTransport({
      service: "gmail",
      auth: {
        type: "OAuth2",
        user: process.env.GOOGLE_OAUTH_EMAIL,
        clientId: process.env.GOOGLE_CLIENT_ID,
        clientSecret: process.env.GOOGLE_CLIENT_SECRET,
        refreshToken: process.env.GOOGLE_REFRESH_TOKEN,
      },
    });
  }
  return _transporter;
}

export async function sendEmail(
  to: string,
  subject: string,
  html: string,
  text?: string
): Promise<boolean> {
  if (!configured()) return false;
  try {
    await getTransporter().sendMail({
      from: process.env.GOOGLE_OAUTH_EMAIL,
      to,
      subject,
      text,
      html,
    });
    return true;
  } catch (err) {
    console.error("[email-server] send failed:", err);
    return false;
  }
}
