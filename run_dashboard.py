#!/usr/bin/env python3
"""
Dashboard Launcher

Launch a Streamlit dashboard from a DashSpec YAML specification.

Usage:
    python run_dashboard.py <spec_path>
    python run_dashboard.py dsl/examples/happy_path.yaml

For Streamlit CLI:
    streamlit run run_dashboard.py -- dsl/examples/happy_path.yaml
"""

import argparse
import sys
from pathlib import Path

from dsl.renderers.streamlit.renderer import render_dashboard


def main():
    parser = argparse.ArgumentParser(
        description="Launch a Streamlit dashboard from a DashSpec specification"
    )
    parser.add_argument("spec_path", type=str, help="Path to the YAML dashboard specification file")

    args = parser.parse_args()

    spec_path = Path(args.spec_path)

    if not spec_path.exists():
        print(f"Error: Specification file not found: {spec_path}", file=sys.stderr)
        sys.exit(1)

    # Render the dashboard
    render_dashboard(str(spec_path))


if __name__ == "__main__":
    main()
