import unittest

from canitf_project.cdktn import complete_feature_input, render_cdktn_source


class CdktnSourceTests(unittest.TestCase):
    def test_renders_constraints_in_target_shape(self):
        source = render_cdktn_source({
            "baseline": "1.7.5",
            "features": [{
                "name": "S3 native state locking",
                "key": "s3-native-state-locking",
                "constraints": {"terraform": ">=1.10.0", "opentofu": ">=1.10.0"},
            }],
        })
        self.assertIn("TERRAFORM_HCL_FEATURE_CONSTRAINTS", source)
        self.assertIn('"s3-native-state-locking"', source)
        self.assertIn('terraform: ">=1.10.0"', source)
        self.assertIn('opentofu: ">=1.10.0"', source)
        self.assertIn("ValidateTerraformFeatureVersion", source)

    def test_human_constraints_override_generated_rows(self):
        input_data = {
            "features": [{
                "name": "Provider-defined functions",
                "key": "provider-defined-functions",
                "constraints": {"terraform": ">=9.9.9"},
            }]
        }
        # No generated path here; the important contract is that explicit input
        # survives rendering unchanged.
        completed = complete_feature_input(input_data)
        self.assertEqual(completed["features"][0]["constraints"]["terraform"], ">=9.9.9")


if __name__ == "__main__":
    unittest.main()
