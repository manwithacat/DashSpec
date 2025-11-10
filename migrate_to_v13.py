#!/usr/bin/env python3
"""
Migrate DashSpec YAML files from v1.2 to v1.3

Extracts common formatting properties and creates default_formatting field.
"""

import yaml
import sys
from pathlib import Path
from collections import Counter
from typing import Dict, Any, Optional


def analyze_formatting(formatting: Optional[Dict[str, Dict]]) -> Optional[Dict]:
    """
    Analyze formatting rules to find common properties
    Returns the most common property values that could be defaults
    """
    if not formatting:
        return None

    # Count property values across all fields
    type_counter = Counter()
    precision_counter = Counter()
    thousands_counter = Counter()
    sig_digits_counter = Counter()

    for field_name, format_spec in formatting.items():
        if 'type' in format_spec:
            type_counter[format_spec['type']] += 1
        if 'precision' in format_spec:
            precision_counter[format_spec['precision']] += 1
        if 'use_thousands_separator' in format_spec:
            thousands_counter[format_spec['use_thousands_separator']] += 1
        if 'significant_digits' in format_spec:
            sig_digits_counter[format_spec['significant_digits']] += 1

    # Only create defaults if there are at least 3 fields with common properties
    if len(formatting) < 3:
        return None

    default_format = {}

    # If most fields share a type (but not currency), use it as default
    if type_counter:
        most_common_type, count = type_counter.most_common(1)[0]
        # Only use 'number' or 'integer' as defaults (not currency/percent - too specific)
        if count >= 3 and most_common_type in ['number', 'integer']:
            default_format['type'] = most_common_type

    # If most fields share precision
    if precision_counter:
        most_common_precision, count = precision_counter.most_common(1)[0]
        if count >= 3:
            default_format['precision'] = most_common_precision

    # If most fields share use_thousands_separator
    if thousands_counter:
        most_common_thousands, count = thousands_counter.most_common(1)[0]
        if count >= 3:
            default_format['use_thousands_separator'] = most_common_thousands

    # If most fields share significant_digits
    if sig_digits_counter:
        most_common_sig, count = sig_digits_counter.most_common(1)[0]
        if count >= 3:
            default_format['significant_digits'] = most_common_sig

    return default_format if default_format else None


def simplify_formatting(formatting: Dict[str, Dict], default_format: Dict) -> Dict[str, Dict]:
    """
    Remove properties from field-specific formatting that match defaults
    Only keep properties that override defaults
    """
    simplified = {}

    for field_name, format_spec in formatting.items():
        # Start with a copy of the format spec
        new_spec = dict(format_spec)

        # Remove properties that match defaults
        for prop, default_value in default_format.items():
            if prop in new_spec and new_spec[prop] == default_value:
                del new_spec[prop]

        # Only include field if it has overrides
        if new_spec:
            simplified[field_name] = new_spec

    return simplified


def migrate_yaml(file_path: Path, dry_run: bool = False) -> bool:
    """
    Migrate a single YAML file to v1.3
    Returns True if changes were made
    """
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Processing: {file_path}")

    # Load YAML
    with open(file_path, 'r') as f:
        content = yaml.safe_load(f)

    # Check version
    if content.get('dsl_version') != '1.2.0':
        print(f"  ⏭️  Skipping (not v1.2.0, found: {content.get('dsl_version')})")
        return False

    # Update version
    content['dsl_version'] = '1.3.0'

    # Check if formatting exists
    data_source = content.get('dashboard', {}).get('data_source', {})
    formatting = data_source.get('formatting')

    if not formatting:
        print("  ℹ️  No formatting section found")
        if not dry_run:
            with open(file_path, 'w') as f:
                yaml.dump(content, f, default_flow_style=False, sort_keys=False)
        print("  ✅ Updated version to 1.3.0")
        return True

    # Analyze formatting
    default_format = analyze_formatting(formatting)

    if not default_format:
        print(f"  ℹ️  No common formatting patterns found ({len(formatting)} fields)")
        if not dry_run:
            with open(file_path, 'w') as f:
                yaml.dump(content, f, default_flow_style=False, sort_keys=False)
        print("  ✅ Updated version to 1.3.0")
        return True

    print(f"  📊 Found common pattern: {default_format}")

    # Simplify formatting
    simplified_formatting = simplify_formatting(formatting, default_format)

    # Update data_source with default_formatting and simplified formatting
    # We need to preserve order: default_formatting should come before formatting
    new_data_source = {}

    # Copy all fields up to formatting
    for key in data_source:
        if key == 'formatting':
            # Insert default_formatting before formatting
            new_data_source['default_formatting'] = default_format
            if simplified_formatting:
                new_data_source['formatting'] = simplified_formatting
            else:
                print("  🗑️  Removed formatting section (all fields use defaults)")
        else:
            new_data_source[key] = data_source[key]

    # If formatting wasn't in original, add default_formatting at end
    if 'formatting' not in data_source:
        new_data_source['default_formatting'] = default_format

    content['dashboard']['data_source'] = new_data_source

    # Write back
    if not dry_run:
        with open(file_path, 'w') as f:
            yaml.dump(content, f, default_flow_style=False, sort_keys=False, width=100000)
        print(f"  ✅ Migrated to v1.3.0")
        print(f"     • Added default_formatting: {len(default_format)} properties")
        print(f"     • Simplified formatting: {len(formatting)} → {len(simplified_formatting)} fields")
    else:
        print(f"  [DRY RUN] Would migrate:")
        print(f"     • Add default_formatting: {len(default_format)} properties")
        print(f"     • Simplify formatting: {len(formatting)} → {len(simplified_formatting)} fields")

    return True


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Migrate DashSpec YAML files from v1.2 to v1.3')
    parser.add_argument('files', nargs='+', help='YAML files to migrate')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without modifying files')

    args = parser.parse_args()

    changed_count = 0

    for file_path in args.files:
        path = Path(file_path)
        if not path.exists():
            print(f"⚠️  File not found: {file_path}")
            continue

        if migrate_yaml(path, dry_run=args.dry_run):
            changed_count += 1

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Summary: {changed_count}/{len(args.files)} files processed")


if __name__ == '__main__':
    main()
