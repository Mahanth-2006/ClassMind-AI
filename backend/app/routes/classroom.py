import random
import string

from fastapi import APIRouter, HTTPException

from app.models import ClassroomCreate, ClassroomJoin
from app.storage import classrooms

router = APIRouter(tags=["Classroom"])


def generate_classroom_code(length: int = 6) -> str:
    """Generate a unique 6-character classroom code."""

    while True:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=length))
        if code not in classrooms:
            return code


@router.post("/classroom/create")
async def create_classroom(data: ClassroomCreate):

    code = generate_classroom_code()

    classrooms[code] = {
        "teacher": data.teacher_name,
        "students": []
    }

    return {
        "classroom_id": code,
        "teacher": data.teacher_name
    }


@router.post("/classroom/join")
async def join_classroom(data: ClassroomJoin):

    if data.classroom_id not in classrooms:
        raise HTTPException(status_code=404, detail="Classroom not found")

    if data.student_name in classrooms[data.classroom_id]["students"]:
        raise HTTPException(status_code=400, detail="Student already joined")

    classrooms[data.classroom_id]["students"].append(data.student_name)

    return {
        "message": "Joined successfully",
        "classroom_id": data.classroom_id,
        "student": data.student_name
    }