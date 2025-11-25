import os

def get_db_url():
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.strip().startswith('DATABASE_URL='):
                    print(line.strip().split('=', 1)[1])
                    return
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_db_url()
