import sys, tempfile, unittest, json
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app_paths as paths

class PathsTest(unittest.TestCase):
    def fixture(self, root):
        install = root / "custom disk" / "Warmachine"
        (install / "Warmachine App_Data").mkdir(parents=True)
        (install / "Warmachine App.exe").touch()
        (install / "Warmachine App_Data/resources.assets").touch()
        data = root / "different user data"
        (data / "public-21").mkdir(parents=True)
        (data / "public-21/test.bundle").touch()
        return install, data

    def test_explicit_paths_and_save_without_console(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); install, data = self.fixture(root); cfg = root / "config.json"
            with patch("sys.stdin.isatty", return_value=False):
                self.assertEqual(paths.resolve_paths(install, data, True, cfg), (install.resolve(), data.resolve()))
            self.assertEqual(paths.resolve_paths(config_path=cfg), (install.resolve(), data.resolve()))
            self.assertEqual(paths.public_cache(data).name, "public-21")

    def test_cli_overrides_stale_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); install, data = self.fixture(root); cfg = root / "config.json"
            cfg.write_text(json.dumps({"app_install":"missing", "app_data":"missing"}))
            self.assertEqual(paths.resolve_paths(install, data, config_path=cfg), (install.resolve(), data.resolve()))
            with self.assertRaises(ValueError): paths.resolve_paths(config_path=cfg)

    def test_ambiguous_install_requires_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); install, data = self.fixture(root)
            with patch.object(paths, "detected_installs", return_value=[install, install / "other"]):
                with self.assertRaises(ValueError): paths.resolve_paths(app_data=data, config_path=root / "absent")

    def test_empty_and_ambiguous_cache_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ValueError): paths.public_cache(root)
            for name in ("public-20", "public-21"):
                (root / name).mkdir(); (root / name / "test.bundle").touch()
            with self.assertRaises(ValueError): paths.public_cache(root)

    def test_invalid_install_and_malformed_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertFalse(paths.valid_install(root))
            cfg = root / "config.json"
            cfg.write_text('{"app_install": 42}')
            with self.assertRaises(ValueError): paths.load_config(cfg)

    def test_detection_deduplicates_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            install, _ = self.fixture(Path(tmp))
            with patch.object(paths, "registry_installs", return_value=[install, install]), patch.dict(paths.os.environ, {}, clear=True):
                self.assertEqual(paths.detected_installs(), [install.resolve()])

    def test_explicit_configuration_never_prompts_even_on_tty(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); install, data = self.fixture(root)
            with patch("sys.stdin.isatty", return_value=True), patch("builtins.input", side_effect=AssertionError("unexpected prompt")):
                paths.resolve_paths(install, data, True, root / "config.json")

    def test_wizard_accepts_detected_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); install, data = self.fixture(root)
            with patch("sys.stdin.isatty", return_value=True), patch("builtins.input", side_effect=["", ""]), patch.object(paths, "detected_installs", return_value=[install]), patch.object(paths, "default_data", return_value=data):
                self.assertEqual(paths.resolve_paths(configure=True, config_path=root / "config.json"), (install.resolve(), data.resolve()))
