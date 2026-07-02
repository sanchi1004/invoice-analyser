import psycopg2

passwords = [
    "",
    "postgres",
    "admin",
    "root",
    "1234",
    "123456",
    "postgres123",
    "password"
]

for password in passwords:

    try:

        conn = psycopg2.connect(
            host="localhost",
            user="postgres",
            password=password,
            dbname="postgres"
        )

        print("="*60)
        print("SUCCESS!")
        print("Your PostgreSQL password is:")
        print(password)
        print("="*60)

        conn.close()
        break

    except Exception as e:

        print(f"Failed: {password}")