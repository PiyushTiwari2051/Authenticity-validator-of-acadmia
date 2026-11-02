"""Tests for Road B Forensic Engine & Fixed Verdict Semantics."""

import pytest
from backend.app.modules.forensics.pipeline import (
    analyze_pdf_metadata, analyze_noise_consistency, analyze_glyph_consistency,
    analyze_copy_move, evaluate_road_b_verdict
)


def test_metadata_forensic_detects_photoshop():
    clean_pdf = b"%PDF-1.7\n1 0 obj\n<< /Producer (Sanad Native Engine) >>\nendobj\n%%EOF"
    tampered_pdf = b"%PDF-1.7\n1 0 obj\n<< /Producer (Adobe Photoshop CC 2024) >>\nendobj\n%%EOF\n%%EOF"

    res_clean = analyze_pdf_metadata(clean_pdf)
    assert res_clean.anomaly_detected is False

    res_tampered = analyze_pdf_metadata(tampered_pdf)
    assert res_tampered.anomaly_detected is True
    assert "photoshop" in res_tampered.explanation.lower()


def test_road_b_verdict_field_contradiction_is_likely_altered():
    verdict, summary, findings = evaluate_road_b_verdict(
        registry_matched=True,
        field_discrepancies=["CGPA extracted 9.20 contradicts registry 7.40"],
        forensic_signals=[]
    )
    assert verdict == "LIKELY_ALTERED"
    assert "CGPA" in summary


def test_road_b_verdict_clean_scan_is_consistent_with_registry():
    clean_signals = [
        analyze_noise_consistency(0.01),
        analyze_glyph_consistency(1.0),
        analyze_copy_move(0)
    ]
    verdict, summary, findings = evaluate_road_b_verdict(
        registry_matched=True,
        field_discrepancies=[],
        forensic_signals=clean_signals
    )
    assert verdict == "CONSISTENT_WITH_REGISTRY"
    assert "not mathematical proof" in summary.lower()


def test_road_b_verdict_unmatched_is_cannot_verify():
    verdict, summary, findings = evaluate_road_b_verdict(
        registry_matched=False,
        field_discrepancies=[],
        forensic_signals=[]
    )
    assert verdict == "CANNOT_VERIFY"
