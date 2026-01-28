#!/usr/bin/env python3
"""Validate that generated code follows ACME API patterns.

This script checks if a generated route file follows the expected patterns.
Useful for verifying ICRL output or comparing ablation results.

Usage:
    python validate_patterns.py path/to/routes/orders.py
    python validate_patterns.py --all  # Check all route files
"""

import argparse
import re
import sys
from pathlib import Path


class PatternChecker:
    """Check code for ACME API pattern compliance."""
    
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.content = filepath.read_text()
        self.issues: list[str] = []
        self.passes: list[str] = []
    
    def check_all(self) -> bool:
        """Run all pattern checks."""
        self.check_api_response_usage()
        self.check_no_http_exception()
        self.check_service_layer()
        self.check_structured_logging()
        self.check_response_model()
        self.check_type_hints()
        return len(self.issues) == 0
    
    def check_api_response_usage(self):
        """Check that APIResponse is imported and used."""
        if "from app.core.response import APIResponse" in self.content:
            self.passes.append("✅ Imports APIResponse from app.core.response")
        elif "APIResponse" in self.content:
            self.issues.append("⚠️  Uses APIResponse but wrong import path")
        else:
            self.issues.append("❌ Does not use APIResponse wrapper")
        
        if "APIResponse.success(" in self.content:
            self.passes.append("✅ Uses APIResponse.success() for responses")
        elif "return {" in self.content or "return order" in self.content:
            self.issues.append("❌ Returns raw dict/model instead of APIResponse")
    
    def check_no_http_exception(self):
        """Check that HTTPException is not used directly."""
        # Check for actual usage, not just mentions in comments/docstrings
        # Look for: raise HTTPException or from fastapi import HTTPException
        if "raise HTTPException" in self.content:
            self.issues.append("❌ Uses 'raise HTTPException' (should use custom exceptions)")
        elif "from fastapi import" in self.content and "HTTPException" in self.content.split("from fastapi import")[1].split("\n")[0]:
            self.issues.append("❌ Imports HTTPException from fastapi (should use custom exceptions)")
        else:
            self.passes.append("✅ Does not use HTTPException directly")
    
    def check_service_layer(self):
        """Check that routes delegate to services."""
        # Look for service imports
        service_pattern = r"from app\.services import \w+_service"
        if re.search(service_pattern, self.content):
            self.passes.append("✅ Imports from app.services")
        elif "_service." in self.content:
            self.passes.append("✅ Uses service layer pattern")
        else:
            # Check if there's business logic in routes
            if "_db[" in self.content or "database" in self.content.lower():
                self.issues.append("❌ Contains database access (should be in service)")
            else:
                self.issues.append("⚠️  No clear service layer usage detected")
    
    def check_structured_logging(self):
        """Check for structured logging usage."""
        if "from app.core.logging import get_logger" in self.content:
            self.passes.append("✅ Imports get_logger from app.core.logging")
        elif "get_logger" in self.content:
            self.issues.append("⚠️  Uses get_logger but wrong import path")
        
        # Check for structured log calls
        structured_log = r'logger\.(info|warning|error)\("[^"]+",\s*\w+='
        if re.search(structured_log, self.content):
            self.passes.append("✅ Uses structured logging (key=value)")
        elif "print(" in self.content:
            self.issues.append("❌ Uses print() instead of structured logging")
        elif 'logger.info(f"' in self.content:
            self.issues.append("❌ Uses f-string in logging (should use key=value)")
    
    def check_response_model(self):
        """Check for response_model declarations."""
        if "response_model=APIResponse[" in self.content:
            self.passes.append("✅ Uses response_model=APIResponse[T]")
        elif "response_model=" in self.content:
            self.issues.append("⚠️  Uses response_model but not with APIResponse")
        else:
            self.issues.append("❌ Missing response_model declarations")
    
    def check_type_hints(self):
        """Check for return type hints."""
        # Look for async def with return type
        typed_func = r"async def \w+\([^)]*\)\s*->\s*APIResponse\["
        if re.search(typed_func, self.content):
            self.passes.append("✅ Has return type hints with APIResponse")
        elif "-> APIResponse" in self.content:
            self.passes.append("✅ Has return type hints")
        else:
            self.issues.append("⚠️  Missing return type hints")
    
    def report(self) -> str:
        """Generate a report of findings."""
        lines = [f"\n📄 Checking: {self.filepath}\n"]
        
        if self.passes:
            lines.append("Passed:")
            lines.extend(f"  {p}" for p in self.passes)
        
        if self.issues:
            lines.append("\nIssues:")
            lines.extend(f"  {i}" for i in self.issues)
        
        score = len(self.passes) / (len(self.passes) + len(self.issues)) * 100
        lines.append(f"\nPattern Score: {score:.0f}%")
        
        if score == 100:
            lines.append("🎉 Perfect! All patterns followed correctly.")
        elif score >= 70:
            lines.append("👍 Good, but some patterns could be improved.")
        else:
            lines.append("⚠️  Needs improvement - review the ACME API patterns.")
        
        return "\n".join(lines)


def find_route_files(base_path: Path) -> list[Path]:
    """Find all route files in the codebase."""
    routes_dir = base_path / "app" / "routes"
    if not routes_dir.exists():
        return []
    
    return [
        f for f in routes_dir.glob("*.py")
        if f.name != "__init__.py"
    ]


def main():
    parser = argparse.ArgumentParser(description="Validate ACME API patterns")
    parser.add_argument("file", nargs="?", help="Route file to check")
    parser.add_argument("--all", action="store_true", help="Check all route files")
    args = parser.parse_args()
    
    base_path = Path(__file__).parent / "mock_codebase"
    
    if args.all:
        files = find_route_files(base_path)
        if not files:
            print("No route files found in app/routes/")
            sys.exit(1)
    elif args.file:
        files = [Path(args.file)]
    else:
        parser.print_help()
        sys.exit(1)
    
    all_passed = True
    for filepath in files:
        if not filepath.exists():
            print(f"❌ File not found: {filepath}")
            all_passed = False
            continue
        
        checker = PatternChecker(filepath)
        passed = checker.check_all()
        print(checker.report())
        
        if not passed:
            all_passed = False
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
