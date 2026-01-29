import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine
from sqlalchemy import text

def migrate():
    print("Migrating database schema...")
    try:
        with engine.connect() as conn:
            # Add data_file column to test_configs
            try:
                print("Executing: ALTER TABLE test_configs ADD COLUMN data_file VARCHAR(255) COMMENT '数据文件路径'")
                conn.execute(text("ALTER TABLE test_configs ADD COLUMN data_file VARCHAR(255) COMMENT '数据文件路径'"))
                conn.commit()
                print("Success: data_file column added.")
            except Exception as e:
                print(f"Error executing ALTER (might already exist): {e}")
                
    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    migrate()
