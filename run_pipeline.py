import logging
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_script(script_path):
    logging.info(f"Running {script_path.name}...")
    result = subprocess.run([sys.executable, str(script_path)], cwd=PROJECT_ROOT)
    if result.returncode != 0:
        logging.error(f"Script {script_path.name} failed with return code {result.returncode}")
        sys.exit(1)
    logging.info(f"Completed {script_path.name}")

def main():
    logging.info("Starting Data Pipeline")
    
    scripts = [
        PROJECT_ROOT / 'src' / 'ingestion' / 'generate_mock_data.py',
        PROJECT_ROOT / 'src' / 'cleaning' / 'clean_data.py',
        PROJECT_ROOT / 'src' / 'loading' / 'load_data.py',
        PROJECT_ROOT / 'src' / 'alerts' / 'generate_alerts.py'
    ]
    
    for script in scripts:
        run_script(script)
        
    logging.info("Data Pipeline executed successfully.")

if __name__ == "__main__":
    main()
