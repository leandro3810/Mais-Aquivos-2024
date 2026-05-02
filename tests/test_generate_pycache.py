"""
Tests for .snapshots/Generate_pycache.py

The script scans the current working directory for .py files and compiles
each one (excluding itself) into __pycache__ using py_compile.
"""

import importlib
import os
import runpy
import sys
import unittest
from io import StringIO
from unittest.mock import MagicMock, call, patch


SCRIPT_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    ".snapshots",
    "Generate_pycache.py",
)


def _run_script(fake_cwd, fake_files):
    """Helper: run the script with a mocked filesystem and return stdout."""
    buf = StringIO()
    with patch("os.getcwd", return_value=fake_cwd), \
         patch("os.listdir", return_value=fake_files), \
         patch("py_compile.compile") as mock_compile, \
         patch("sys.stdout", buf):
        runpy.run_path(SCRIPT_PATH)
    return buf.getvalue(), mock_compile


class TestGeneratePycache(unittest.TestCase):

    def test_compiles_single_python_file(self):
        """A single .py file (not the script itself) should be compiled."""
        output, mock_compile = _run_script("/fake/dir", ["mymodule.py"])

        mock_compile.assert_called_once_with(
            "mymodule.py", cfile="__pycache__/mymodule.pyc"
        )
        self.assertIn("Compilando mymodule.py", output)
        self.assertIn("Compilação concluída", output)

    def test_compiles_multiple_python_files(self):
        """All .py files other than the script itself should be compiled."""
        files = ["alpha.py", "beta.py", "gamma.py"]
        output, mock_compile = _run_script("/fake/dir", files)

        self.assertEqual(mock_compile.call_count, 3)
        expected_calls = [
            call("alpha.py", cfile="__pycache__/alpha.pyc"),
            call("beta.py", cfile="__pycache__/beta.pyc"),
            call("gamma.py", cfile="__pycache__/gamma.pyc"),
        ]
        mock_compile.assert_has_calls(expected_calls, any_order=True)
        for name in files:
            self.assertIn(f"Compilando {name}", output)

    def test_skips_lowercase_generate_pycache(self):
        """The script excludes 'generate_pycache.py' (lowercase) by name."""
        output, mock_compile = _run_script(
            "/fake/dir", ["generate_pycache.py", "util.py"]
        )

        # util.py must be compiled; generate_pycache.py must be skipped
        mock_compile.assert_called_once_with(
            "util.py", cfile="__pycache__/util.pyc"
        )
        self.assertNotIn("Compilando generate_pycache.py", output)

    def test_ignores_non_python_files(self):
        """Non-.py files (txt, json, xml, …) should not be compiled."""
        files = ["README.txt", "config.json", "data.xml", "image.png"]
        output, mock_compile = _run_script("/fake/dir", files)

        mock_compile.assert_not_called()
        self.assertIn("Compilação concluída", output)

    def test_empty_directory(self):
        """An empty directory should produce no compile calls."""
        output, mock_compile = _run_script("/fake/empty", [])

        mock_compile.assert_not_called()
        self.assertIn("Compilação concluída", output)

    def test_mixed_file_types(self):
        """Only .py files (except the script name) are compiled."""
        files = [
            "app.py",
            "utils.py",
            "notes.txt",
            "schema.json",
            "generate_pycache.py",
        ]
        output, mock_compile = _run_script("/fake/dir", files)

        self.assertEqual(mock_compile.call_count, 2)
        compiled = {c.args[0] for c in mock_compile.call_args_list}
        self.assertSetEqual(compiled, {"app.py", "utils.py"})

    def test_cfile_path_uses_pycache_subdir(self):
        """Compiled output paths are always inside __pycache__/."""
        output, mock_compile = _run_script("/proj", ["service.py"])

        _, kwargs = mock_compile.call_args
        self.assertTrue(
            mock_compile.call_args.kwargs.get("cfile", "").startswith("__pycache__/")
            or mock_compile.call_args.args[1].startswith("__pycache__/")
            if len(mock_compile.call_args.args) > 1
            else mock_compile.call_args.kwargs["cfile"].startswith("__pycache__/")
        )

    def test_output_message_contains_filename(self):
        """Each compiled file name appears in the printed progress line."""
        output, _ = _run_script("/fake", ["parser.py"])
        self.assertIn("parser.py", output)

    def test_completion_message_always_printed(self):
        """The final completion message is always printed, even with no files."""
        output, _ = _run_script("/empty", [])
        self.assertIn("Compilação concluída", output)
        self.assertIn("__pycache__", output)


if __name__ == "__main__":
    unittest.main()
