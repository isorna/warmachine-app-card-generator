import importlib.util, tempfile, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('builder',HERE/'build-print-profiles.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)

class MediaPathTest(unittest.TestCase):
    def test_alternative_cache_and_path_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);app=root/'data';cache=app/'public-42';cache.mkdir(parents=True)
            (cache/'test.bundle').touch();(cache/'Media').mkdir();(cache/'Media/icon.png').write_bytes(b'test-image')
            out=root/'out';out.mkdir();b=builder.Builder({},app,out)
            target=b.asset('/Media/icon.png')
            self.assertEqual((out/target).read_bytes(),b'test-image')
            with self.assertRaises(ValueError):b.asset('/../../outside.png')
