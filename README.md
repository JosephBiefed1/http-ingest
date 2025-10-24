# HTTP ingest server (Koyeb compatible)

This minimal project accepts HTTP POSTs from devices (STM32) at `/ingest`
and broadcasts them to connected browsers using Server-Sent Events (SSE) at
`/events`. It serves static files from `server/` so a single process handles
everything on the port provided by Koyeb ($PORT).

Run locally

```powershell
cd "http-ingest/server"
python -m pip install -r "..\requirements.txt"
# optionally set PORT (default 2029)
$env:PORT=2029; python app.py
```

Test from command-line

```powershell
curl -X POST http://localhost:2029/ingest -d "temperature : 30"
```

STM32 guidance

- Change `DEST_PORT` to the server port (2029 locally; Koyeb will set $PORT).
- Send an HTTP POST to `/ingest` with the message in the request body. Your
  existing code already shows how to compose an HTTP POST when `USING_IOT_SERVER`.

Deploy to Koyeb

- Ensure `Procfile` exists at repo root (provided) and `requirements.txt` lists
  `aiohttp` (provided).
- Koyeb will set the `PORT` environment variable; the app reads it and binds
  to the correct port.
