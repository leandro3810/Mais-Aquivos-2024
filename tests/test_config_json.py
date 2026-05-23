"""
Testes para os arquivos de configuração JSON do projeto.

Valida que cada arquivo JSON está bem-formado e que os arquivos de
configuração principais contêm os campos e tipos esperados.

Arquivos cobertos
-----------------
- ``.snapshots/config.json``   — configuração da ferramenta de snapshot.
- ``.snapshots/Package.json``  — manifesto do diretório de snapshots.
- ``package.json``             — manifesto da extensão YAML para VS Code.
- ``.snapshots/Composer.Json`` — manifesto PHP Composer.
- ``.snapshots/.eslintrc.json``— configuração do ESLint.
"""

import json
import os
import unittest

# Caminhos absolutos calculados em relação ao diretório deste arquivo de testes.
SNAPSHOTS_DIR = os.path.join(os.path.dirname(__file__), "..", ".snapshots")
ROOT_DIR = os.path.join(os.path.dirname(__file__), "..")


def _load_json(path):
    """Abre e desserializa um arquivo JSON, retornando o objeto Python.

    Args:
        path: Caminho absoluto ou relativo para o arquivo ``.json``.

    Returns:
        Objeto Python (dict, list, etc.) resultante da desserialização.
    """
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# .snapshots/config.json
# ---------------------------------------------------------------------------


class TestConfigJson(unittest.TestCase):
    """Testa .snapshots/config.json — configuração da ferramenta de snapshot."""

    @classmethod
    def setUpClass(cls):
        """Carrega o arquivo uma única vez para todos os métodos da classe."""
        cls.config = _load_json(os.path.join(SNAPSHOTS_DIR, "config.json"))

    def test_is_dict(self):
        """O arquivo deve ser desserializado como dicionário."""
        self.assertIsInstance(self.config, dict)

    def test_excluded_patterns_key_exists(self):
        """Deve existir a chave 'excluded_patterns'."""
        self.assertIn("excluded_patterns", self.config)

    def test_excluded_patterns_is_list(self):
        """'excluded_patterns' deve ser uma lista."""
        self.assertIsInstance(self.config["excluded_patterns"], list)

    def test_excluded_patterns_not_empty(self):
        """A lista de padrões excluídos não pode estar vazia."""
        self.assertGreater(len(self.config["excluded_patterns"]), 0)

    def test_excluded_patterns_contains_git(self):
        """'.git' deve estar entre os padrões excluídos."""
        self.assertIn(".git", self.config["excluded_patterns"])

    def test_excluded_patterns_contains_node_modules(self):
        """'node_modules' deve estar entre os padrões excluídos."""
        self.assertIn("node_modules", self.config["excluded_patterns"])

    def test_included_patterns_key_exists(self):
        """Deve existir a chave 'included_patterns'."""
        self.assertIn("included_patterns", self.config)

    def test_included_patterns_is_list(self):
        """'included_patterns' deve ser uma lista."""
        self.assertIsInstance(self.config["included_patterns"], list)

    def test_included_patterns_contains_package_json(self):
        """'package.json' deve estar entre os padrões incluídos."""
        self.assertIn("package.json", self.config["included_patterns"])

    def test_default_key_exists(self):
        """Deve existir a chave 'default' com as configurações padrão."""
        self.assertIn("default", self.config)

    def test_default_is_dict(self):
        """'default' deve ser um dicionário."""
        self.assertIsInstance(self.config["default"], dict)

    def test_default_prompt_key(self):
        """'default_prompt' deve estar presente dentro de 'default'."""
        self.assertIn("default_prompt", self.config["default"])

    def test_default_include_all_files_is_bool(self):
        """'default_include_all_files' deve ser do tipo bool."""
        self.assertIsInstance(
            self.config["default"]["default_include_all_files"], bool
        )

    def test_default_include_project_structure_is_bool(self):
        """'default_include_entire_project_structure' deve ser do tipo bool."""
        self.assertIsInstance(
            self.config["default"]["default_include_entire_project_structure"], bool
        )

    def test_all_excluded_patterns_are_strings(self):
        """Todos os itens de 'excluded_patterns' devem ser strings."""
        for pattern in self.config["excluded_patterns"]:
            self.assertIsInstance(pattern, str, f"Padrão não-string: {pattern!r}")

    def test_all_included_patterns_are_strings(self):
        """Todos os itens de 'included_patterns' devem ser strings."""
        for pattern in self.config["included_patterns"]:
            self.assertIsInstance(pattern, str, f"Padrão não-string: {pattern!r}")

    def test_no_duplicate_excluded_patterns(self):
        """Não deve haver padrões duplicados em 'excluded_patterns'."""
        patterns = self.config["excluded_patterns"]
        self.assertEqual(len(patterns), len(set(patterns)))

    def test_no_duplicate_included_patterns(self):
        """Não deve haver padrões duplicados em 'included_patterns'."""
        patterns = self.config["included_patterns"]
        self.assertEqual(len(patterns), len(set(patterns)))


# ---------------------------------------------------------------------------
# .snapshots/Package.json
# ---------------------------------------------------------------------------


class TestSnapshotsPackageJson(unittest.TestCase):
    """Testa .snapshots/Package.json — manifesto do diretório de snapshots."""

    @classmethod
    def setUpClass(cls):
        """Carrega o arquivo uma única vez para todos os métodos da classe."""
        cls.pkg = _load_json(os.path.join(SNAPSHOTS_DIR, "Package.json"))

    def test_is_dict(self):
        """O manifesto deve ser um dicionário."""
        self.assertIsInstance(self.pkg, dict)

    def test_name_field_exists(self):
        """Deve existir o campo 'name'."""
        self.assertIn("name", self.pkg)

    def test_name_is_string(self):
        """'name' deve ser uma string."""
        self.assertIsInstance(self.pkg["name"], str)

    def test_version_field_exists(self):
        """Deve existir o campo 'version'."""
        self.assertIn("version", self.pkg)

    def test_version_is_semver_format(self):
        """'version' deve seguir o formato semver (MAJOR.MINOR.PATCH)."""
        version = self.pkg["version"]
        parts = version.split(".")
        self.assertEqual(len(parts), 3, f"Versão '{version}' não está no formato semver")
        for part in parts:
            self.assertTrue(part.isdigit(), f"Segmento de versão não-numérico: '{part}'")

    def test_scripts_field_exists(self):
        """Deve existir o campo 'scripts'."""
        self.assertIn("scripts", self.pkg)

    def test_scripts_is_dict(self):
        """'scripts' deve ser um dicionário."""
        self.assertIsInstance(self.pkg["scripts"], dict)

    def test_license_field_exists(self):
        """Deve existir o campo 'license'."""
        self.assertIn("license", self.pkg)

    def test_dependencies_is_dict(self):
        """'dependencies' (se presente) deve ser um dicionário."""
        self.assertIsInstance(self.pkg.get("dependencies", {}), dict)

    def test_dev_dependencies_is_dict(self):
        """'devDependencies' (se presente) deve ser um dicionário."""
        self.assertIsInstance(self.pkg.get("devDependencies", {}), dict)


# ---------------------------------------------------------------------------
# package.json (raiz)
# ---------------------------------------------------------------------------


class TestRootPackageJson(unittest.TestCase):
    """Testa o package.json da raiz — manifesto da extensão YAML para VS Code."""

    @classmethod
    def setUpClass(cls):
        """Carrega o arquivo uma única vez para todos os métodos da classe."""
        cls.pkg = _load_json(os.path.join(ROOT_DIR, "package.json"))

    def test_is_dict(self):
        """O manifesto deve ser um dicionário."""
        self.assertIsInstance(self.pkg, dict)

    def test_name_is_string(self):
        """'name' deve ser uma string."""
        self.assertIsInstance(self.pkg["name"], str)

    def test_version_field_present(self):
        """Deve existir o campo 'version'."""
        self.assertIn("version", self.pkg)

    def test_contributes_key_exists(self):
        """Deve existir a chave 'contributes' com as contribuições da extensão."""
        self.assertIn("contributes", self.pkg)

    def test_contributes_languages_is_list(self):
        """'contributes.languages' deve ser uma lista."""
        self.assertIsInstance(self.pkg["contributes"]["languages"], list)

    def test_contributes_languages_not_empty(self):
        """A lista de linguagens contribuídas não pode estar vazia."""
        self.assertGreater(len(self.pkg["contributes"]["languages"]), 0)

    def test_contributes_grammars_is_list(self):
        """'contributes.grammars' deve ser uma lista."""
        self.assertIsInstance(self.pkg["contributes"]["grammars"], list)

    def test_each_language_has_id(self):
        """Cada entrada em 'contributes.languages' deve ter o campo 'id'."""
        for lang in self.pkg["contributes"]["languages"]:
            self.assertIn("id", lang, f"Entrada de linguagem sem 'id': {lang}")

    def test_each_grammar_has_scope_name(self):
        """Cada entrada em 'contributes.grammars' deve ter o campo 'scopeName'."""
        for grammar in self.pkg["contributes"]["grammars"]:
            self.assertIn("scopeName", grammar, f"Entrada de gramática sem 'scopeName': {grammar}")

    def test_engines_field_present(self):
        """Deve existir o campo 'engines' especificando a versão mínima do VS Code."""
        self.assertIn("engines", self.pkg)

    def test_yaml_language_present(self):
        """A linguagem 'yaml' deve estar registrada nas contribuições."""
        ids = [lang["id"] for lang in self.pkg["contributes"]["languages"]]
        self.assertIn("yaml", ids)

    def test_dockercompose_language_present(self):
        """A linguagem 'dockercompose' deve estar registrada nas contribuições."""
        ids = [lang["id"] for lang in self.pkg["contributes"]["languages"]]
        self.assertIn("dockercompose", ids)


# ---------------------------------------------------------------------------
# .snapshots/Composer.Json
# ---------------------------------------------------------------------------


class TestComposerJson(unittest.TestCase):
    """Testa .snapshots/Composer.Json — manifesto PHP Composer."""

    @classmethod
    def setUpClass(cls):
        """Carrega o arquivo uma única vez para todos os métodos da classe."""
        cls.composer = _load_json(os.path.join(SNAPSHOTS_DIR, "Composer.Json"))

    def test_is_dict(self):
        """O manifesto deve ser um dicionário."""
        self.assertIsInstance(self.composer, dict)

    def test_require_field_exists(self):
        """Deve existir o campo 'require' com as dependências do projeto."""
        self.assertIn("require", self.composer)

    def test_require_is_dict(self):
        """'require' deve ser um dicionário."""
        self.assertIsInstance(self.composer["require"], dict)

    def test_php_version_constraint_present(self):
        """A chave 'php' com a restrição de versão deve estar em 'require'."""
        self.assertIn("php", self.composer["require"])

    def test_php_version_is_string(self):
        """A restrição de versão do PHP deve ser uma string."""
        self.assertIsInstance(self.composer["require"]["php"], str)

    def test_autoload_field_present(self):
        """Deve existir o campo 'autoload'."""
        self.assertIn("autoload", self.composer)

    def test_require_dev_field_present(self):
        """Deve existir o campo 'require-dev' para dependências de desenvolvimento."""
        self.assertIn("require-dev", self.composer)

    def test_scripts_test_command(self):
        """O campo 'scripts.test' deve estar presente para execução de testes."""
        scripts = self.composer.get("scripts", {})
        self.assertIn("test", scripts)


# ---------------------------------------------------------------------------
# .snapshots/.eslintrc.json
# ---------------------------------------------------------------------------


class TestEslintrcJson(unittest.TestCase):
    """Testa .snapshots/.eslintrc.json — configuração do ESLint."""

    @classmethod
    def setUpClass(cls):
        """Carrega o arquivo uma única vez para todos os métodos da classe."""
        cls.eslint = _load_json(os.path.join(SNAPSHOTS_DIR, ".eslintrc.json"))

    def test_is_dict(self):
        """O arquivo de configuração deve ser um dicionário."""
        self.assertIsInstance(self.eslint, dict)

    def test_env_key_exists(self):
        """Deve existir a chave 'env' com os ambientes habilitados."""
        self.assertIn("env", self.eslint)

    def test_env_browser_is_bool(self):
        """'env.browser' deve ser um valor booleano."""
        self.assertIsInstance(self.eslint["env"].get("browser"), bool)

    def test_extends_is_list(self):
        """'extends' deve ser uma lista de configurações herdadas."""
        self.assertIsInstance(self.eslint["extends"], list)

    def test_extends_not_empty(self):
        """A lista 'extends' não pode estar vazia."""
        self.assertGreater(len(self.eslint["extends"]), 0)

    def test_rules_key_exists(self):
        """Deve existir a chave 'rules' com as regras do linter."""
        self.assertIn("rules", self.eslint)

    def test_rules_is_dict(self):
        """'rules' deve ser um dicionário."""
        self.assertIsInstance(self.eslint["rules"], dict)

    def test_indent_rule_present(self):
        """A regra 'indent' deve estar configurada."""
        self.assertIn("indent", self.eslint["rules"])

    def test_semi_rule_present(self):
        """A regra 'semi' (ponto-e-vírgula) deve estar configurada."""
        self.assertIn("semi", self.eslint["rules"])

    def test_quotes_rule_present(self):
        """A regra 'quotes' (aspas) deve estar configurada."""
        self.assertIn("quotes", self.eslint["rules"])

    def test_parser_options_ecma_version(self):
        """'parserOptions.ecmaVersion' deve estar presente e ser um inteiro."""
        self.assertIn("parserOptions", self.eslint)
        self.assertIn("ecmaVersion", self.eslint["parserOptions"])
        self.assertIsInstance(self.eslint["parserOptions"]["ecmaVersion"], int)


if __name__ == "__main__":
    unittest.main()
