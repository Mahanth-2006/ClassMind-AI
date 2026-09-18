from pydantic import BaseModel, Field


class ClassroomCreate(BaseModel):
    teacher_name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Name of the teacher creating the classroom"
    )


class ClassroomJoin(BaseModel):
    classroom_id: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="6-character classroom code"
    )

    student_name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Student joining the classroom"
    )