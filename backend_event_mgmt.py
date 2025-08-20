import psycopg2
import pandas as pd
from typing import List, Dict, Any
import numpy as np

# Database connection parameters
DB_PARAMS = {
    "host": "localhost",
    "database": "event_mgmt_db",
    "user": "postgres",
    "password": "seemaxime@30190"
}

def get_db_connection():
    """Establishes and returns a new database connection."""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        return conn
    except psycopg2.Error as e:
        print(f"Database connection failed: {e}")
        return None

# --- CRUD Operations ---

def create_event(user_id, event_name, event_date, event_time, location, description):
    """Creates a new event."""
    conn, cur = None, None
    try:
        conn = get_db_connection()
        if not conn: return False
        cur = conn.cursor()
        query = "INSERT INTO events (user_id, event_name, event_date, event_time, location, description) VALUES (%s, %s, %s, %s, %s, %s);"
        cur.execute(query, (user_id, event_name, event_date, event_time, location, description))
        conn.commit()
        return True
    except (Exception, psycopg2.Error) as error:
        print(f"Error creating event: {error}")
        if conn: conn.rollback()
        return False
    finally:
        if cur: cur.close()
        if conn: conn.close()

def create_ticket(event_id, ticket_type, price, quantity):
    """Creates a new ticket type for an event."""
    conn, cur = None, None
    try:
        event_id = int(event_id)
        quantity = int(quantity)

        conn = get_db_connection()
        if not conn: return False
        cur = conn.cursor()
        query = "INSERT INTO tickets (event_id, ticket_type, price, quantity_available) VALUES (%s, %s, %s, %s);"
        cur.execute(query, (event_id, ticket_type, price, quantity))
        conn.commit()
        return True
    except (Exception, psycopg2.Error) as error:
        print(f"Error creating ticket: {error}")
        if conn: conn.rollback()
        return False
    finally:
        if cur: cur.close()
        if conn: conn.close()

def register_attendee(ticket_id, attendee_name, attendee_email):
    """Registers a new attendee for an event."""
    conn, cur = None, None
    try:
        ticket_id = int(ticket_id)
        
        conn = get_db_connection()
        if not conn: return False
        cur = conn.cursor()
        query = "INSERT INTO attendees (ticket_id, attendee_name, attendee_email) VALUES (%s, %s, %s);"
        cur.execute(query, (ticket_id, attendee_name, attendee_email))
        conn.commit()
        return True
    except (Exception, psycopg2.Error) as error:
        print(f"Error registering attendee: {error}")
        if conn: conn.rollback()
        return False
    finally:
        if cur: cur.close()
        if conn: conn.close()

# --- READ Operations ---

def get_user_events(user_id):
    """Fetches all events created by a user."""
    conn, cur = None, None
    try:
        conn = get_db_connection()
        if not conn: return pd.DataFrame()
        cur = conn.cursor()
        query = "SELECT event_id, event_name, event_date, event_time, location FROM events WHERE user_id = %s ORDER BY event_date DESC;"
        cur.execute(query, (user_id,))
        data = cur.fetchall()
        df = pd.DataFrame(data, columns=[desc[0] for desc in cur.description])
        return df
    except (Exception, psycopg2.Error) as error:
        print(f"Error fetching events: {error}")
        return pd.DataFrame()
    finally:
        if cur: cur.close()
        if conn: conn.close()

def get_event_tickets(event_id):
    """Fetches all ticket types for a specific event."""
    conn, cur = None, None
    try:
        event_id = int(event_id)
        
        conn = get_db_connection()
        if not conn: return pd.DataFrame()
        cur = conn.cursor()
        query = "SELECT ticket_id, ticket_type, price, quantity_available FROM tickets WHERE event_id = %s;"
        cur.execute(query, (event_id,))
        data = cur.fetchall()
        df = pd.DataFrame(data, columns=[desc[0] for desc in cur.description])
        return df
    except (Exception, psycopg2.Error) as error:
        print(f"Error fetching tickets: {error}")
        return pd.DataFrame()
    finally:
        if cur: cur.close()
        if conn: conn.close()

def get_attendees_by_ticket_type(event_id, ticket_type):
    """Fetches attendees filtered by event and ticket type."""
    conn, cur = None, None
    try:
        event_id = int(event_id)
        
        conn = get_db_connection()
        if not conn: return pd.DataFrame()
        cur = conn.cursor()
        query = """
        SELECT a.attendee_name, a.attendee_email, t.ticket_type, a.registration_date
        FROM attendees a
        JOIN tickets t ON a.ticket_id = t.ticket_id
        WHERE t.event_id = %s AND t.ticket_type = %s;
        """
        cur.execute(query, (event_id, ticket_type))
        data = cur.fetchall()
        df = pd.DataFrame(data, columns=[desc[0] for desc in cur.description])
        return df
    except (Exception, psycopg2.Error) as error:
        print(f"Error fetching attendees: {error}")
        return pd.DataFrame()
    finally:
        if cur: cur.close()
        if conn: conn.close()

def get_event_insights(event_id):
    """Provides business insights for a single event."""
    conn, cur = None, None
    try:
        event_id = int(event_id)

        conn = get_db_connection()
        if not conn: return {}
        cur = conn.cursor()
        
        query = """
        SELECT 
            COUNT(a.attendee_id) AS total_attendees,
            SUM(t.price) AS total_revenue,
            MIN(t.price) AS min_ticket_price,
            MAX(t.price) AS max_ticket_price,
            AVG(t.price) AS avg_ticket_price,
            (SELECT SUM(quantity_available) FROM tickets WHERE event_id = %s) AS total_tickets_available
        FROM attendees a
        JOIN tickets t ON a.ticket_id = t.ticket_id
        WHERE t.event_id = %s;
        """
        cur.execute(query, (event_id, event_id))
        result = cur.fetchone()

        if result:
            col_names = [desc[0] for desc in cur.description]
            return dict(zip(col_names, result))
        return {}
    except (Exception, psycopg2.Error) as error:
        print(f"Error fetching insights: {error}")
        return {}
    finally:
        if cur: cur.close()
        if conn: conn.close()

def get_event_tickets_for_registration(event_id):
    """Fetches tickets for attendee registration dropdowns."""
    conn, cur = None, None
    try:
        event_id = int(event_id)

        conn = get_db_connection()
        if not conn: return []
        cur = conn.cursor()
        query = "SELECT ticket_id, ticket_type, price FROM tickets WHERE event_id = %s;"
        cur.execute(query, (event_id,))
        data = cur.fetchall()
        return data
    except (Exception, psycopg2.Error) as error:
        print(f"Error fetching tickets for registration: {error}")
        return []
    finally:
        if cur: cur.close()
        if conn: conn.close()

def get_or_create_user(name, email, organization):
    """Fetches an existing user or creates a new one."""
    conn, cur = None, None
    try:
        conn = get_db_connection()
        if not conn: return None
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM users WHERE email = %s;", (email,))
        user = cur.fetchone()
        if user:
            return user[0]
        else:
            cur.execute("INSERT INTO users (name, email, organization) VALUES (%s, %s, %s) RETURNING user_id;", (name, email, organization))
            conn.commit()
            new_user_id = cur.fetchone()[0]
            return new_user_id
    except (Exception, psycopg2.Error) as error:
        print(f"Error getting/creating user: {error}")
        if conn: conn.rollback()
        return None
    finally:
        if cur: cur.close()
        if conn: conn.close()
