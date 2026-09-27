from __future__ import annotations

import hashlib
import importlib.machinery
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def load_amiga_env_module():
    loader = importlib.machinery.SourceFileLoader(
        "amiga_env_under_test", str(ROOT / "scripts" / "amiga-env")
    )
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class PrebuiltHdfEnvironmentTests(unittest.TestCase):
    def test_machine_keyed_prebuilt_hdf_copies_without_mutating_source(self) -> None:
        amiga_env = load_amiga_env_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            recipes = root / "recipes"
            machines = root / "machines"
            environments = root / "environments"
            local_env = root / "amiga.env"
            recipes.mkdir()
            machines.mkdir()
            source = root / "source.hdf"
            kickstart = root / "kick13.rom"
            source.write_bytes(b"prepared-ofs-hdf")
            kickstart.write_bytes(b"kickstart")
            source_digest = hashlib.sha256(source.read_bytes()).hexdigest()
            (recipes / "wb13.yaml").write_text(
                "id: wb13\n"
                "kickstart_var: AMIGA_WB13_KICKSTART\n"
                "assembly:\n"
                "  method: prebuilt_hdf\n"
                "  machine: required\n"
                "  source_hdf_var: AMIGA_WB13_HDF\n",
                encoding="utf-8",
            )
            (machines / "a500-000.yaml").write_text("id: a500-000\n", encoding="utf-8")
            local_env.write_text(
                f"AMIGA_WB13_KICKSTART={kickstart}\nAMIGA_WB13_HDF={source}\n",
                encoding="utf-8",
            )

            amiga_env.RECIPES_DIR = recipes
            amiga_env.MACHINES_DIR = machines
            amiga_env.ENVS_DIR = environments
            amiga_env.LOCAL_AMIGA_ENV = local_env
            amiga_env.cmd_build("wb13", force=False, machine_id="a500-000")

            base_hdf = environments / "wb13" / "a500-000" / "base.hdf"
            manifest = json.loads(
                (environments / "wb13" / "a500-000" / "manifest.json").read_text()
            )
            self.assertEqual(base_hdf.read_bytes(), b"prepared-ofs-hdf")
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), source_digest)
            self.assertEqual(manifest["machine"], "a500-000")
            self.assertIsNone(manifest["fast_file_system"])

