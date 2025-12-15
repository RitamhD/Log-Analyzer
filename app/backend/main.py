import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from app.backend.schemas.event import EventBatch
from app.backend.preprocessing.normalize import normalize_event
from app.backend.pipeline.dispatcher import dispatch_for_analysis


app = FastAPI(title="Log Analysis Backend")

clients = set()

@app.websocket("/events/live")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        while True:
            data = await ws.receive_text()
            # Later we push this data to dashboard in realtime via pub/sub
            print("Data:\n", data)
    except WebSocketDisconnect:
        clients.remove(ws)


@app.post("/analyze")
def analyze(batch: EventBatch):
    normalized_events = [normalize_event(e) for e in batch.events]
    dispatch_for_analysis(normalized_events)
    return {
        "status": "accepted",
        "count": len(normalized_events)
    }



if __name__ == "__main__":
    uvicorn.run(app=app)
        
    