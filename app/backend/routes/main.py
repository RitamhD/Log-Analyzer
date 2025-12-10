from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import uvicorn



app = FastAPI()

clients = set()

@app.websocket("/events/live")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        while True:
            data = await ws.receive_text()
            # Later push this data to dashboard in realtime via pub/sub
            print("Data: ", data)
    except WebSocketDisconnect:
        clients.remove(ws)


@app.post("/analyze")
async def analyze(payload: dict):
    events = payload.get("events", [])
    print("Batch received count: ", len(events))
    # Apply ML analysis here
    return JSONResponse({"status" : "ok", "count": len(events)})


if __name__ == "__main__":
    uvicorn.run(app=app)
        
    