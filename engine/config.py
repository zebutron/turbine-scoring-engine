"""
Load scoring configuration from local JSON files or Google Sheets.

Config files live in configs/ (timestamped JSON). The Google Sheets Apps Script
endpoint is the authoritative source; cached JSONs avoid network round-trips.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict

import requests

# Resolve paths relative to repo root
_SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
_REPO_ROOT = _SCRIPT_DIR.parent
_CONFIG_DIR = _REPO_ROOT / 'configs'

# Google Sheets Web App endpoint
CONFIG_URL = "https://script.google.com/macros/s/AKfycbxgWZsK0nSyDkh1XzNfLpWesAEBDHy2KKAmlnO4T73DAfNgszE46bwxUPPeE9AX6ZznNg/exec"


def fetch_scoring_config() -> dict:
    """Fetch the latest scoring/tuning config from the Google Sheet."""
    try:
        print("Fetching latest scoring config from Google Sheets...")
        response = requests.get(CONFIG_URL, timeout=15)
        response.raise_for_status()
        config_data = response.json()
        print("Successfully fetched config from Google Sheets")
        return config_data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching config from Google Sheets: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        raise


def save_config_file(config_data: dict, config_dir: str = None) -> str:
    """Save the config data to a timestamped JSON file and archive old configs."""
    if config_dir is None:
        config_dir = str(_CONFIG_DIR)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"SCORE_TUNING_CONFIG_{timestamp}.json"
    filepath = os.path.join(config_dir, filename)

    os.makedirs(config_dir, exist_ok=True)

    archive_dir = os.path.join(config_dir, 'archive')
    os.makedirs(archive_dir, exist_ok=True)

    # Move existing config files to archive before saving new one
    existing_configs = [f for f in os.listdir(config_dir)
                        if f.startswith('SCORE_TUNING_CONFIG_') and f.endswith('.json')]
    for config_file in existing_configs:
        old_path = os.path.join(config_dir, config_file)
        new_path = os.path.join(archive_dir, config_file)
        if os.path.exists(old_path):
            os.rename(old_path, new_path)
            print(f"Archived old config: {config_file}")

    with open(filepath, 'w') as f:
        json.dump(config_data, f, indent=2)

    print(f"Saved config to: {filepath}")
    return filepath


def get_latest_config_file(config_dir: str = None) -> str:
    """Find the most recent SCORE_TUNING_CONFIG file in the directory."""
    if config_dir is None:
        config_dir = str(_CONFIG_DIR)

    if not os.path.exists(config_dir):
        return None

    config_files = [f for f in os.listdir(config_dir)
                    if f.startswith('SCORE_TUNING_CONFIG_') and f.endswith('.json')]
    if not config_files:
        return None

    config_files.sort(reverse=True)
    return os.path.join(config_dir, config_files[0])


def load_latest_config(config_dir: str = None) -> dict:
    """Load the most recent config file, or fetch from Google Sheets if none exists."""
    if config_dir is None:
        config_dir = str(_CONFIG_DIR)

    latest_file = get_latest_config_file(config_dir)

    if latest_file and os.path.exists(latest_file):
        print(f"Loading latest config from: {os.path.basename(latest_file)}")
        with open(latest_file, 'r') as f:
            return json.load(f)
    else:
        print("No local config found, fetching from Google Sheets...")
        config_data = fetch_scoring_config()
        save_config_file(config_data, config_dir)
        return config_data


def load_config() -> dict:
    """Convenience wrapper: load the latest scoring config."""
    return load_latest_config()


def update_config(force_refresh: bool = False) -> str:
    """Update the scoring config, optionally forcing a refresh from Google Sheets."""
    config_dir = str(_CONFIG_DIR)

    if force_refresh:
        print("Force refresh requested - fetching latest config...")
        config_data = fetch_scoring_config()
        return save_config_file(config_data, config_dir)

    latest_file = get_latest_config_file(config_dir)
    if latest_file:
        # Extract timestamp from filename
        basename = os.path.basename(latest_file)
        try:
            parts = basename.replace('.json', '').split('_')
            # SCORE_TUNING_CONFIG_YYYYMMDD_HHMMSS
            file_date_str = parts[3]
            file_time_str = parts[4]
            file_dt = datetime.strptime(f"{file_date_str}_{file_time_str}", '%Y%m%d_%H%M%S')

            now = datetime.now()
            if (now - file_dt).total_seconds() < 3600:
                print(f"Recent config exists: {basename}")
                return latest_file
        except (IndexError, ValueError):
            pass

    print("Fetching fresh config...")
    config_data = fetch_scoring_config()
    return save_config_file(config_data, config_dir)


def main():
    """CLI entrypoint to update config."""
    import argparse

    parser = argparse.ArgumentParser(description='Update scoring configuration from Google Sheets')
    parser.add_argument('--force', action='store_true', help='Force refresh even if recent config exists')
    parser.add_argument('--test', action='store_true', help='Test config access after update')
    args = parser.parse_args()

    try:
        config_file = update_config(force_refresh=args.force)

        if args.test:
            cfg = load_latest_config()
            print(f"\nConfig test:")
            print(f"  Company Alignment weight: {cfg['companyScore']['pillars']['Alignment']['weight']}")
            print(f"  Seniority weight: {cfg['peopleScore']['pillars']['Seniority']['description']}")

        print(f"\nConfig update complete! Latest config: {os.path.basename(config_file)}")
    except Exception as e:
        print(f"\nConfig update failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
