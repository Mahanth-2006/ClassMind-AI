from fastapi import WebSocket

from app.storage import teacher_connections, student_connections


class ConnectionManager:
    """Manages active WebSocket connections."""

    async def connect_teacher(self, classroom_id: str, websocket: WebSocket):
        await websocket.accept()
        teacher_connections[classroom_id] = websocket

    def disconnect_teacher(self, classroom_id: str):
        teacher_connections.pop(classroom_id, None)

    async def connect_student(
        self,
        classroom_id: str,
        student_id: str,
        websocket: WebSocket,
    ):
        await websocket.accept()

        if classroom_id not in student_connections:
            student_connections[classroom_id] = {}

        student_connections[classroom_id][student_id] = websocket

    def disconnect_student(self, classroom_id: str, student_id: str):
        if classroom_id in student_connections:
            student_connections[classroom_id].pop(student_id, None)

            if not student_connections[classroom_id]:
                student_connections.pop(classroom_id)

    async def send_to_teacher(self, classroom_id: str, message: dict):
        websocket = teacher_connections.get(classroom_id)

        if websocket:
            await websocket.send_json(message)

    async def broadcast_to_students(self, classroom_id: str, message: dict):
        if classroom_id not in student_connections:
            return

        for websocket in student_connections[classroom_id].values():
            await websocket.send_json(message)


manager = ConnectionManager()