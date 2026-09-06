"""
Dummy User Generator Script

Generates realistic user data with properly hashed passwords (Argon2)
for testing and development purposes.

Usage:
    python scripts/seed/generate_dummy_users.py --count 50 --start-id 7
"""

import random
import argparse
from datetime import datetime, timedelta, timezone
from faker import Faker
from passlib.context import CryptContext

fake = Faker()
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def parse_args():
    parser = argparse.ArgumentParser(description="Generate dummy users")
    parser.add_argument("--count", type=int, default=50,
                        help="Number of users to generate (default: 50)")
    parser.add_argument("--start-id", type=int, default=1,
                        help="Starting user ID (default: 1)")
    parser.add_argument("--output", default="insert_users.sql",
                        help="Output SQL file (default: insert_users.sql)")
    parser.add_argument("--admin-count", type=int, default=2,
                        help="Number of admin users (default: 2)")
    return parser.parse_args()


def generate_password_hash():
    """Generate a realistic password and hash it with Argon2."""
    plain_password = fake.password(length=12, special_chars=True, digits=True)
    hashed = pwd_context.hash(plain_password)
    return hashed, plain_password


def generate_users(count: int, start_id: int, admin_count: int, output_file: str):
    users_sql = []
    credentials_log = []  # Track plain passwords for testing
    
    # Decide which users will be admins (first N users)
    admin_indices = set(range(admin_count))
    
    for i in range(count):
        user_id = start_id + i
        first_name = fake.first_name().replace("'", "''")
        last_name = fake.last_name().replace("'", "''")
        email = fake.unique.email()
        
        # Random dates within the last 2 years
        created_at = fake.date_time_between(
            start_date="-2y", 
            end_date="now"
        )
        # Updated at is always after or equal to created_at
        updated_at = created_at + timedelta(days=random.randint(0, 30))
        
        # Generate hashed password
        hashed_password, plain_password = generate_password_hash()
        
        # Assign admin status
        is_admin = "true" if i in admin_indices else "false"
        
        # Format dates for PostgreSQL
        created_str = created_at.strftime("%Y-%m-%d %H:%M:%S")
        updated_str = updated_at.strftime("%Y-%m-%d %H:%M:%S")
        
        sql = (
            f"INSERT INTO users (id, first_name, last_name, email, created_at, updated_at, "
            f"password_hash, is_admin) VALUES ({user_id}, '{first_name}', '{last_name}', "
            f"'{email}', '{created_str}', '{updated_str}', '{hashed_password}', {is_admin});"
        )
        users_sql.append(sql)
        
        # Log credentials for testing
        credentials_log.append({
            "id": user_id,
            "email": email,
            "password": plain_password,
            "is_admin": is_admin == "true"
        })
    
    # Write SQL to file
    with open(output_file, "w") as f:
        f.write("\n".join(users_sql))
    
    # Write credentials to a separate file for easy testing
    credentials_file = output_file.replace(".sql", "_credentials.txt")
    with open(credentials_file, "w") as f:
        f.write("=" * 60 + "\n")
        f.write("DUMMY USER CREDENTIALS (DO NOT COMMIT TO GIT!)\n")
        f.write("=" * 60 + "\n\n")
        for cred in credentials_log:
            role = "👑 ADMIN" if cred["is_admin"] else "👤 USER"
            f.write(f"{role} | ID: {cred['id']}\n")
            f.write(f"   Email:    {cred['email']}\n")
            f.write(f"   Password: {cred['password']}\n\n")
    
    print(f"Generated {count} users in {output_file}")
    print(f"Credentials saved to {credentials_file}")
    print(f"Admin users: {admin_count}")
    print(f"IDs: {start_id} → {start_id + count - 1}")
    print(f"\nIMPORTANT: Add '{credentials_file}' to .gitignore!")


if __name__ == "__main__":
    args = parse_args()
    generate_users(args.count, args.start_id, args.admin_count, args.output)