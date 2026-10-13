import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.storage import classrooms, teacher_connections
from app.websocket.manager import manager

router = APIRouter(tags=["Teacher WebSocket"])


@router.websocket("/ws/teacher/{classroom_id}")
async def teacher_websocket(websocket: WebSocket, classroom_id: str):
    """
    WebSocket endpoint for the teacher dashboard.
    """

    # 1. Validate classroom before accepting connection
    if classroom_id not in classrooms:
        await websocket.close(code=1008, reason="Classroom not found")
        return

    # 2. Reject duplicate connection: at most one active teacher per classroom
    if classroom_id in teacher_connections:
        await websocket.close(code=1008, reason="Teacher already connected")
        return

    # 3. Accept and register connection
    await manager.connect_teacher(classroom_id, websocket)

    try:
        while True:
            raw_text = await websocket.receive_text()

            # Parse JSON message safely
            try:
                data = json.loads(raw_text)
            except (json.JSONDecodeError, ValueError):
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON message"
                })
                continue

            # Echo JSON response preserving message structure
            message_content = data.get("message", data) if isinstance(data, dict) else data
            await websocket.send_json({
                "type": "echo",
                "classroom_id": classroom_id,
                "message": message_content
            })

    except WebSocketDisconnect:
        pass
    except Exception:
        # Prevent unexpected errors from crashing the server
        pass
    finally:
        manager.disconnect_teacher(classroom_id, websocket)