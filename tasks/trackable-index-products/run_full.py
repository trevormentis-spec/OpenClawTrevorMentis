#!/usr/bin/env python3
"""Run full 4-region pipeline."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import grain_supply_monitor as gsm
from datetime import date

td = date(2026, 6, 1)
gsm.run_pipeline(target_date=td, output_path="outputs/gsm-4regions-2026-06-01.json")
