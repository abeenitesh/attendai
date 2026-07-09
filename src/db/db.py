import bcrypt
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from src.db.config import get_connection



# ==========================
# Password Helpers
# ==========================

def hash_pass(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_pass(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ==========================
# Teachers
# ==========================

def check_teacher_exists(username):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM teachers WHERE username=%s",
                (username,)
            )
            return cur.fetchone() is not None


def create_teacher(username, password, name):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                INSERT INTO teachers(username, password, name)
                VALUES (%s,%s,%s)
                RETURNING *
            """, (
                username,
                hash_pass(password),
                name
            ))
            return cur.fetchone()


def teacher_login(username, password):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM teachers WHERE username=%s",
                (username,)
            )

            teacher = cur.fetchone()

            if teacher and check_pass(password, teacher["password"]):
                return teacher

            return None


# ==========================
# Students
# ==========================

def get_all_students():
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM students")
            return cur.fetchall()


def create_student(name, face_embedding=None, voice_embedding=None):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                INSERT INTO students(name, face_embedding, voice_embedding)
                VALUES (%s,%s,%s)
                RETURNING *
            """, (
                name,
                Jsonb(face_embedding),
                Jsonb(voice_embedding)
            ))
            return cur.fetchone()


# ==========================
# Subjects
# ==========================

def create_subject(subject_code, name, section, teacher_id):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                INSERT INTO subjects
                (subject_code,name,section,teacher_id)
                VALUES (%s,%s,%s,%s)
                RETURNING *
            """, (
                subject_code,
                name,
                section,
                teacher_id
            ))
            return cur.fetchone()


def get_teacher_subjects(teacher_id):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    s.*,
                    COUNT(DISTINCT ss.student_id) AS total_students,
                    COUNT(DISTINCT al.timestamp) AS total_classes
                FROM subjects s
                LEFT JOIN subject_students ss
                    ON s.subject_id = ss.subject_id
                LEFT JOIN attendance_logs al
                    ON s.subject_id = al.subject_id
                WHERE s.teacher_id = %s
                GROUP BY s.subject_id
                ORDER BY s.subject_code;
            """, (teacher_id,))

            return cur.fetchall()


# ==========================
# Subject Enrollment
# ==========================

def enroll_student_to_subject(student_id, subject_id):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                INSERT INTO subject_students(student_id, subject_id)
                VALUES (%s,%s)
                RETURNING *
            """, (
                student_id,
                subject_id
            ))
            return cur.fetchone()


def unenroll_student_to_subject(student_id, subject_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM subject_students
                WHERE student_id=%s
                AND subject_id=%s
            """, (
                student_id,
                subject_id
            ))


def get_student_subjects(student_id):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    s.*
                FROM subjects s
                JOIN subject_students ss
                    ON s.subject_id = ss.subject_id
                WHERE ss.student_id=%s
            """, (student_id,))

            return cur.fetchall()


# ==========================
# Attendance
# ==========================

def get_student_attendance(student_id):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    al.*,
                    s.subject_code,
                    s.name,
                    s.section
                FROM attendance_logs al
                JOIN subjects s
                    ON al.subject_id = s.subject_id
                WHERE al.student_id=%s
                ORDER BY al.timestamp DESC
            """, (student_id,))

            return cur.fetchall()


def create_attendance(logs):
    """
    logs example:
    [
        (1, 5, True),
        (1, 6, False),
        (1, 7, True)
    ]
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany("""
                INSERT INTO attendance_logs
                (timestamp, subject_id, student_id, is_present)
                VALUES (%(timestamp)s, %(subject_id)s, %(student_id)s, %(is_present)s)
            """, logs)


def get_attendance_for_teacher(teacher_id):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    al.*,
                    s.subject_code,
                    s.name AS subject_name,
                    s.section,
                    st.name AS student_name
                FROM attendance_logs al
                JOIN subjects s
                    ON al.subject_id = s.subject_id
                JOIN students st
                    ON al.student_id = st.student_id
                WHERE s.teacher_id=%s
                ORDER BY al.timestamp DESC
            """, (teacher_id,))

            return cur.fetchall()
        
        

def join_subject(student_id, subject_code):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:

            # Find subject
            cur.execute("""
                SELECT subject_id, name, subject_code
                FROM subjects
                WHERE subject_code = %s
            """, (subject_code,))
            subject = cur.fetchone()

            if not subject:
                return "not_found"

            # Check enrollment
            cur.execute("""
                SELECT 1
                FROM subject_students
                WHERE student_id = %s
                  AND subject_id = %s
            """, (student_id, subject["subject_id"]))

            if cur.fetchone():
                return "already_enrolled"

            # Enroll
            cur.execute("""
                INSERT INTO subject_students(student_id, subject_id)
                VALUES (%s, %s)
            """, (student_id, subject["subject_id"]))

            return subject


def get_subject_by_code(subject_code):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT subject_id, name
                FROM subjects
                WHERE subject_code = %s
            """, (subject_code,))
            return cur.fetchone()
        
        
def is_student_enrolled(student_id, subject_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 1
                FROM subject_students
                WHERE student_id = %s
                  AND subject_id = %s
            """, (student_id, subject_id))
            return cur.fetchone() is not None
        

def get_enrolled_students(subject_id):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    ss.subject_id,
                    ss.student_id,
                    st.name,
                    st.face_embedding,
                    st.voice_embedding
                FROM subject_students ss
                JOIN students st
                    ON ss.student_id = st.student_id
                WHERE ss.subject_id = %s
                ORDER BY st.name;
            """, (subject_id,))

            return cur.fetchall()