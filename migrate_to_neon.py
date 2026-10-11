import os
import sqlite3
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor


# ============================================================
# CONFIGURATION
# ============================================================

SQLITE_DB = "umeed.db"

NEON_URL = os.environ.get("NEON_DATABASE_URL")

if not NEON_URL:
    raise RuntimeError(
        "NEON_DATABASE_URL is not set in this terminal."
    )

# Convert postgres:// to postgresql:// if necessary
if NEON_URL.startswith("postgres://"):
    NEON_URL = NEON_URL.replace(
        "postgres://",
        "postgresql://",
        1
    )


# ============================================================
# HELPERS
# ============================================================

def parse_datetime(value):
    """Convert SQLite datetime values into Python datetime."""

    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    value = str(value).strip()

    if not value:
        return None

    # SQLite usually stores these as:
    # 2026-10-11 12:34:56.123456
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        pass

    for fmt in (
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass

    raise ValueError(
        f"Cannot parse datetime: {value}"
    )


def get_sqlite_rows(connection, table_name):
    """Read an entire SQLite table as dictionaries."""

    cursor = connection.execute(
        f"SELECT * FROM {table_name}"
    )

    columns = [
        description[0]
        for description in cursor.description
    ]

    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


# ============================================================
# START
# ============================================================

print()
print("=" * 65)
print("UMEED DATA MIGRATION")
print("SQLite -> Neon PostgreSQL")
print("=" * 65)
print()


# ============================================================
# OPEN SQLITE
# ============================================================

if not os.path.exists(SQLITE_DB):
    raise FileNotFoundError(
        f"Could not find {SQLITE_DB}"
    )

print("Opening local SQLite database...")

sqlite_connection = sqlite3.connect(
    SQLITE_DB
)

print("SQLite opened successfully.")
print()


# ============================================================
# READ LOCAL DATA
# ============================================================

users = get_sqlite_rows(
    sqlite_connection,
    "users"
)

ngos = get_sqlite_rows(
    sqlite_connection,
    "ngos"
)

campaigns = get_sqlite_rows(
    sqlite_connection,
    "campaigns"
)

donations = get_sqlite_rows(
    sqlite_connection,
    "donations"
)

donation_items = get_sqlite_rows(
    sqlite_connection,
    "donation_items"
)

donation_events = get_sqlite_rows(
    sqlite_connection,
    "donation_events"
)


print("LOCAL DATA FOUND")
print("-" * 65)
print(f"Users:           {len(users)}")
print(f"NGOs:            {len(ngos)}")
print(f"Campaigns:       {len(campaigns)}")
print(f"Donations:       {len(donations)}")
print(f"Donation items:  {len(donation_items)}")
print(f"Donation events: {len(donation_events)}")
print()


# ============================================================
# CONNECT TO NEON
# ============================================================

print("Connecting to Neon PostgreSQL...")

neon_connection = psycopg2.connect(
    NEON_URL
)

neon_connection.autocommit = False

print("Neon connection successful.")
print()


# ============================================================
# ID MAPS
#
# Local IDs and Neon IDs do not have to be the same.
# These dictionaries keep all relationships correct.
# ============================================================

user_id_map = {}
ngo_id_map = {}
campaign_id_map = {}
donation_id_map = {}


try:

    with neon_connection.cursor(
        cursor_factory=RealDictCursor
    ) as cursor:

        # ====================================================
        # 1. MIGRATE NGOs
        # ====================================================

        print("=" * 65)
        print("1. MIGRATING NGOs")
        print("=" * 65)

        for local_ngo in ngos:

            # Look for an NGO already existing in Neon.
            cursor.execute(
                """
                SELECT id
                FROM ngos
                WHERE name = %s
                  AND email = %s
                LIMIT 1
                """,
                (
                    local_ngo["name"],
                    local_ngo["email"],
                )
            )

            existing = cursor.fetchone()

            if existing:

                neon_ngo_id = existing["id"]

                print(
                    f"Already exists: "
                    f"{local_ngo['name']} "
                    f"(Neon ID {neon_ngo_id})"
                )

            else:

                cursor.execute(
                    """
                    INSERT INTO ngos
                    (
                        name,
                        email,
                        location,
                        description,
                        status,
                        created_at
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    RETURNING id
                    """,
                    (
                        local_ngo["name"],
                        local_ngo["email"],
                        local_ngo["location"] or "",
                        local_ngo["description"] or "",
                        local_ngo["status"],
                        parse_datetime(
                            local_ngo["created_at"]
                        ),
                    )
                )

                neon_ngo_id = cursor.fetchone()["id"]

                print(
                    f"Added NGO: "
                    f"{local_ngo['name']} "
                    f"(Neon ID {neon_ngo_id})"
                )

            ngo_id_map[
                local_ngo["id"]
            ] = neon_ngo_id

        print()


        # ====================================================
        # 2. FIND EXISTING NEON USERS
        # ====================================================

        print("=" * 65)
        print("2. PREPARING USERS")
        print("=" * 65)

        cursor.execute(
            """
            SELECT id, email, role
            FROM users
            """
        )

        neon_users = cursor.fetchall()

        neon_users_by_email = {
            row["email"].strip().lower(): row
            for row in neon_users
        }

        # Find the existing production admin.
        neon_admin = None

        for row in neon_users:
            if row["role"] == "admin":
                neon_admin = row
                break

        if neon_admin:
            print(
                "Existing Neon admin found:"
                f" {neon_admin['email']}"
            )
        else:
            raise RuntimeError(
                "No admin account exists in Neon. "
                "The production admin should exist before "
                "running this migration."
            )

        print()


        # ====================================================
        # 3. MIGRATE USERS
        # ====================================================

        print("=" * 65)
        print("3. MIGRATING USERS")
        print("=" * 65)

        for local_user in users:

            local_email = (
                local_user["email"]
                .strip()
                .lower()
            )

            local_role = local_user["role"]

            # ------------------------------------------------
            # ADMIN USERS
            #
            # Do NOT create another admin.
            # Map local admin to the production admin.
            # ------------------------------------------------

            if local_role == "admin":

                user_id_map[
                    local_user["id"]
                ] = neon_admin["id"]

                print(
                    f"Mapped local admin "
                    f"{local_email} -> "
                    f"Neon admin "
                    f"{neon_admin['email']}"
                )

                continue

            # ------------------------------------------------
            # CHECK WHETHER NORMAL USER ALREADY EXISTS
            # ------------------------------------------------

            existing_user = neon_users_by_email.get(
                local_email
            )

            if existing_user:

                neon_user_id = existing_user["id"]

                print(
                    f"Already exists: "
                    f"{local_email} "
                    f"(Neon ID {neon_user_id})"
                )

                user_id_map[
                    local_user["id"]
                ] = neon_user_id

                continue

            # ------------------------------------------------
            # MAP NGO
            # ------------------------------------------------

            neon_ngo_id = None

            if local_user["ngo_id"] is not None:

                neon_ngo_id = ngo_id_map.get(
                    local_user["ngo_id"]
                )

                if neon_ngo_id is None:
                    raise RuntimeError(
                        f"Could not map NGO ID "
                        f"{local_user['ngo_id']} "
                        f"for user {local_email}"
                    )

            # ------------------------------------------------
            # INSERT USER
            # ------------------------------------------------

            cursor.execute(
                """
                INSERT INTO users
                (
                    name,
                    email,
                    password_hash,
                    role,
                    ngo_id,
                    created_at
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                RETURNING id
                """,
                (
                    local_user["name"],
                    local_email,
                    local_user["password_hash"],
                    local_user["role"],
                    neon_ngo_id,
                    parse_datetime(
                        local_user["created_at"]
                    ),
                )
            )

            neon_user_id = cursor.fetchone()["id"]

            user_id_map[
                local_user["id"]
            ] = neon_user_id

            print(
                f"Added user: "
                f"{local_email} "
                f"({local_role}) "
                f"(Neon ID {neon_user_id})"
            )

        print()


        # ====================================================
        # 4. MIGRATE CAMPAIGNS
        # ====================================================

        print("=" * 65)
        print("4. MIGRATING CAMPAIGNS")
        print("=" * 65)

        for local_campaign in campaigns:

            local_ngo_id = local_campaign["ngo_id"]

            neon_ngo_id = ngo_id_map.get(
                local_ngo_id
            )

            if neon_ngo_id is None:
                raise RuntimeError(
                    f"Could not map NGO "
                    f"{local_ngo_id} "
                    f"for campaign "
                    f"{local_campaign['title']}"
                )

            # Check if campaign already exists.
            cursor.execute(
                """
                SELECT id
                FROM campaigns
                WHERE title = %s
                  AND ngo_id = %s
                LIMIT 1
                """,
                (
                    local_campaign["title"],
                    neon_ngo_id,
                )
            )

            existing_campaign = cursor.fetchone()

            if existing_campaign:

                neon_campaign_id = (
                    existing_campaign["id"]
                )

                print(
                    f"Already exists: "
                    f"{local_campaign['title']} "
                    f"(Neon ID {neon_campaign_id})"
                )

            else:

                cursor.execute(
                    """
                    INSERT INTO campaigns
                    (
                        title,
                        emergency_type,
                        location,
                        description,
                        required_items,
                        status,
                        last_verified_at,
                        created_at,
                        ngo_id
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    RETURNING id
                    """,
                    (
                        local_campaign["title"],
                        local_campaign["emergency_type"],
                        local_campaign["location"],
                        local_campaign["description"],
                        local_campaign["required_items"],
                        local_campaign["status"],
                        parse_datetime(
                            local_campaign[
                                "last_verified_at"
                            ]
                        ),
                        parse_datetime(
                            local_campaign["created_at"]
                        ),
                        neon_ngo_id,
                    )
                )

                neon_campaign_id = (
                    cursor.fetchone()["id"]
                )

                print(
                    f"Added campaign: "
                    f"{local_campaign['title']} "
                    f"(Neon ID {neon_campaign_id})"
                )

            campaign_id_map[
                local_campaign["id"]
            ] = neon_campaign_id

        print()


        # ====================================================
        # 5. MIGRATE DONATIONS
        # ====================================================

        print("=" * 65)
        print("5. MIGRATING DONATIONS")
        print("=" * 65)

        for local_donation in donations:

            local_code = local_donation["code"]

            # ------------------------------------------------
            # Check duplicate donation by QR/code.
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT id
                FROM donations
                WHERE code = %s
                LIMIT 1
                """,
                (local_code,)
            )

            existing_donation = cursor.fetchone()

            if existing_donation:

                neon_donation_id = (
                    existing_donation["id"]
                )

                print(
                    f"Already exists donation: "
                    f"{local_code} "
                    f"(Neon ID {neon_donation_id})"
                )

            else:

                # ------------------------------------------------
                # Donor
                # ------------------------------------------------

                neon_donor_id = None

                if local_donation["donor_id"] is not None:

                    neon_donor_id = user_id_map.get(
                        local_donation["donor_id"]
                    )

                    if neon_donor_id is None:
                        raise RuntimeError(
                            f"Could not map donor "
                            f"{local_donation['donor_id']} "
                            f"for donation "
                            f"{local_code}"
                        )

                # ------------------------------------------------
                # Created by
                # ------------------------------------------------

                neon_created_by_id = user_id_map.get(
                    local_donation["created_by_id"]
                )

                if neon_created_by_id is None:
                    raise RuntimeError(
                        f"Could not map created_by_id "
                        f"{local_donation['created_by_id']} "
                        f"for donation "
                        f"{local_code}"
                    )

                # ------------------------------------------------
                # NGO
                # ------------------------------------------------

                neon_ngo_id = ngo_id_map.get(
                    local_donation["ngo_id"]
                )

                if neon_ngo_id is None:
                    raise RuntimeError(
                        f"Could not map NGO "
                        f"{local_donation['ngo_id']} "
                        f"for donation "
                        f"{local_code}"
                    )

                # ------------------------------------------------
                # Campaign
                # ------------------------------------------------

                neon_campaign_id = None

                if local_donation["campaign_id"] is not None:

                    neon_campaign_id = campaign_id_map.get(
                        local_donation["campaign_id"]
                    )

                    if neon_campaign_id is None:
                        raise RuntimeError(
                            f"Could not map campaign "
                            f"{local_donation['campaign_id']} "
                            f"for donation "
                            f"{local_code}"
                        )

                # ------------------------------------------------
                # INSERT DONATION
                # ------------------------------------------------

                cursor.execute(
                    """
                    INSERT INTO donations
                    (
                        code,
                        donor_id,
                        created_by_id,
                        ngo_id,
                        campaign_id,
                        source,
                        status,
                        delivery_method,
                        notes,
                        created_at,
                        received_at
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    RETURNING id
                    """,
                    (
                        local_donation["code"],
                        neon_donor_id,
                        neon_created_by_id,
                        neon_ngo_id,
                        neon_campaign_id,
                        local_donation["source"],
                        local_donation["status"],
                        local_donation["delivery_method"],
                        local_donation["notes"] or "",
                        parse_datetime(
                            local_donation["created_at"]
                        ),
                        parse_datetime(
                            local_donation["received_at"]
                        ),
                    )
                )

                neon_donation_id = (
                    cursor.fetchone()["id"]
                )

                print(
                    f"Added donation: "
                    f"{local_code} "
                    f"(Neon ID {neon_donation_id})"
                )

            donation_id_map[
                local_donation["id"]
            ] = neon_donation_id

        print()


        # ====================================================
        # 6. MIGRATE DONATION ITEMS
        # ====================================================

        print("=" * 65)
        print("6. MIGRATING DONATION ITEMS")
        print("=" * 65)

        for local_item in donation_items:

            neon_donation_id = donation_id_map.get(
                local_item["donation_id"]
            )

            if neon_donation_id is None:
                raise RuntimeError(
                    f"Could not map donation "
                    f"{local_item['donation_id']} "
                    f"for donation item"
                )

            # Check for existing item.
            cursor.execute(
                """
                SELECT id
                FROM donation_items
                WHERE donation_id = %s
                  AND item_name = %s
                LIMIT 1
                """,
                (
                    neon_donation_id,
                    local_item["item_name"],
                )
            )

            existing_item = cursor.fetchone()

            if existing_item:

                print(
                    f"Already exists item: "
                    f"{local_item['item_name']}"
                )

            else:

                cursor.execute(
                    """
                    INSERT INTO donation_items
                    (
                        donation_id,
                        item_name,
                        declared_qty,
                        received_qty,
                        accepted_qty,
                        condition,
                        rejection_reason
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        neon_donation_id,
                        local_item["item_name"],
                        local_item["declared_qty"],
                        local_item["received_qty"],
                        local_item["accepted_qty"],
                        local_item["condition"],
                        local_item["rejection_reason"] or "",
                    )
                )

                print(
                    f"Added item: "
                    f"{local_item['item_name']}"
                )

        print()


        # ====================================================
        # 7. MIGRATE DONATION EVENTS
        # ====================================================

        print("=" * 65)
        print("7. MIGRATING DONATION EVENTS")
        print("=" * 65)

        for local_event in donation_events:

            neon_donation_id = donation_id_map.get(
                local_event["donation_id"]
            )

            if neon_donation_id is None:
                raise RuntimeError(
                    f"Could not map donation "
                    f"{local_event['donation_id']} "
                    f"for event"
                )

            neon_user_id = None

            if local_event["user_id"] is not None:

                neon_user_id = user_id_map.get(
                    local_event["user_id"]
                )

                if neon_user_id is None:
                    raise RuntimeError(
                        f"Could not map event user "
                        f"{local_event['user_id']}"
                    )

            event_datetime = parse_datetime(
                local_event["created_at"]
            )

            # Check for duplicate event.
            cursor.execute(
                """
                SELECT id
                FROM donation_events
                WHERE donation_id = %s
                  AND event_type = %s
                  AND created_at = %s
                LIMIT 1
                """,
                (
                    neon_donation_id,
                    local_event["event_type"],
                    event_datetime,
                )
            )

            existing_event = cursor.fetchone()

            if existing_event:

                print(
                    f"Already exists event: "
                    f"{local_event['event_type']}"
                )

            else:

                cursor.execute(
                    """
                    INSERT INTO donation_events
                    (
                        donation_id,
                        user_id,
                        event_type,
                        note,
                        created_at
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        neon_donation_id,
                        neon_user_id,
                        local_event["event_type"],
                        local_event["note"] or "",
                        event_datetime,
                    )
                )

                print(
                    f"Added event: "
                    f"{local_event['event_type']}"
                )

        print()


    # ========================================================
    # COMMIT
    # ========================================================

    print("=" * 65)
    print("COMMITTING MIGRATION")
    print("=" * 65)

    neon_connection.commit()

    print("Migration committed successfully.")
    print()


except Exception as error:

    print()
    print("=" * 65)
    print("MIGRATION FAILED")
    print("=" * 65)
    print()
    print(error)
    print()
    print("Rolling back all Neon changes...")
    neon_connection.rollback()
    print("Rollback complete.")
    print()

    raise


finally:

    sqlite_connection.close()
    neon_connection.close()


# ============================================================
# FINAL CHECK
# ============================================================

print("=" * 65)
print("MIGRATION COMPLETE")
print("=" * 65)
print()

# Reconnect only for verification
verify_connection = psycopg2.connect(
    NEON_URL
)

try:

    with verify_connection.cursor() as cursor:

        tables = [
            "users",
            "ngos",
            "campaigns",
            "donations",
            "donation_items",
            "donation_events",
        ]

        for table in tables:

            cursor.execute(
                f"SELECT COUNT(*) FROM {table}"
            )

            count = cursor.fetchone()[0]

            print(
                f"{table}: {count}"
            )

finally:

    verify_connection.close()

print()
print("Your local umeed.db was NOT modified.")
print("Your Neon database now contains the migrated data.")
print()