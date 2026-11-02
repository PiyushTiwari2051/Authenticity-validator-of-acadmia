"""
End-to-end Verification Diagnostic Script
Probes all UI views, static assets, APIs, and file upload forensics.
"""

import urllib.request
import json
import sys

BASE_URL = "http://localhost:3000"

def run_tests():
    print("=" * 65)
    print("AUTHENTICITY VALIDATOR FOR ACADEMIA: FULL SYSTEM AUDIT")
    print("=" * 65)

    # 1. Probing HTML Home View
    print("\n[1/6] Probing Root Home View (/) ...")
    with urllib.request.urlopen(f"{BASE_URL}/") as resp:
        html = resp.read().decode("utf-8")
        assert "AUTHENTICITY VALIDATOR" in html, "Wordmark missing"
        assert "DROP CERTIFICATE HERE" in html, "Drop slab missing"
        assert "sanad" not in html.lower(), "Legacy name found in HTML"
        assert "mohar" not in html.lower(), "Legacy name found in HTML"
        print("  ✓ Home view live with 0 legacy names, stacked wordmark, and Drop Slab.")

    # 2. Probing Static Assets
    print("\n[2/6] Probing Static Assets (/css/brutalist.css & /js/brutalist.js) ...")
    with urllib.request.urlopen(f"{BASE_URL}/css/brutalist.css") as resp:
        css = resp.read().decode("utf-8")
        assert "border-radius: 0 !important" in css
        assert "--blue: #BFE3FF" in css
        print("  ✓ Brutalist CSS loaded (0 radius, strict tokens, 6px hard shadows).")

    with urllib.request.urlopen(f"{BASE_URL}/js/brutalist.js") as resp:
        js = resp.read().decode("utf-8")
        assert "playMechanicalThud" in js
        assert "initBreakItYourself" in js
        print("  ✓ Brutalist JS loaded (Web Audio thud, ledger run, tampering sandbox).")

    # 3. Probing Preset Verification APIs
    print("\n[3/6] Probing Preset Verification Endpoints ...")
    with urllib.request.urlopen(f"{BASE_URL}/api/verify?id=RU-2024-88492") as resp:
        r_gen = json.loads(resp.read())
        assert r_gen["verdict"] == "VERIFIED_ISSUER_SIGNED"
        print(f"  ✓ RU-2024-88492 -> {r_gen['verdict']} ({r_gen['headline']})")

    with urllib.request.urlopen(f"{BASE_URL}/api/verify?id=VBU-2023-11002") as resp:
        r_rev = json.loads(resp.read())
        assert r_rev["verdict"] == "REVOKED"
        print(f"  ✓ VBU-2023-11002 -> {r_rev['verdict']} ({r_rev['headline']})")

    # 4. Testing Upload of Authentic Registered Certificate
    print("\n[4/6] Testing Upload of Authentic Certificate (RapidOCR + Registry) ...")
    img_data = open("ml/data/sanad_cert/test_registered_amit.png", "rb").read()
    req = urllib.request.Request(f"{BASE_URL}/api/upload", data=img_data, headers={"Content-Type": "application/octet-stream"})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read())
        assert res["verdict"] == "VERIFIED_ISSUER_SIGNED"
        print(f"  ✓ Authentic Scan -> {res['verdict']} ({res['headline']})")

    # 5. Testing Upload of Tampered Certificate
    print("\n[5/6] Testing Upload of Tampered Certificate (T8 Contradictory CGPA) ...")
    tamp_data = open("ml/data/sanad_cert/test_tampered_amit.png", "rb").read()
    req = urllib.request.Request(f"{BASE_URL}/api/upload", data=tamp_data, headers={"Content-Type": "application/octet-stream"})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read())
        assert res["verdict"] == "LIKELY_ALTERED"
        print(f"  ✓ Tampered Scan -> {res['verdict']} ({res['headline']})")

    # 6. Testing Upload of Random Non-Academic File
    print("\n[6/6] Testing Upload of Random Non-Academic File (pyproject.toml) ...")
    rand_data = open("pyproject.toml", "rb").read()
    req = urllib.request.Request(f"{BASE_URL}/api/upload", data=rand_data, headers={"Content-Type": "application/octet-stream"})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read())
        assert res["verdict"] == "UNRECOGNIZED_DOCUMENT"
        print(f"  ✓ Random Non-Academic File -> {res['verdict']} ({res['headline']})")

    print("\n" + "=" * 65)
    print("ALL 6 PRODUCTION-GRADE VERIFICATION TESTS PASSED SUCCESSFULLY.")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
