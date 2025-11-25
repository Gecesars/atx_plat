import subprocess
import os

env = os.environ.copy()
env['PGPASSWORD'] = 'postgres'

cmd = [
    'pg_dump',
    '-h', '127.0.0.1',
    '-p', '5432',
    '-U', 'postgres',
    '-d', 'atxcover',
    '-f', 'backup_20251125.sql'
]

try:
    subprocess.run(cmd, env=env, check=True)
    print("Backup successful.")
except subprocess.CalledProcessError as e:
    print(f"Backup failed: {e}")
