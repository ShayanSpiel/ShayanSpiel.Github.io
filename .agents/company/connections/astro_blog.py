"""Repository-local blog publishing Connection; writes only after runtime approval."""

import re
from pathlib import Path
from .base import ConnectionResult


class AstroBlogConnection:
    id = "astro-blog"

    def __init__(self, root=None):
        self.root = Path(root or Path(__file__).resolve().parents[3])

    def publish(self, *, slug, source, dry_run=True):
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            return ConnectionResult(False, self.id, "publish", error="Slug must be lowercase kebab-case")
        target = self.root / "src/content/notes" / f"{slug}.mdx"
        if dry_run:
            return ConnectionResult(True, self.id, "publish", {"dry_run": True, "target": str(target), "bytes": len(source.encode())})
        if target.exists():
            return ConnectionResult(False, self.id, "publish", error="Refusing to overwrite an existing article")
        target.write_text(source)
        return ConnectionResult(True, self.id, "publish", {"target": str(target), "bytes": target.stat().st_size})
