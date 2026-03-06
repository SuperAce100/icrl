"""Load theorems from miniF2F-lean4 repository."""

import os
import shutil
from pathlib import Path

from lean_dojo import LeanGitRepo, Theorem, trace


#### 
# Simon note: right now we just gonna hillclimb the benchmark
# which is just minif2f
### 
class MiniF2FLoader:
    """Load and filter theorems from miniF2F-lean4."""

    def __init__(self, repo_path: str | Path = "/home/simon/miniF2F-lean4"):
        self.repo_path = Path(repo_path)
        self._traced_repo = None
        self._theorems: list[Theorem] = []

    def trace_repo(self, commit: str = "main") -> None:
        """Trace the repository to extract theorem information.
        
        This may take a while on first run (builds Lean, caches results).
        """
        if shutil.which("lake") is None:
            elan_bin = Path.home() / ".elan" / "bin"
            lake_path = elan_bin / "lake"
            if lake_path.exists():
                os.environ["PATH"] = f"{elan_bin}:{os.environ.get('PATH', '')}"
            else:
                raise RuntimeError(
                    "`lake` not found on PATH. Install Lean via elan and ensure "
                    "~/.elan/bin is on PATH (or set PATH in your shell) before "
                    "calling trace_repo()."
                )
        repo = LeanGitRepo(str(self.repo_path), commit)
        self._traced_repo = trace(repo)
        self._theorems = list(self._traced_repo.get_theorems())

    @property
    def theorems(self) -> list[Theorem]:
        if not self._theorems:
            raise RuntimeError("Call trace_repo() first")
        return self._theorems

    def get_valid_theorems(self) -> list[Theorem]:
        """Get theorems from the Valid split (development set)."""
        return [t for t in self.theorems if "Valid" in str(t.file_path)]

    def get_test_theorems(self) -> list[Theorem]:
        """Get theorems from the Test split (held-out)."""
        return [t for t in self.theorems if "Test" in str(t.file_path)]

    def get_mathd_algebra(self) -> list[Theorem]:
        """Get mathd_algebra theorems (easiest subset)."""
        return [t for t in self.get_valid_theorems() if "mathd_algebra" in t.full_name]

    def get_mathd_numbertheory(self) -> list[Theorem]:
        """Get mathd_numbertheory theorems."""
        return [t for t in self.get_valid_theorems() if "mathd_numbertheory" in t.full_name]

    def get_easy_subset(self) -> list[Theorem]:
        """Get combined easy subset: mathd_algebra + mathd_numbertheory."""
        return self.get_mathd_algebra() + self.get_mathd_numbertheory()

    def filter_by_prefix(self, prefix: str) -> list[Theorem]:
        """Filter theorems by name prefix (e.g., 'amc12', 'aime')."""
        return [t for t in self.theorems if t.full_name.startswith(prefix)]


def list_theorem_files(repo_path: str | Path = "/home/simon/miniF2F-lean4") -> dict[str, list[str]]:
    """Quick scan of theorem files without tracing (faster for exploration)."""
    repo_path = Path(repo_path)
    result = {"valid": [], "test": []}
    
    valid_dir = repo_path / "MiniF2F" / "Valid"
    test_dir = repo_path / "MiniF2F" / "Test"
    
    if valid_dir.exists():
        result["valid"] = sorted([f.stem for f in valid_dir.glob("*.lean") if f.stem != "Valid"])
    if test_dir.exists():
        result["test"] = sorted([f.stem for f in test_dir.glob("*.lean") if f.stem != "Test"])
    
    return result


def count_by_category(theorem_names: list[str]) -> dict[str, int]:
    """Count theorems by category prefix."""
    categories: dict[str, int] = {}
    for name in theorem_names:
        prefix = name.split("_")[0] if "_" in name else name
        categories[prefix] = categories.get(prefix, 0) + 1
    return dict(sorted(categories.items(), key=lambda x: -x[1]))
