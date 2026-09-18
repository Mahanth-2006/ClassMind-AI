from fastapi import WebSocket



# Classroom data
classrooms: dict[str, dict] = {}


# Active teacher WebSocket connections
teacher_connections: dict[str, WebSocket] = {}


# Active student WebSocket connections
student_connections: dict[str, dict[str, WebSocket]] = {}