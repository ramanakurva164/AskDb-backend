from datetime import date, datetime, timedelta
from app.db import SessionLocal, engine, Base
from app import models


def seed():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Clear existing data (dev only)
        db.query(models.StudentAssignment).delete()
        db.query(models.Assignment).delete()
        db.query(models.Student).delete()
        db.commit()

        # Students
        s1 = models.Student(
            first_name="Riya",
            last_name="Sharma",
            email="riya@example.com",
            enrollment_date=date(2024, 6, 1),
            class_="10",
            section="A",
            roll_number="12",
        )
        s2 = models.Student(
            first_name="Arjun",
            last_name="Verma",
            email="arjun@example.com",
            enrollment_date=date(2024, 6, 1),
            class_="10",
            section="A",
            roll_number="15",
        )

        # Assignments
        a1 = models.Assignment(
            title="Math Worksheet 1",
            description="Algebra basics",
            due_date=date.today() + timedelta(days=3),
            subject="Math",
            course="Algebra I",
        )
        a2 = models.Assignment(
            title="Physics Lab Report",
            description="Experiment on motion",
            due_date=date.today() + timedelta(days=7),
            subject="Physics",
            course="Physics I",
        )

        db.add_all([s1, s2, a1, a2])
        db.flush()

        # StudentAssignments
        sa1 = models.StudentAssignment(
            student_id=s1.id,
            assignment_id=a1.id,
            status="in_progress",
        )
        sa2 = models.StudentAssignment(
            student_id=s1.id,
            assignment_id=a2.id,
            status="assigned",
        )
        sa3 = models.StudentAssignment(
            student_id=s2.id,
            assignment_id=a1.id,
            status="submitted",
            score=92,
            submitted_at=datetime.utcnow() - timedelta(days=1),
        )

        db.add_all([sa1, sa2, sa3])
        db.commit()
        print("Seed data inserted.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
