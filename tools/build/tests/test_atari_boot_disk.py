from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from nio_build.context import BuildContext
from nio_build.runner import Runner
from nio_build.tasks import Build, build_tasks


class AtariBootDiskTests(unittest.TestCase):
    def test_builds_both_config_variants_before_installing_disk(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = {name: str(root / name) for name in (
                "FUJINET_NIO_LIB", "NIO_CONFIG", "NIO_CORE_APPS", "FUJINET_NIO",
                "NIO_LOG_DIR", "NIO_IMAGE_DIR")}
            build = Build(BuildContext(root, env))
            build.runner = Mock(spec=Runner)
            build_tasks(build)["atari-boot-disk"].action(build)
            calls = build.runner.run.call_args_list
            self.assertEqual([call.args[0] for call in calls], [
                "lib-atari", "config-atari", "config-atari-banked", "boot-disk-atari"])
            self.assertIn("TARGET=atari", calls[1].args[1])
            self.assertIn("atari-banked", calls[2].args[1])
            self.assertIn("install-boot-disk", calls[3].args[1])


if __name__ == "__main__":
    unittest.main()
