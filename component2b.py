import pytest

class SpikeDetector:
    """CUSUM algorithm for detecting shifts in fraud rate with state isolation for testing."""
    def __init__(self, threshold: float = 1.5, drift: float = 0.1, baseline: float = 0.02):
        self.threshold = threshold
        self.drift = drift
        self.mean_fraud_rate = baseline
        self.pos_cusum = 0.0

    def reset(self) -> None:
        """Resets internal state for test isolation."""
        self.pos_cusum = 0.0

    def detect_spike(self, current_fraud_rate: float) -> dict:
        deviation = current_fraud_rate - self.mean_fraud_rate - self.drift
        self.pos_cusum = max(0.0, self.pos_cusum + deviation)
        is_spike = self.pos_cusum > self.threshold
        current_val = round(self.pos_cusum, 4)
        
        if is_spike:
            self.pos_cusum = 0.0
            
        return {
            "alert": is_spike,
            "current_cusum_value": current_val,
            "threshold": self.threshold
        }

@pytest.fixture
def detector():
    return SpikeDetector(threshold=1.5, drift=0.1, baseline=0.02)

def test_normal_background_noise(detector):
    for rate in [0.02, 0.03, 0.01]:
        result = detector.detect_spike(rate)
        assert not result["alert"]

def test_fraud_spike_triggers_alert(detector):
    detector.detect_spike(0.50)
    result = detector.detect_spike(0.80)
    assert result["alert"] is True
    assert detector.pos_cusum == 0.0

def test_manual_reset(detector):
    detector.detect_spike(0.80)
    detector.reset()
    assert detector.pos_cusum == 0.0