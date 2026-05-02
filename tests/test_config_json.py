"""
Tests for JSON and project-configuration files in .snapshots/ and the root.

Validates that every JSON file is well-formed and that key configuration
files contain the expected fields and value types.
"""

import json
import os
import unittest

SNAPSHOTS_DIR = os.path.join(os.path.dirname(__file__), "..", ".snapshots")
ROOT_DIR = os.path.join(os.path.dirname(__file__), "..")


def _load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


class TestConfigJson(unittest.TestCase):
    """Tests for .snapshots/config.json — snapshot tool configuration."""

    @classmethod
    def setUpClass(cls):
        cls.config = _load_json(os.path.join(SNAPSHOTS_DIR, "config.json"))

    def test_is_dict(self):
        self.assertIsInstance(self.config, dict)

    def test_excluded_patterns_key_exists(self):
        self.assertIn("excluded_patterns", self.config)

    def test_excluded_patterns_is_list(self):
        self.assertIsInstance(self.config["excluded_patterns"], list)

    def test_excluded_patterns_not_empty(self):
        self.assertGreater(len(self.config["excluded_patterns"]), 0)

    def test_excluded_patterns_contains_git(self):
        self.assertIn(".git", self.config["excluded_patterns"])

    def test_excluded_patterns_contains_node_modules(self):
        self.assertIn("node_modules", self.config["excluded_patterns"])

    def test_included_patterns_key_exists(self):
        self.assertIn("included_patterns", self.config)

    def test_included_patterns_is_list(self):
        self.assertIsInstance(self.config["included_patterns"], list)

    def test_included_patterns_contains_package_json(self):
        self.assertIn("package.json", self.config["included_patterns"])

    def test_default_key_exists(self):
        self.assertIn("default", self.config)

    def test_default_is_dict(self):
        self.assertIsInstance(self.config["default"], dict)

    def test_default_prompt_key(self):
        self.assertIn("default_prompt", self.config["default"])

    def test_default_include_all_files_is_bool(self):
        self.assertIsInstance(
            self.config["default"]["default_include_all_files"], bool
        )

    def test_default_include_project_structure_is_bool(self):
        self.assertIsInstance(
            self.config["default"]["default_include_entire_project_structure"], bool
        )

    def test_all_excluded_patterns_are_strings(self):
        for pattern in self.config["excluded_patterns"]:
            self.assertIsInstance(pattern, str, f"Non-string pattern: {pattern!r}")

    def test_all_included_patterns_are_strings(self):
        for pattern in self.config["included_patterns"]:
            self.assertIsInstance(pattern, str, f"Non-string pattern: {pattern!r}")

    def test_no_duplicate_excluded_patterns(self):
        patterns = self.config["excluded_patterns"]
        self.assertEqual(len(patterns), len(set(patterns)))

    def test_no_duplicate_included_patterns(self):
        patterns = self.config["included_patterns"]
        self.assertEqual(len(patterns), len(set(patterns)))


class TestSnapshotsPackageJson(unittest.TestCase):
    """Tests for .snapshots/Package.json — snapshot directory package manifest."""

    @classmethod
    def setUpClass(cls):
        cls.pkg = _load_json(os.path.join(SNAPSHOTS_DIR, "Package.json"))

    def test_is_dict(self):
        self.assertIsInstance(self.pkg, dict)

    def test_name_field_exists(self):
        self.assertIn("name", self.pkg)

    def test_name_is_string(self):
        self.assertIsInstance(self.pkg["name"], str)

    def test_version_field_exists(self):
        self.assertIn("version", self.pkg)

    def test_version_is_semver_format(self):
        version = self.pkg["version"]
        parts = version.split(".")
        self.assertEqual(len(parts), 3, f"Version '{version}' is not semver")
        for part in parts:
            self.assertTrue(part.isdigit(), f"Non-numeric version segment: '{part}'")

    def test_scripts_field_exists(self):
        self.assertIn("scripts", self.pkg)

    def test_scripts_is_dict(self):
        self.assertIsInstance(self.pkg["scripts"], dict)

    def test_license_field_exists(self):
        self.assertIn("license", self.pkg)

    def test_dependencies_is_dict(self):
        self.assertIsInstance(self.pkg.get("dependencies", {}), dict)

    def test_dev_dependencies_is_dict(self):
        self.assertIsInstance(self.pkg.get("devDependencies", {}), dict)


class TestRootPackageJson(unittest.TestCase):
    """Tests for the root package.json — VS Code YAML extension manifest."""

    @classmethod
    def setUpClass(cls):
        cls.pkg = _load_json(os.path.join(ROOT_DIR, "package.json"))

    def test_is_dict(self):
        self.assertIsInstance(self.pkg, dict)

    def test_name_is_string(self):
        self.assertIsInstance(self.pkg["name"], str)

    def test_version_field_present(self):
        self.assertIn("version", self.pkg)

    def test_contributes_key_exists(self):
        self.assertIn("contributes", self.pkg)

    def test_contributes_languages_is_list(self):
        self.assertIsInstance(self.pkg["contributes"]["languages"], list)

    def test_contributes_languages_not_empty(self):
        self.assertGreater(len(self.pkg["contributes"]["languages"]), 0)

    def test_contributes_grammars_is_list(self):
        self.assertIsInstance(self.pkg["contributes"]["grammars"], list)

    def test_each_language_has_id(self):
        for lang in self.pkg["contributes"]["languages"]:
            self.assertIn("id", lang, f"Language entry missing 'id': {lang}")

    def test_each_grammar_has_scope_name(self):
        for grammar in self.pkg["contributes"]["grammars"]:
            self.assertIn("scopeName", grammar, f"Grammar entry missing 'scopeName': {grammar}")

    def test_engines_field_present(self):
        self.assertIn("engines", self.pkg)

    def test_yaml_language_present(self):
        ids = [lang["id"] for lang in self.pkg["contributes"]["languages"]]
        self.assertIn("yaml", ids)

    def test_dockercompose_language_present(self):
        ids = [lang["id"] for lang in self.pkg["contributes"]["languages"]]
        self.assertIn("dockercompose", ids)


class TestComposerJson(unittest.TestCase):
    """Tests for .snapshots/Composer.Json — PHP Composer manifest."""

    @classmethod
    def setUpClass(cls):
        cls.composer = _load_json(os.path.join(SNAPSHOTS_DIR, "Composer.Json"))

    def test_is_dict(self):
        self.assertIsInstance(self.composer, dict)

    def test_require_field_exists(self):
        self.assertIn("require", self.composer)

    def test_require_is_dict(self):
        self.assertIsInstance(self.composer["require"], dict)

    def test_php_version_constraint_present(self):
        self.assertIn("php", self.composer["require"])

    def test_php_version_is_string(self):
        self.assertIsInstance(self.composer["require"]["php"], str)

    def test_autoload_field_present(self):
        self.assertIn("autoload", self.composer)

    def test_require_dev_field_present(self):
        self.assertIn("require-dev", self.composer)

    def test_scripts_test_command(self):
        scripts = self.composer.get("scripts", {})
        self.assertIn("test", scripts)


class TestEslintrcJson(unittest.TestCase):
    """Tests for .snapshots/.eslintrc.json — ESLint configuration."""

    @classmethod
    def setUpClass(cls):
        cls.eslint = _load_json(os.path.join(SNAPSHOTS_DIR, ".eslintrc.json"))

    def test_is_dict(self):
        self.assertIsInstance(self.eslint, dict)

    def test_env_key_exists(self):
        self.assertIn("env", self.eslint)

    def test_env_browser_is_bool(self):
        self.assertIsInstance(self.eslint["env"].get("browser"), bool)

    def test_extends_is_list(self):
        self.assertIsInstance(self.eslint["extends"], list)

    def test_extends_not_empty(self):
        self.assertGreater(len(self.eslint["extends"]), 0)

    def test_rules_key_exists(self):
        self.assertIn("rules", self.eslint)

    def test_rules_is_dict(self):
        self.assertIsInstance(self.eslint["rules"], dict)

    def test_indent_rule_present(self):
        self.assertIn("indent", self.eslint["rules"])

    def test_semi_rule_present(self):
        self.assertIn("semi", self.eslint["rules"])

    def test_quotes_rule_present(self):
        self.assertIn("quotes", self.eslint["rules"])

    def test_parser_options_ecma_version(self):
        self.assertIn("parserOptions", self.eslint)
        self.assertIn("ecmaVersion", self.eslint["parserOptions"])
        self.assertIsInstance(self.eslint["parserOptions"]["ecmaVersion"], int)


if __name__ == "__main__":
    unittest.main()
