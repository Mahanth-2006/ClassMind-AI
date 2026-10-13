from fastapi import WebSocket

from app.storage import teacher_connections, student_connections


class ConnectionManager:
    """Manages active WebSocket connections."""

    async def connect_teacher(self, classroom_id: str, websocket: WebSocket):
        await websocket.accept()
        teacher_connections[classroom_id] = websocket

    def disconnect_teacher(self, classroom_id: str, websocket: WebSocket | None = None):
        """Disconnect teacher. If websocket is passed, only disconnect if it matches the active connection."""
        if classroom_id in teacher_connections:
            if websocket is None or teacher_connections[classroom_id] == websocket:
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

    def disconnect_student(self, classroom_id: str, student_id: str, websocket: WebSocket | None = None):
        """Disconnect student. If websocket is passed, only disconnect if it matches."""
        if classroom_id in student_connections:
            if websocket is None or student_connections[classroom_id].get(student_id) == websocket:
                student_connections[classroom_id].pop(student_id, None)

            if not student_connections[classroom_id]:
                student_connections.pop(classroom_id, None)

    async def send_to_teacher(self, classroom_id: str, message: dict):
        websocket = teacher_connections.get(classroom_id)
        if websocket:
            try:
                await websocket.send_json(message)
            except Exception:
                self.disconnect_teacher(classroom_id, websocket)

    async def broadcast_to_students(self, classroom_id: str, message: dict):
        if classroom_id not in student_connections:
            return

        for student_id, websocket in list(student_connections[classroom_id].items()):
            try:
                await websocket.send_json(message)
            except Exception:
                self.disconnect_student(classroom_id, student_id, websocket)


manager = ConnectionManager()