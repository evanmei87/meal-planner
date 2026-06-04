import pytest
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tools.calculate_tdee import calculate_tdee

def test_calculate_tdee_male():
    # Height: 175cm, Weight: 70kg, Age: 30, Gender: male, Activity factor: 1.55 (default)
    # BMR = 10 * 70 + 6.25 * 175 - 5 * 30 + 5 = 700 + 1093.75 - 150 + 5 = 1648.75
    # TDEE = 1648.75 * 1.55 = 2555.5625 -> rounded: 2556
    tdee = calculate_tdee(height_cm=175, weight_kg=70, age=30, gender='male')
    assert tdee == 2556

def test_calculate_tdee_female():
    # Height: 165cm, Weight: 60kg, Age: 25, Gender: female, Activity factor: 1.2
    # BMR = 10 * 60 + 6.25 * 165 - 5 * 25 - 161 = 600 + 1031.25 - 125 - 161 = 1345.25
    # TDEE = 1345.25 * 1.2 = 1614.3 -> rounded: 1614
    tdee = calculate_tdee(height_cm=165, weight_kg=60, age=25, gender='female', activity_factor=1.2)
    assert tdee == 1614

def test_calculate_tdee_with_running_adjustment(monkeypatch):
    # Set environment variables for long run
    monkeypatch.setenv('RUNNING_SCHEDULE', 'long_run')
    monkeypatch.setenv('LONG_RUN_DISTANCE', '10')
    
    # BMR for Male: 1648.75
    # TDEE = 1648.75 * 1.55 = 2555.5625
    # running_burn = 10 * 83 = 830
    # Expected TDEE = 2555.5625 + 830 = 3385.5625 -> rounded: 3386
    tdee = calculate_tdee(height_cm=175, weight_kg=70, age=30, gender='male')
    assert tdee == 3386
