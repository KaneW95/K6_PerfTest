import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine
from sqlalchemy import text

def fix():
    print("Fixing database schema...")
    try:
        with engine.connect() as conn:
            # Modify column to LONGTEXT (MySQL)
            try:
                print("Executing: ALTER TABLE test_executions MODIFY logs LONGTEXT")
                conn.execute(text("ALTER TABLE test_executions MODIFY logs LONGTEXT"))
                conn.commit()
                print("Success: logs column modified to LONGTEXT.")
            except Exception as e:
                print(f"Error executing ALTER: {e}")
                # Try simple TEXT if LONGTEXT fails? No, LONGTEXT is standard in mysql.
    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    fix()
