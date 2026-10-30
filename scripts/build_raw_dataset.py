"""
Entrypoint script for generating and building raw civic complaints datasets for SIH 2026.
Calls generate_synthetic_data.
"""

import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.generate_synthetic_data import main

if __name__ == "__main__":
    main()
