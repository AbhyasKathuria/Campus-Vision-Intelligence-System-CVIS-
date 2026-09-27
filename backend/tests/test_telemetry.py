import unittest
from collections import Counter
from app.models.enums import RejectionReasonType

class TestTelemetryCalculations(unittest.TestCase):
    def test_small_sample_size_guard(self):
        min_sample_size = 15

        # Scenario 1: Camera A with low sample size (2 reviewed, 1 rejected)
        # Even though rejected / total is 50%, sample size N=2 is below threshold (15)
        # It must report status_label="insufficient_data", fpr_percentage=None, and NO calibration alert
        cam_a_total = 2
        cam_a_rejected = 1
        cam_a_leading_reason = RejectionReasonType.LIGHTING_CONTRAST_ARTIFACT.value

        if cam_a_total >= min_sample_size:
            cam_a_fpr = round((cam_a_rejected / cam_a_total) * 100.0, 2)
            cam_a_status = "calibrated"
            recommend_calibration_a = False
            if cam_a_fpr >= 35.0 and cam_a_leading_reason == RejectionReasonType.LIGHTING_CONTRAST_ARTIFACT.value:
                recommend_calibration_a = True
                cam_a_status = "calibration_recommended"
        else:
            cam_a_fpr = None
            cam_a_status = "insufficient_data"
            recommend_calibration_a = False

        self.assertIsNone(cam_a_fpr, "Low sample size should yield None for FPR percentage.")
        self.assertEqual(cam_a_status, "insufficient_data", "Low sample size must report insufficient_data status.")
        self.assertFalse(recommend_calibration_a, "Low sample size must not trigger environmental calibration alert.")

        # Scenario 2: Camera B with statistical significance (16 reviewed, 8 rejected)
        cam_b_total = 16
        cam_b_rejected = 8
        cam_b_leading_reason = RejectionReasonType.LIGHTING_CONTRAST_ARTIFACT.value

        if cam_b_total >= min_sample_size:
            cam_b_fpr = round((cam_b_rejected / cam_b_total) * 100.0, 2)
            cam_b_status = "calibrated"
            recommend_calibration_b = False
            if cam_b_fpr >= 35.0 and cam_b_leading_reason == RejectionReasonType.LIGHTING_CONTRAST_ARTIFACT.value:
                recommend_calibration_b = True
                cam_b_status = "calibration_recommended"
        else:
            cam_b_fpr = None
            cam_b_status = "insufficient_data"
            recommend_calibration_b = False

        self.assertEqual(cam_b_fpr, 50.0)
        self.assertEqual(cam_b_status, "calibration_recommended")
        self.assertTrue(recommend_calibration_b, "Sufficient sample size with high lighting FPR must trigger calibration alert.")

    def test_rejection_reason_enum_aggregation(self):
        rejections = [
            RejectionReasonType.LIGHTING_CONTRAST_ARTIFACT.value,
            RejectionReasonType.LIGHTING_CONTRAST_ARTIFACT.value,
            RejectionReasonType.FALSE_POSITIVE_CLOTHING.value,
            RejectionReasonType.STUDENT_POSTURE_ANGLE.value,
        ]
        counts = Counter(rejections)
        self.assertEqual(counts[RejectionReasonType.LIGHTING_CONTRAST_ARTIFACT.value], 2)
        self.assertEqual(counts[RejectionReasonType.FALSE_POSITIVE_CLOTHING.value], 1)
        self.assertEqual(counts[RejectionReasonType.STUDENT_POSTURE_ANGLE.value], 1)
        self.assertEqual(counts[RejectionReasonType.NO_VIOLATION_FOUND.value], 0)

if __name__ == "__main__":
    unittest.main()
