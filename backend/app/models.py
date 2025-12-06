from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    Text,
    Numeric,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base
import uuid


def uuid_str():
    return str(uuid.uuid4())


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    enrollment_date = Column(Date, nullable=False)
    class_ = Column("class", String)
    section = Column(String)
    roll_number = Column(String)

    student_assignments = relationship("StudentAssignment", back_populates="student")


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    due_date = Column(Date, nullable=False)
    subject = Column(String)
    course = Column(String)

    student_assignments = relationship("StudentAssignment", back_populates="assignment")


class StudentAssignment(Base):
    __tablename__ = "student_assignments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    time_taken_minutes = Column(Integer)
    status = Column(String)          # assigned / in_progress / submitted / graded
    score = Column(Numeric)
    submitted_at = Column(DateTime)

    student = relationship("Student", back_populates="student_assignments")
    assignment = relationship("Assignment", back_populates="student_assignments")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=uuid_str, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=uuid_str, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    text = Column(Text, nullable=False)
    query_text = Column(Text)
    rows_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    conversation = relationship("Conversation", back_populates="messages")
