import cv2
import numpy as np
from typing import Dict, Any, Optional
from app.schemas.models import ComplianceViolationResult

class ComplianceClassifier:
    """
    Modular dress-code & ID compliance heuristic engine.
    Analyzes body/torso crops for:
    - Untucked shirt (waistband transition line & hanging hem gradients)
    - Casual attire (collar presence vs round-neck / t-shirt texture)
    - Missing ID badge (chest quadrant edge and lanyard gradient)
    - Missing lab coat (high-luminance coverage ratio)
    """

    def analyze_clothing(
        self,
        image_bytes: bytes,
        target_check: Optional[str] = None
    ) -> ComplianceViolationResult:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return ComplianceViolationResult(
                violation_detected=False,
                violation_type="untucked_shirt",
                violation_confidence=0.0,
                features={"error": "Invalid image data"},
                summary="Unable to process body crop."
            )

        h, w, _ = img.shape
        if h < 40 or w < 20:
            return ComplianceViolationResult(
                violation_detected=False,
                violation_type="untucked_shirt",
                violation_confidence=0.0,
                features={"error": "Crop too small for analysis"},
                summary="Body crop resolution insufficient."
            )

        # Standardize body crop to 200x400
        standard = cv2.resize(img, (200, 400))
        gray = cv2.cvtColor(standard, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(standard, cv2.COLOR_BGR2HSV)

        # Feature 1: Collar detection (Upper torso: Y 50 to 120, X 60 to 140)
        collar_roi = gray[50:120, 60:140]
        collar_edges = cv2.Canny(collar_roi, 50, 150)
        # Look for diagonal / V-lines typical of collars
        lines = cv2.HoughLinesP(collar_edges, 1, np.pi/180, threshold=20, minLineLength=15, maxLineGap=5)
        has_collar_lines = lines is not None and len(lines) >= 2
        collar_score = float(np.mean(collar_edges) / 255.0)

        # Feature 2: Waistband transition detection (Y 240 to 320, full width)
        waist_roi = gray[240:320, 30:170]
        # Horizontal Sobel filter to detect tuck line / belt
        sobel_h = cv2.Sobel(waist_roi, cv2.CV_32F, 0, 1, ksize=3)
        horizontal_line_strength = float(np.max(np.abs(sobel_h)))
        mean_waist_gradient = float(np.mean(np.abs(sobel_h)))
        
        # Color difference between upper shirt (Y 140:220) and lower pants (Y 280:360)
        upper_mean_val = float(np.mean(gray[140:220, 40:160]))
        lower_mean_val = float(np.mean(gray[280:360, 40:160]))
        contrast_diff = abs(upper_mean_val - lower_mean_val)
        
        # Untucked shirts typically have irregular jagged hem lines lower down (Y 300:340)
        lower_hem_roi = gray[300:350, 40:160]
        lower_hem_std = float(np.std(lower_hem_roi))
        
        is_untucked = mean_waist_gradient < 15.0 or (lower_hem_std > 38.0 and contrast_diff < 25.0)
        untucked_confidence = min(0.92, max(0.40, 0.50 + (lower_hem_std / 100.0) * 0.40))

        # Feature 3: ID badge detection in left or center chest (Y 100 to 200, X 40 to 110)
        chest_roi = gray[100:200, 40:110]
        chest_edges = cv2.Canny(chest_roi, 40, 120)
        contours, _ = cv2.findContours(chest_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        badge_detected = False
        for c in contours:
            bx, by, bw, bh = cv2.boundingRect(c)
            # Badges are typically rectangular aspect ratio (1.2 to 1.8)
            if 15 < bw < 45 and 20 < bh < 60:
                aspect = bh / float(bw)
                if 1.1 <= aspect <= 2.2:
                    badge_detected = True
                    break
        badge_confidence = 0.85 if not badge_detected else 0.20

        # Feature 4: Lab coat detection (high brightness, low saturation over torso Y 80 to 320)
        torso_s = hsv[80:320, 30:170, 1]
        torso_v = hsv[80:320, 30:170, 2]
        white_pixels = np.sum((torso_s < 45) & (torso_v > 175))
        total_pixels = torso_s.size
        white_ratio = float(white_pixels / total_pixels)
        lab_coat_missing = white_ratio < 0.40

        # Construct comprehensive features breakdown dictionary
        features = {
            "collar_detected": bool(has_collar_lines),
            "collar_gradient_score": round(collar_score, 3),
            "waistband_edge_gradient": round(mean_waist_gradient, 2),
            "waistband_max_edge": round(horizontal_line_strength, 2),
            "torso_contrast_difference": round(contrast_diff, 2),
            "lower_hem_dispersion": round(lower_hem_std, 2),
            "id_badge_detected": bool(badge_detected),
            "white_coat_coverage_ratio": round(white_ratio, 3)
        }

        # Determine primary violation based on target check or highest confidence heuristic
        if target_check == "lab_coat_missing":
            return ComplianceViolationResult(
                violation_detected=lab_coat_missing,
                violation_type="lab_coat_missing",
                violation_confidence=round(min(0.95, max(0.50, 1.0 - white_ratio)), 3),
                features=features,
                summary=f"Lab coat coverage is {round(white_ratio*100, 1)}% (minimum requirement: 40%)."
            )

        if target_check == "no_id_badge" or (not badge_detected and badge_confidence >= 0.70):
            return ComplianceViolationResult(
                violation_detected=not badge_detected,
                violation_type="no_id_badge",
                violation_confidence=round(badge_confidence, 3),
                features=features,
                summary="No identification badge or lanyard contour detected on chest quadrant."
            )

        if not has_collar_lines and collar_score < 0.05:
            return ComplianceViolationResult(
                violation_detected=True,
                violation_type="casual_attire",
                violation_confidence=0.74,
                features=features,
                summary="No formal collar or folded lapel detected (casual round-neck/t-shirt signature)."
            )

        # Default to untucked shirt check
        return ComplianceViolationResult(
            violation_detected=is_untucked,
            violation_type="untucked_shirt",
            violation_confidence=round(untucked_confidence, 3),
            features=features,
            summary=(
                "Untucked shirt pattern: low waistline demarcation and irregular lower hem dispersion."
                if is_untucked else "Shirt appears properly tucked; waistline transition clear."
            )
        )

classifier = ComplianceClassifier()
