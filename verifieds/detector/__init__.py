"""VerifiedDS detector package."""

from verifieds.detector.engine import analyze_file
from verifieds.detector.loader import load_rules
from verifieds.detector.scanner import SourceView

detect_file = analyze_file

__all__ = ["analyze_file", "detect_file", "load_rules", "SourceView"]
