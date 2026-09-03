#!/usr/bin/env python3
"""
Update OpenRouter free models in Hermes Agent configuration.

This script fetches the latest free models from OpenRouter's frontend API
and updates the Hermes configuration to show only free models in the
model picker (CLI and Web UI).

Author: John Snoopy (JohnSnoopyKnowNothing)
License: MIT
Repository: https://github.com/JohnSnoopyKnowNothing/openrouter-free-models-updater
"""

import json
import os
import sys
import requests
from datetime import datetime, timezone
from pathlib import Path

def safe_get(d, *keys, default=None):
    for k in keys:
        if isinstance(d, dict) and k in d:
            d = d[k]
        else:
            return default
    return d


import argparse
import logging

def setup_logging(verbose):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler("/tmp/openrouter-update.log"), logging.StreamHandler()] if verbose else [logging.StreamHandler()]
    )

# Configuration
FRONTEND_API_URL = "https://openrouter.ai/api/frontend/v1/models/find?active=true&fmt=cards&q=free"
MODEL_CATALOG_PATH = Path(os.getenv("HERMES_MODEL_CATALOG", Path.home() / ".hermes" / "cache" / "model_catalog.json"))
PROVIDER_MODEL_CATALOG_PATH = Path(os.getenv("HERMES_WEBUI_CATALOG", Path.home() / ".hermes-web-ui" / "cache" / "provider-model-catalog.json"))
WEBUI_KEY = "profile:default|openrouter|https://openrouter.ai/api/v1|free"


def fetch_free_models():
    """Fetch free models from OpenRouter frontend API."""
    print(f"Fetching free models from: {FRONTEND_API_URL}")
    
    try:
        response = requests.get(FRONTEND_API_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"Error fetching API: {e}")
        sys.exit(1)
    
    models = data.get('data', {}).get('models', [])
    print(f"Found {len(models)} models from API")
    
    # Filter models with text output
    free_models = []
    for m in models:
        # Skip models without text output (embedding, TTS, etc.)
        if not m.get('has_text_output', False):
            continue
        
        endpoint = m.get('endpoint') or {}
        slug = endpoint.get('model_variant_slug') or m.get('slug', 'N/A')
        name = m.get('short_name') or m.get('name', 'N/A')
        
        # Check capabilities
        supports_reasoning = endpoint.get('supports_reasoning', False) or m.get('supports_reasoning', False)
        supports_tools = endpoint.get('supports_tool_parameters', False)
        input_modalities = m.get('input_modalities', [])
        has_vision = 'image' in input_modalities or 'video' in input_modalities
        
        # Build capability tags
        caps = []
        if supports_reasoning: caps.append('reasoning')
        if has_vision: caps.append('vision')
        if supports_tools: caps.append('tools')
        
        description = f"free, {', '.join(caps)}" if caps else "free"
        
        free_models.append({
            'id': slug,
            'description': description
        })
    
    print(f"Filtered to {len(free_models)} free models with text output")
    return free_models


def update_model_catalog(free_models):
    """Update model_catalog.json with free models."""
    print(f"\nUpdating: {MODEL_CATALOG_PATH}")
    
    try:
        if MODEL_CATALOG_PATH.exists():
            with open(MODEL_CATALOG_PATH, 'r') as f:
                catalog = json.load(f)
        else:
            catalog = {}
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: could not read {MODEL_CATALOG_PATH}: {e}. Starting fresh.")
        catalog = {}

    # Normalize/initialize catalog structure
    if not isinstance(catalog, dict):
        catalog = {}
    if 'version' not in catalog:
        catalog['version'] = 1
    if 'updated_at' not in catalog:
        catalog['updated_at'] = datetime.now(timezone.utc).isoformat()
    if 'providers' not in catalog or not isinstance(catalog.get('providers'), dict):
        catalog['providers'] = {}
    
    # Ensure openrouter provider exists
    if 'openrouter' not in catalog.get('providers', {}):
        catalog['providers']['openrouter'] = {
            "metadata": {
                "display_name": "OpenRouter",
                "note": "Descriptions drive picker badges. Live /api/v1/models filters curated ids by tool-calling support and free pricing. The entry labeled \"default\": true is the model Hermes silently lands on when the user never picked one."
            },
            "models": []
        }
    
    # Update models list
    catalog['providers']['openrouter']['models'] = free_models
    catalog['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    # Write back
    if not getattr(main, '_dry_run', False):
        MODEL_CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(MODEL_CATALOG_PATH, 'w') as f:
            json.dump(catalog, f, indent=2)
    else:
        print("[DRY-RUN] Would write", MODEL_CATALOG_PATH)
        json.dump(catalog, f, indent=2)
    
    print(f"✓ Updated {len(free_models)} models in model_catalog.json")


def update_webui_cache(free_models):
    """Update provider-model-catalog.json for Web UI."""
    print(f"\nUpdating: {PROVIDER_MODEL_CATALOG_PATH}")
    
    try:
        if PROVIDER_MODEL_CATALOG_PATH.exists():
            with open(PROVIDER_MODEL_CATALOG_PATH, 'r') as f:
                cache = json.load(f)
        else:
            cache = {}
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: could not read {PROVIDER_MODEL_CATALOG_PATH}: {e}. Starting fresh.")
        cache = {}
    if not isinstance(cache, dict):
        cache = {}
    if 'providers' not in cache or not isinstance(cache.get('providers'), dict):
        cache['providers'] = {}
    
    # Extract model IDs
    model_ids = [m['id'] for m in free_models]
    
    # Update Web UI cache
    if WEBUI_KEY in cache.get('providers', {}):
        cache['providers'][WEBUI_KEY]['models'] = model_ids
        cache['providers'][WEBUI_KEY]['updated_at'] = datetime.now(timezone.utc).isoformat()
    else:
        # Create new entry if not exists
        cache['providers'][WEBUI_KEY] = {
            "provider": "openrouter",
            "label": "OpenRouter",
            "base_url": "https://openrouter.ai/api/v1",
            "models": model_ids,
            "source": "live",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "free_only": True,
            "profiles": ["default"],
            "profile": "default"
        }
    
    # Write back
    PROVIDER_MODEL_CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PROVIDER_MODEL_CATALOG_PATH, 'w') as f:
        json.dump(cache, f, indent=2)
    
    print(f"✓ Updated {len(model_ids)} models in provider-model-catalog.json")


def print_report(free_models):
    """Print update report."""
    print("\n" + "=" * 80)
    print("Update Report")
    print("=" * 80)
    print(f"\nTotal free models: {len(free_models)}")
    print("\nModels:")
    for i, m in enumerate(free_models, 1):
        print(f"  {i:2}. {m['id']}")
        print(f"      {m['description']}")
    print("\n" + "=" * 80)
    print("\nNext steps:")
    print("  1. Refresh your browser (Ctrl+Shift+R) to see updated models in Web UI")
    print("  2. Do NOT run `hermes model --refresh` as it will overwrite our filtered list")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    parser.add_argument("--verbose", action="store_true", help="Enable logging")
    args = parser.parse_args()
    setup_logging(args.verbose)
    """Main entry point."""
    print("OpenRouter Free Models Updater")
    print("=" * 80)
    
    # Fetch free models
    free_models = fetch_free_models()
    
    # Update configurations
    update_model_catalog(free_models)
    update_webui_cache(free_models)
    
    # Print report
    print_report(free_models)
    
    print("\n✓ Update completed successfully!")


if __name__ == "__main__":
    main()
