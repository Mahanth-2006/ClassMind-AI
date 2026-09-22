from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException

from app.storage import classrooms
from app.websocket.manager import manager

router = APIRouter(tags=["Teacher WebSocket"])


@router.websocket("/ws/teacher/{classroom_id}")
async def teacher_websocket(websocket: WebSocket, classroom_id: str):
    """
    WebSocket endpoint for the teacher dashboard.
    """

    # Validate classroom before accepting connection
    if classroom_id not in classrooms:
        await websocket.close(code=1008)
        return

    await manager.connect_teacher(classroom_id, websocket)

    try:
        while True:
            message = await websocket.receive_text()

            await websocket.send_json({
                "type": "echo",
                "classroom_id": classroom_id,
                "message": message
            })

    except WebSocketDisconnect:
        manager.disconnect_teacher(classroom_id)