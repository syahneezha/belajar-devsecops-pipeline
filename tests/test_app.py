"""Unit test untuk aplikasi login Flask (app.py)."""
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
