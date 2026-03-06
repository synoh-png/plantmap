#!/usr/bin/env python3
"""
Local dev server for power_plant_map.html
- Static file serving (HTML, CSV, etc.)
- Reverse proxy for Naver Geocoding API (bypasses CORS)
  -> GET /api/geocode?q=주소  returns Naver Geocoding JSON
"""

import http.server
import urllib.request
import urllib.parse
import json
import sys

# ====================================================
# Naver Geocoding API Credentials
# ====================================================
NAVER_CLIENT_ID     = '1r1kquageh'
NAVER_CLIENT_SECRET = 'zCFOuX6i1yzDoGaoPkDy7Ri6Xl6qTGBQgJFVuZGz'

PORT = 8000


class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        # ── Geocode proxy endpoint ──────────────────
        if parsed.path == '/api/geocode':
            params = urllib.parse.parse_qs(parsed.query)
            query  = params.get('q', [''])[0]

            if not query:
                self.send_error(400, 'Missing query parameter: q')
                return

            naver_url = (
                'https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode'
                f'?query={urllib.parse.quote(query)}'
            )
            req = urllib.request.Request(naver_url, headers={
                'X-NCP-APIGW-API-KEY-ID': NAVER_CLIENT_ID,
                'X-NCP-APIGW-API-KEY':    NAVER_CLIENT_SECRET,
            })

            try:
                with urllib.request.urlopen(req, timeout=5) as r:
                    body = r.read()
            except Exception as e:
                print(f'[Geocode ERROR] {query}: {e}', flush=True)
                self.send_error(502, str(e))
                return

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(body)

        # ── Static file serving ─────────────────────
        else:
            super().do_GET()

    def log_message(self, fmt, *args):
        # Only log non-static requests to reduce noise
        if '/api/' in args[0] if args else True:
            super().log_message(fmt, *args)


if __name__ == '__main__':
    server = http.server.HTTPServer(('', PORT), ProxyHandler)
    print(f'✅  Serving at  http://localhost:{PORT}/power_plant_map.html')
    print(f'🌐  Geocode API at http://localhost:{PORT}/api/geocode?q=주소')
    print('Press Ctrl+C to stop.\n')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopped.')
