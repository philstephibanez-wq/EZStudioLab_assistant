from pathlib import Path
root=Path(__file__).resolve().parents[1]
install=(root/'scripts/install-main.ps1').read_text(encoding='utf-8-sig')
web=(root/'scripts/start-web.ps1').read_text(encoding='utf-8-sig')
caddy=(root/'Caddyfile').read_text(encoding='utf-8-sig')
assert "H:\\Caddy\\caddy.exe" in install and "H:\\Caddy\\caddy.exe" in web
assert "2022" in install and "admin 127.0.0.1:2022" in caddy
assert "LLAMA_SERVER_REQUIRED" in install
assert "Assert-FreePort $port" in install
print("MAIN_SHARED_INFRA_STATIC_OK")
