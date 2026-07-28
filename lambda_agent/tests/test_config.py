import importlib
import os
import unittest


class ConfigImportTests(unittest.TestCase):
    def test_config_import_does_not_fail_without_gemini_key(self):
        original_value = os.environ.get("GEMINI_API_KEY")
        os.environ["GEMINI_API_KEY"] = ""

        import config

        importlib.reload(config)

        self.assertIsNone(config.GEMINI_API_KEY)

        if original_value is None:
            os.environ.pop("GEMINI_API_KEY", None)
        else:
            os.environ["GEMINI_API_KEY"] = original_value


if __name__ == "__main__":
    unittest.main()
