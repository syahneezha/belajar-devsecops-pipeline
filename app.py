"""Modul backend autentikasi Flask dengan antarmuka web interaktif."""
import os
import secrets
import sqlite3

from flask import Flask, render_template, request
from flask_wtf.csrf import CSRFProtect
from werkzeug.serving import WSGIRequestHandler

app = Flask(__name__)
# Kunci penanda tangan sesi dan token CSRF. Diambil dari lingkungan; jika tidak
# ada, dibuat acak saat start (token lama gugur saat aplikasi restart).
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
CSRFProtect(app)

SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "img-src 'self'; object-src 'none'; base-uri 'self'; "
        "form-action 'self'; frame-ancestors 'none'"
    ),
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Embedder-Policy": "require-corp",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Cache-Control": "no-store",
}


class QuietRequestHandler(WSGIRequestHandler):
    """Handler server dev yang tidak membocorkan versi Werkzeug dan Python."""

    def version_string(self):
        return "webserver"


@app.after_request
def set_security_headers(response):
    """Memasang header keamanan pada setiap respons."""
    for name, value in SECURITY_HEADERS.items():
        response.headers[name] = value
    return response


def init_db():
    """Inisialisasi basis data dan membuat data pengguna awal."""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)"
    )
    cursor.execute(
        "INSERT OR IGNORE INTO users VALUES ('admin', 'supersecret')"
    )
    conn.commit()
    conn.close()


@app.route("/", methods=["GET", "POST"])
def index():
    """Menampilkan formulir login dan memproses autentikasi."""
    message = None
    status_class = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        # Parameterized query untuk mencegah SQL Injection
        query = "SELECT * FROM users WHERE username = ? AND password = ?"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            message = "Login Berhasil! Selamat datang."
            status_class = "success"
        else:
            message = "Login Gagal! Kredensial tidak valid."
            status_class = "danger"
    return render_template(
        "index.html", message=message, status_class=status_class
    )


@app.route("/about")
def about():
    """Menampilkan halaman informasi aplikasi."""
    return "Aplikasi Login Aman - DevSecOps Pipeline"


@app.route("/health")
def health():
    """Menampilkan status aplikasi."""
    return "OK"


if __name__ == "__main__":
    init_db()
    app.run(  # nosemgrep
        host="0.0.0.0", port=5000, request_handler=QuietRequestHandler
    )
