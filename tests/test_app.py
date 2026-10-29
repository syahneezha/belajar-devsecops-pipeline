"""Unit test untuk aplikasi login Flask (app.py)."""
import re
import sqlite3

import pytest

import app as app_module


@pytest.fixture(name="client")
def client_fixture(tmp_path, monkeypatch):
    """Client Flask dengan database sqlite sementara.

    app.py memakai file "users.db" relatif terhadap folder kerja, jadi
    folder kerja dipindah ke tmp_path agar test tidak menyentuh data asli.
    """
    monkeypatch.chdir(tmp_path)
    app_module.init_db()
    app_module.app.config["TESTING"] = True
    # CSRF dimatikan agar test fungsional fokus ke logika login;
    # perlindungan CSRF diuji terpisah lewat fixture csrf_client.
    monkeypatch.setitem(app_module.app.config, "WTF_CSRF_ENABLED", False)
    with app_module.app.test_client() as test_client:
        yield test_client


@pytest.fixture(name="csrf_client")
def csrf_client_fixture(tmp_path, monkeypatch):
    """Client Flask dengan perlindungan CSRF aktif seperti di produksi."""
    monkeypatch.chdir(tmp_path)
    app_module.init_db()
    app_module.app.config["TESTING"] = True
    monkeypatch.setitem(app_module.app.config, "WTF_CSRF_ENABLED", True)
    with app_module.app.test_client() as test_client:
        yield test_client


def test_index_get_menampilkan_form_login(client):
    """GET / menampilkan halaman login tanpa pesan."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Portal Login" in response.data
    assert b'class="alert' not in response.data


def test_login_berhasil(client):
    """POST / dengan kredensial benar menampilkan pesan sukses."""
    response = client.post(
        "/", data={"username": "admin", "password": "supersecret"}
    )
    assert response.status_code == 200
    assert b"Login Berhasil" in response.data
    assert b'class="alert success"' in response.data


def test_login_gagal_password_salah(client):
    """POST / dengan password salah menampilkan pesan gagal."""
    response = client.post(
        "/", data={"username": "admin", "password": "salah"}
    )
    assert response.status_code == 200
    assert b"Login Gagal" in response.data


def test_login_gagal_field_kosong(client):
    """POST / tanpa field apa pun tetap ditolak dengan pesan gagal."""
    response = client.post("/", data={})
    assert response.status_code == 200
    assert b"Login Gagal" in response.data


def test_login_tahan_sql_injection(client):
    """Query berparameter: payload SQL injection tidak boleh lolos login."""
    response = client.post(
        "/", data={"username": "' OR '1'='1", "password": "' OR '1'='1"}
    )
    assert response.status_code == 200
    assert b"Login Gagal" in response.data


def test_about(client):
    """GET /about mengembalikan teks informasi aplikasi."""
    response = client.get("/about")
    assert response.status_code == 200
    assert b"DevSecOps Pipeline" in response.data


def test_health(client):
    """GET /health dipakai health check dan harus mengembalikan OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.data == b"OK"


def test_init_db_membuat_user_admin(tmp_path, monkeypatch):
    """init_db() membuat tabel users berisi akun admin awal."""
    monkeypatch.chdir(tmp_path)
    app_module.init_db()
    conn = sqlite3.connect("users.db")
    user = conn.execute(
        "SELECT username FROM users WHERE username = 'admin'"
    ).fetchone()
    conn.close()
    assert user is not None


def test_post_tanpa_token_csrf_ditolak(csrf_client):
    """POST / tanpa token CSRF harus ditolak dengan status 400."""
    response = csrf_client.post(
        "/", data={"username": "admin", "password": "supersecret"}
    )
    assert response.status_code == 400


def test_login_dengan_token_csrf_valid(csrf_client):
    """POST / dengan token CSRF dari form diterima dan login berhasil."""
    page = csrf_client.get("/")
    match = re.search(rb'name="csrf_token" value="([^"]+)"', page.data)
    assert match is not None
    response = csrf_client.post(
        "/",
        data={
            "username": "admin",
            "password": "supersecret",
            "csrf_token": match.group(1).decode(),
        },
    )
    assert response.status_code == 200
    assert b"Login Berhasil" in response.data


def test_header_keamanan_terpasang(client):
    """Setiap respons membawa header keamanan dan tidak membocorkan versi."""
    response = client.get("/")
    for name in (
        "Content-Security-Policy",
        "X-Frame-Options",
        "X-Content-Type-Options",
        "Referrer-Policy",
        "Permissions-Policy",
        "Cross-Origin-Opener-Policy",
        "Cross-Origin-Embedder-Policy",
        "Cross-Origin-Resource-Policy",
    ):
        assert name in response.headers
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
    assert "unsafe-inline" not in response.headers["Content-Security-Policy"]
    assert "Werkzeug" not in response.headers.get("Server", "")


def test_css_statis_tersedia(client):
    """CSS dilayani dari file statis agar CSP tidak perlu unsafe-inline."""
    response = client.get("/static/style.css")
    assert response.status_code == 200
    assert response.mimetype == "text/css"


def test_handler_server_tidak_membocorkan_versi():
    """Handler server dev hanya menyebut nama generik, tanpa versi."""
    handler = app_module.QuietRequestHandler
    assert handler.version_string(object()) == "webserver"
