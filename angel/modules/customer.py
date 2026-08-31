from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "angel_business.db"


@dataclass
class Customer:
    id: int
    name: str
    phone: str = ""
    email: str = ""
    address: str = ""
    notes: str = ""


@dataclass
class Lead:
    id: int
    customer_id: int
    project_type: str
    description: str = ""
    status: str = "NEW"
    next_action: str = ""


class CustomerLeadModule:
    STATUSES = (
        "NEW",
        "CONTACTED",
        "ESTIMATE_NEEDED",
        "ESTIMATE_SENT",
        "FOLLOW_UP",
        "WON",
        "LOST",
    )

    NEXT_ACTIONS = {
        "NEW": "Contact customer",
        "CONTACTED": "Schedule estimate",
        "ESTIMATE_NEEDED": "Prepare estimate",
        "ESTIMATE_SENT": "Follow up on estimate",
        "FOLLOW_UP": "Contact customer",
        "WON": "Schedule project",
        "LOST": "No action",
    }

    CUSTOMER_FIELDS = {
        "phone",
        "email",
        "address",
        "notes",
    }

    def __init__(self, db_path=DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _initialize(self):
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT DEFAULT '',
                    email TEXT DEFAULT '',
                    address TEXT DEFAULT '',
                    notes TEXT DEFAULT '',
                    created_at TEXT NOT NULL
                )
            """)

            db.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    project_type TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'NEW',
                    next_action TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(customer_id) REFERENCES customers(id)
                )
            """)

            db.commit()

    def _next_action_for_status(self, status):
        if status not in self.STATUSES:
            raise ValueError(
                f"Invalid status: {status}. "
                f"Allowed: {', '.join(self.STATUSES)}"
            )

        return self.NEXT_ACTIONS[status]

    def add_customer(
        self,
        name,
        phone="",
        email="",
        address="",
        notes="",
    ):
        name = name.strip()

        if not name:
            raise ValueError("Customer name is required.")

        with self._connect() as db:
            cursor = db.execute(
                """
                INSERT INTO customers
                (name, phone, email, address, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    phone.strip(),
                    email.strip(),
                    address.strip(),
                    notes.strip(),
                    datetime.now().astimezone().isoformat(),
                ),
            )

            db.commit()

            return Customer(
                id=cursor.lastrowid,
                name=name,
                phone=phone.strip(),
                email=email.strip(),
                address=address.strip(),
                notes=notes.strip(),
            )

    def update_customer(self, customer_id, field, value):
        field = field.strip().lower()
        value = value.strip()

        if field not in self.CUSTOMER_FIELDS:
            raise ValueError(
                f"Invalid customer field: {field}. "
                f"Allowed: {', '.join(sorted(self.CUSTOMER_FIELDS))}"
            )

        if not value:
            raise ValueError("Customer value is required.")

        with self._connect() as db:
            cursor = db.execute(
                f"""
                UPDATE customers
                SET {field} = ?
                WHERE id = ?
                """,
                (value, customer_id),
            )

            db.commit()

            if cursor.rowcount != 1:
                return None

            row = db.execute(
                """
                SELECT id, name, phone, email, address, notes
                FROM customers
                WHERE id = ?
                """,
                (customer_id,),
            ).fetchone()

        return Customer(*row) if row else None

    def update_customer_by_name(self, name, field, value):
        customer = self.find_customer(name)

        if not customer:
            return None

        return self.update_customer(
            customer.id,
            field,
            value,
        )

    def add_lead(
        self,
        customer_id,
        project_type,
        description="",
        status="NEW",
        next_action="",
    ):
        project_type = project_type.strip()

        if not project_type:
            raise ValueError("Project type is required.")

        if status not in self.STATUSES:
            raise ValueError(
                f"Invalid status: {status}. "
                f"Allowed: {', '.join(self.STATUSES)}"
            )

        if not next_action:
            next_action = self._next_action_for_status(status)

        with self._connect() as db:
            cursor = db.execute(
                """
                INSERT INTO leads
                (customer_id, project_type, description, status,
                 next_action, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    customer_id,
                    project_type,
                    description.strip(),
                    status,
                    next_action.strip(),
                    datetime.now().astimezone().isoformat(),
                ),
            )

            db.commit()

            return Lead(
                id=cursor.lastrowid,
                customer_id=customer_id,
                project_type=project_type,
                description=description,
                status=status,
                next_action=next_action,
            )

    def list_customers(self):
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT id, name, phone, email, address, notes
                FROM customers
                ORDER BY id DESC
                """
            ).fetchall()

        return [Customer(*row) for row in rows]

    def list_leads(self, status=None):
        query = """
            SELECT
                leads.id,
                leads.customer_id,
                customers.name,
                leads.project_type,
                leads.description,
                leads.status,
                leads.next_action
            FROM leads
            JOIN customers
                ON customers.id = leads.customer_id
        """

        params = []

        if status:
            query += " WHERE leads.status = ?"
            params.append(status)

        query += " ORDER BY leads.id DESC"

        with self._connect() as db:
            return db.execute(query, params).fetchall()

    def find_lead(self, lead_id):
        with self._connect() as db:
            row = db.execute(
                """
                SELECT
                    leads.id,
                    leads.customer_id,
                    customers.name,
                    leads.project_type,
                    leads.description,
                    leads.status,
                    leads.next_action
                FROM leads
                JOIN customers
                    ON customers.id = leads.customer_id
                WHERE leads.id = ?
                """,
                (lead_id,),
            ).fetchone()

        return row

    def find_customer(self, name):
        with self._connect() as db:
            row = db.execute(
                """
                SELECT id, name, phone, email, address, notes
                FROM customers
                WHERE name LIKE ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (f"%{name.strip()}%",),
            ).fetchone()

        return Customer(*row) if row else None

    def find_leads_for_customer(self, customer_id):
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT
                    leads.id,
                    leads.customer_id,
                    customers.name,
                    leads.project_type,
                    leads.description,
                    leads.status,
                    leads.next_action
                FROM leads
                JOIN customers
                    ON customers.id = leads.customer_id
                WHERE leads.customer_id = ?
                ORDER BY leads.id DESC
                """,
                (customer_id,),
            ).fetchall()

        return rows

    def find_leads_needing_follow_up(self):
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT
                    leads.id,
                    leads.customer_id,
                    customers.name,
                    leads.project_type,
                    leads.description,
                    leads.status,
                    leads.next_action
                FROM leads
                JOIN customers
                    ON customers.id = leads.customer_id
                WHERE leads.status IN (
                    'NEW',
                    'CONTACTED',
                    'ESTIMATE_NEEDED',
                    'ESTIMATE_SENT',
                    'FOLLOW_UP'
                )
                ORDER BY leads.id DESC
                """
            ).fetchall()

        return rows

    def update_lead_status(self, lead_id, status):
        next_action = self._next_action_for_status(status)

        with self._connect() as db:
            cursor = db.execute(
                """
                UPDATE leads
                SET status = ?, next_action = ?
                WHERE id = ?
                """,
                (status, next_action, lead_id),
            )

            db.commit()

            return cursor.rowcount == 1
