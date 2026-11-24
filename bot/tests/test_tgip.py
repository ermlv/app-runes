"""Тесты tgip.py — локальная подмена DNS для api.telegram.org (Task 7)."""
import socket


def test_install_routes_host_to_fixed_ip():
    import tgip
    tgip.install("api.telegram.org", "149.154.167.220")
    try:
        infos = socket.getaddrinfo("api.telegram.org", 443,
                                   type=socket.SOCK_STREAM)
        assert infos, "getaddrinfo ничего не вернул"
        assert all(i[4][0] == "149.154.167.220" for i in infos)
    finally:
        tgip.uninstall()


def test_uninstall_restores_original_resolver():
    import tgip
    assert socket.getaddrinfo is tgip._orig  # до установки — оригинальный
    tgip.install("api.telegram.org", "149.154.167.220")
    assert socket.getaddrinfo is not tgip._orig
    tgip.uninstall()
    assert socket.getaddrinfo is tgip._orig


def test_other_hosts_unaffected(monkeypatch):
    """Чужой хост уходит в оригинальный резолвер без подмены, целевой — с подменой."""
    import tgip
    seen = []
    real_getaddrinfo = socket.getaddrinfo  # настоящий резолвер до эксперимента

    def fake_orig(host, port, *args, **kwargs):
        seen.append(host)
        return [("fake-af",)]

    monkeypatch.setattr(tgip, "_orig", fake_orig)
    tgip.install("api.telegram.org", "149.154.167.220")
    try:
        socket.getaddrinfo("example.com", 443, type=socket.SOCK_STREAM)
        socket.getaddrinfo("api.telegram.org", 443, type=socket.SOCK_STREAM)
    finally:
        tgip.uninstall()          # запишет в socket текущий (мок) _orig
        socket.getaddrinfo = real_getaddrinfo  # …поэтому возвращаем настоящий
    assert seen == ["example.com", "149.154.167.220"], seen


def test_config_tg_api_ip_reads_env(monkeypatch):
    import importlib
    import config
    # bot/.env может задавать TG_API_IP (локальный воркaround) — проверяем
    # контракт «переменная окружения → config», а не дефолт в чистом окружении
    monkeypatch.setenv("TG_API_IP", "9.9.9.9")
    importlib.reload(config)
    assert config.TG_API_IP == "9.9.9.9"
