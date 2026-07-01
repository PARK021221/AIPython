"""선박 출항 판단기 웹 UI — 외부 패키지 없이 실행됩니다."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

from voyage_checker import VoyageConditions, assess_voyage


HOST = "127.0.0.1"
PORT = 8000
HTML = Path(__file__).with_name("web.html")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/":
            self.send_error(404)
            return
        self._send(200, HTML.read_bytes(), "text/html; charset=utf-8")

    def do_POST(self) -> None:
        if self.path != "/assess":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = parse_qs(self.rfile.read(length).decode("utf-8"))
            checked = lambda name: data.get(name, [""])[0] == "on"
            conditions = VoyageConditions(
                wind_speed_ms=float(data["wind"][0]),
                wave_height_m=float(data["wave"][0]),
                visibility_km=float(data["visibility"][0]),
                vessel_length_m=float(data["length"][0]),
                engine_ok=checked("engine_ok"),
                navigation_ok=checked("navigation_ok"),
                lifesaving_ok=checked("lifesaving_ok"),
                crew_ready=checked("crew_ready"),
                weather_warning=checked("weather_warning"),
            )
            result = assess_voyage(conditions)
            body = {"decision": result.decision.value, "reasons": result.reasons}
            self._send(200, json.dumps(body, ensure_ascii=False).encode(), "application/json; charset=utf-8")
        except (KeyError, ValueError) as exc:
            body = json.dumps({"error": f"입력값을 확인하세요: {exc}"}, ensure_ascii=False).encode()
            self._send(400, body, "application/json; charset=utf-8")

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        pass


if __name__ == "__main__":
    print(f"웹 브라우저에서 http://{HOST}:{PORT} 를 여세요.")
    print("종료하려면 이 창에서 Ctrl+C를 누르세요.")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
