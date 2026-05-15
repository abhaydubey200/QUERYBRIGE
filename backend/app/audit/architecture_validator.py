import os
import sys
import importlib.util
from typing import List, Dict

class ArchitectureValidator:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.gaps = []

    def check_dependencies(self):
        """Check if required modules are importable."""
        required = [
            "fastapi", "sqlalchemy", "prometheus_client", "pydantic", 
            "jwt", "cryptography", "pandas", "duckdb", "redis"
        ]
        for lib in required:
            if importlib.util.find_spec(lib) is None:
                self.gaps.append(f"MISSING_DEPENDENCY: {lib} is not installed in the environment.")

    def check_file_structure(self):
        """Verify that all Phase 4 files exist."""
        required_paths = [
            "backend/app/semantic/semantic_resolver.py",
            "backend/app/services/ai_analyst_service.py",
            "backend/app/notebook/execution_engine.py",
            "backend/app/ml/forecasting_engine.py",
            "backend/app/governance/masking_service.py"
        ]
        for path in required_paths:
            full_path = os.path.join(self.root_dir, path)
            if not os.path.exists(full_path):
                self.gaps.append(f"MISSING_FILE: {path} was expected but not found.")

    def run_audit(self):
        self.check_dependencies()
        self.check_file_structure()
        return self.gaps

if __name__ == "__main__":
    validator = ArchitectureValidator(os.getcwd())
    results = validator.run_audit()
    for gap in results:
        print(gap)
