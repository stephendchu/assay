"""Reference workflows built on the assay control plane.

Each app is a thin adapter: it supplies steps; the plane supplies determinism,
checkpoints, gates, approvals, artifacts, and the audit log. Running multiple
domains through the same plane is the proof it generalizes.
"""
