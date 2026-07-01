import unittest

from voyage_checker import Decision, VoyageConditions, assess_voyage


class VoyageCheckerTests(unittest.TestCase):
    def conditions(self, **changes):
        values = dict(wind_speed_ms=5, wave_height_m=1, visibility_km=5, vessel_length_m=20)
        values.update(changes)
        return VoyageConditions(**values)

    def test_allowed(self):
        self.assertEqual(assess_voyage(self.conditions()).decision, Decision.ALLOWED)

    def test_conditional(self):
        result = assess_voyage(self.conditions(wind_speed_ms=11))
        self.assertEqual(result.decision, Decision.CONDITIONAL)

    def test_weather_warning_prohibits(self):
        result = assess_voyage(self.conditions(weather_warning=True))
        self.assertEqual(result.decision, Decision.PROHIBITED)

    def test_equipment_fault_prohibits(self):
        result = assess_voyage(self.conditions(engine_ok=False))
        self.assertEqual(result.decision, Decision.PROHIBITED)

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            assess_voyage(self.conditions(wave_height_m=-1))


if __name__ == "__main__":
    unittest.main()
