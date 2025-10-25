#!/usr/bin/env python3
"""A minimal HTTP ingest server for Koyeb-compatible deployment.

Accepts JSON POSTs at /ingest, expecting a 'temperature' field.
Browsers connect to /events (Server-Sent Events) to receive live updates.
"""

import os
import asyncio
import json
from aiohttp import web

STATIC_DIR = os.path.join(os.path.dirname(__file__))
PORT = int(os.environ.get("PORT", "2029"))

clients = set()  # set of asyncio.Queue objects, one per SSE client


async def ingest(request):
    # Try header first (no await)
    temp_header = request.headers.get('temperature')
    if temp_header is not None:
        #print("Got temperature from header:", temp_header)
        data = {'temperature': temp_header}
    else:
        # Expect JSON body if header not present
        if not request.content_type or 'json' not in request.content_type:
            return web.Response(status=415, text='Unsupported Media Type: expected application/json or temperature header')

        body = await request.text()
        #print("Raw body:", repr(body))
        if not body or not body.strip():
            return web.Response(status=400, text='Empty body and no temperature header')

        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as e:
            #print("JSON parse error:", e)
            return web.Response(status=400, text=f'Bad JSON: {e.msg}')

        if 'temperature' not in parsed:
            return web.Response(status=400, text='Missing "temperature" field')
        data = {'temperature': parsed['temperature']}

    # Broadcast to SSE clients
    msg = json.dumps(data, separators=(',', ':'))
    ##print("✅ Ingest received:", msg)
    for q in list(clients):
        try:
            q.put_nowait(msg)
        except asyncio.QueueFull:
            pass

    return web.Response(text='ok\n')


async def events(request):
    resp = web.StreamResponse(
        status=200,
        reason='OK',
        headers={
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
        }
    )
    await resp.prepare(request)

    q = asyncio.Queue(maxsize=10)
    clients.add(q)
    ##print("🔌 SSE client connected, total:", len(clients))
    try:
        await resp.write(b": connected\n\n")
        while True:
            msg = await q.get()
            s = f"data: {msg}\n\n"
            try:
                await resp.write(s.encode())
                await resp.drain()
            except ConnectionResetError:
                break
    finally:
        clients.discard(q)
        #print("🔌 SSE client disconnected, total:", len(clients))
    return resp


async def index(request):
    return web.FileResponse(os.path.join(STATIC_DIR, "index.html"))


async def main():
    app = web.Application()
    app.router.add_post('/ingest', ingest)
    app.router.add_get('/events', events)
    app.router.add_get('/', index)
    app.router.add_static('/', STATIC_DIR)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    ##print(f"🚀 Starting server on http://0.0.0.0:{PORT}/")
    await site.start()

    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        pass
    finally:
        await runner.cleanup()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
