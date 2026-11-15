from __future__ import annotations

import argparse

from app.core.engine import SecurityEngine


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a safe pentest scan against an authorized target.")
    parser.add_argument("target", help="URL or hostname to scan, e.g. https://example.com")
    args = parser.parse_args()

    engine = SecurityEngine()
    report = engine.run(args.target)
    print(f"Target: {report['target']}")
    print(f"Status: {report['status']}")
    for item in report.get("prioritized_findings", []):
        print(f"- [{item['severity'].upper()}] {item['title']}")


if __name__ == "__main__":
    main()
