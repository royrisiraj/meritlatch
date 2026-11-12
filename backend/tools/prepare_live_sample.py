"""Offline Pillow drawing; no photograph, model, network or automatic consent."""

from hashlib import sha256
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def prepare(root=Path("fixtures/live_inputs/gemini_3_8_validation")):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    image_path, truth_path = root / "pump_inspection.png", root / "ground_truth.json"
    if image_path.exists() or truth_path.exists():
        raise ValueError("Preserve existing review image/truth; do not overwrite a human-reviewed sample.")

    def font(size, bold=False):
        name = "arialbd.ttf" if bold else "arial.ttf"
        path = Path("C:/Windows/Fonts") / name
        return ImageFont.truetype(str(path) if path.exists() else "DejaVuSans.ttf", size)

    image = Image.new("RGB", (1800, 1200), "#e5e9ec")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1800, 115), fill="#172b36")
    draw.text((45, 22), "FICTIONAL / SYNTHETIC INSPECTION CARD", font=font(48, True), fill="white")
    draw.text((48, 130), "INDUSTRIAL WATER PUMP  /  LOCAL TEST DRAWING", font=font(32, True), fill="#243846")

    # Mechanical context: pump casing, motor, inlet/outlet, inspection gauge pipe.
    draw.rounded_rectangle((65, 965, 950, 1130), radius=18, fill="#76838b", outline="#38434a", width=5)
    draw.rectangle((95, 1115, 930, 1150), fill="#434f56")
    draw.ellipse((110, 920, 420, 1115), fill="#317d92", outline="#1c4d5d", width=8)
    draw.rectangle((392, 972, 875, 1090), fill="#286a80", outline="#183d4c", width=6)
    for x in range(440, 860, 35):
        draw.line((x, 985, x, 1077), fill="#173e50", width=7)
    draw.rectangle((65, 970, 145, 1040), fill="#a9b5bb", outline="#4b5960", width=5)
    draw.rectangle((205, 882, 280, 953), fill="#a9b5bb", outline="#4b5960", width=5)
    draw.rectangle((510, 855, 550, 977), fill="#b6bdc0", outline="#4b5960", width=5)

    cx, cy, radius = 530, 545, 330
    draw.ellipse((cx-radius-18, cy-radius-18, cx+radius+18, cy+radius+18), fill="#65747d", outline="#24323b", width=6)
    draw.ellipse((cx-radius, cy-radius, cx+radius, cy+radius), fill="#fbfaf5", outline="#aab0b2", width=10)

    def point(value, r):
        # 0 PSI at lower left, clockwise 270-degree sweep to 60 at lower right.
        angle = math.radians(135 + value * 270 / 60)
        return cx + math.cos(angle) * r, cy + math.sin(angle) * r

    for value in range(61):
        major = value % 5 == 0
        draw.line((*point(value, 303), *point(value, 275 if major else 288)), fill="#172b36", width=5 if major else 2)
        if major:
            x, y = point(value, 246)
            draw.text((x, y), str(value), font=font(33, True), fill="#172b36", anchor="mm")
    draw.text((cx, cy+105), "PSI", font=font(56, True), fill="#172b36", anchor="mm")
    draw.text((cx, cy+158), "PRESSURE  /  0 - 60", font=font(25), fill="#45545d", anchor="mm")
    # Needle tip lands exactly on the 35-PSI tick (292.5 degrees).
    tip = point(35, 270)
    tail = point(35, -63)
    draw.line((*tail, *tip), fill="#ac2028", width=9)
    draw.ellipse((cx-20, cy-20, cx+20, cy+20), fill="#263640", outline="#a5aeb2", width=4)

    def label(y, heading, value, size=54, color="#172b36"):
        draw.rounded_rectangle((1000, y, 1740, y+178), radius=12, fill="white", outline="#7b8a93", width=3)
        draw.text((1030, y+18), heading, font=font(28, True), fill="#566872")
        draw.text((1030, y+73), value, font=font(size, True), fill=color)

    challenge = "DEMO-7C4A-9F2B"  # Public fictional label, not an application challenge.
    label(210, "ASSET IDENTIFIER", "PUMP-042", 74)
    label(414, "EQUIPMENT STATUS", "RUNNING", 68, "#216843")
    label(618, "FICTIONAL SESSION CHALLENGE", challenge, 52)
    label(822, "CALIBRATION EXPIRY (YYYY-MM-DD)", "2099-12-31", 66)
    draw.text((1010, 1040), "Fictional values. No customer data.", font=font(28), fill="#394d59")
    draw.text((1010, 1085), "Not a photograph or safety certificate.", font=font(28), fill="#394d59")
    image.save(image_path, format="PNG")  # No EXIF, GPS, personal data or text metadata.
    truth = {
        "origin": "CONSENTED_FICTIONAL_NO_CUSTOMER_DATA",
        "human_reviewed": False,
        "human_review_sha256": None,
        "reviewed_by": "REPLACE_WITH_HUMAN_REVIEWER",
        "validation_model": "gemini-3.8-flash",
        "image_sha256": sha256(image_path.read_bytes()).hexdigest(),
        "image_description": "Locally drawn synthetic inspection card, not a photograph; human approval pending.",
        "expected_observation": {
            "asset_id_observed": "PUMP-042", "challenge_text_observed": challenge,
            "pressure_value": 35.0, "pressure_unit": "PSI", "equipment_status": "RUNNING",
            "calibration_expiry_date": "2099-12-31", "uncertain_fields": [], "conflicting_fields": []},
        "policy_context": {
            "tenant_id": "synthetic-org-a", "job_id": "synthetic-job-001",
            "asset_id_expected": "PUMP-042", "approved_policy_version": "1.0.0",
            "expected_challenge": challenge,
            "challenge_expires_at": "2026-11-12T23:59:59Z", "evaluated_at": "2026-11-12T06:00:00Z"},
        "drawing_reference": {"scale_min": 0, "scale_max": 60, "unit": "PSI",
            "needle_value": 35, "needle_angle_degrees": 292.5,
            "warning": "Construction reference is not human approval or a Gemini observation."}}
    truth_path.write_text(json.dumps(truth, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"image": str(image_path), "ground_truth": str(truth_path),
        "human_reviewed": False, "network_called": False, "origin": "LOCAL_PILLOW_SYNTHETIC_CARD"}))
    return image_path, truth_path


if __name__ == "__main__":
    prepare()
