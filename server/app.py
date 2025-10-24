#!/usr/bin/env python3
"""A minimal HTTP ingest server for Koyeb-compatible deployment.

STM32 (or any TCP device) should send an HTTP POST to /ingest with a plain
text body. Browsers connect to /events (Server-Sent Events) to receive live
updates and index.html displays them.

This app reads PORT from the environment (Koyeb sets $PORT). It serves static
files from the same folder so a single process handles HTTP and SSE on one
public port.
"""
import os
import asyncio
from aiohttp import web

STATIC_DIR = os.path.join(os.path.dirname(__file__))
PORT = int(os.environ.get("PORT", "2029"))

clients = set()  # set of asyncio.Queue objects, one per SSE client

async def ingest(request):
    try:
        text = await request.text()
    except Exception:
        return web.Response(status=400, text="Bad request")
    text = text.rstrip("\r\n")
    print("Ingest received:", text)
    # broadcast to SSE clients
    for q in list(clients):
        # use put_nowait to avoid waiting; if full, skip
        try:
            q.put_nowait(text)
        except asyncio.QueueFull:
            pass
    return web.Response(text="ok\n")

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
    print("SSE client connected, total:", len(clients))
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
        print("SSE client disconnected, total:", len(clients))
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
    print(f"Starting server on http://0.0.0.0:{PORT}/")
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
