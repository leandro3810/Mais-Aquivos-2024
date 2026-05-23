"""
Testes para as folhas de estilo XSLT no diretório App.xsl/.

Cada teste aplica uma folha de estilo a um documento XML de exemplo e
verifica que o conteúdo esperado aparece no resultado transformado.  Todas
as folhas de estilo usam XSLT 1.0 e são processadas via ``lxml.etree.XSLT``.

Nota
----
``appcompat_delailed_bidi.xsl`` declara ``version="2.0"``, que não é
suportado pelo lxml.  Esse arquivo é testado apenas para verificar se é
XML bem-formado e contém os elementos esperados de uma folha de estilo.
"""

import os
import textwrap
import unittest

from lxml import etree

# Diretório raiz das folhas de estilo XSL.
XSL_DIR = os.path.join(os.path.dirname(__file__), "..", "App.xsl")


def _load_xslt(filename):
    """Carrega e compila um arquivo XSL, retornando um transformador XSLT.

    Args:
        filename: Nome do arquivo ``.xsl`` dentro de ``XSL_DIR``.

    Returns:
        Instância de ``lxml.etree.XSLT`` pronta para transformar documentos.
    """
    xsl_path = os.path.join(XSL_DIR, filename)
    with open(xsl_path, "rb") as fh:
        xsl_doc = etree.parse(fh)
    return etree.XSLT(xsl_doc)


def _transform(xslt, xml_string, **params):
    """Aplica *xslt* ao documento XML e retorna o resultado como string.

    Args:
        xslt: Transformador ``lxml.etree.XSLT`` criado por ``_load_xslt``.
        xml_string: Documento XML como bytes.
        **params: Parâmetros XSLT passados diretamente para o transformador.

    Returns:
        Resultado da transformação como string UTF-8.
    """
    source = etree.fromstring(xml_string)
    result = xslt(source, **params)
    return str(result)


# ---------------------------------------------------------------------------
# Appcompat.xsl
# ---------------------------------------------------------------------------


class TestAppcompatXsl(unittest.TestCase):
    """Testa Appcompat.xsl — transforma elementos app em uma tabela HTML."""

    @classmethod
    def setUpClass(cls):
        """Compila a folha de estilo uma única vez para todos os testes."""
        cls.xslt = _load_xslt("Appcompat.xsl")

    def _xml(self, apps):
        """Gera um documento XML <apps> com os dados fornecidos.

        Args:
            apps: Lista de tuplas ``(nome, versão, status)``.

        Returns:
            Documento XML como bytes.
        """
        rows = "".join(
            f"<app><name>{a}</name><version>{v}</version>"
            f"<status>{s}</status></app>"
            for a, v, s in apps
        )
        return f"<apps>{rows}</apps>".encode()

    def test_produces_html_output(self):
        """A transformação deve produzir um documento HTML."""
        result = _transform(self.xslt, self._xml([("App One", "1.0", "Compatible")]))
        self.assertIn("<html", result.lower())

    def test_title_in_output(self):
        """O título 'App Compatibility Report' deve estar no HTML gerado."""
        result = _transform(self.xslt, self._xml([]))
        self.assertIn("App Compatibility Report", result)

    def test_table_headers_present(self):
        """Os cabeçalhos da tabela (App Name, Version, Status) devem estar presentes."""
        result = _transform(self.xslt, self._xml([]))
        self.assertIn("App Name", result)
        self.assertIn("Version", result)
        self.assertIn("Status", result)

    def test_single_app_row(self):
        """Um único app deve gerar uma linha com nome, versão e status."""
        result = _transform(self.xslt, self._xml([("MyApp", "2.0", "Compatible")]))
        self.assertIn("MyApp", result)
        self.assertIn("2.0", result)
        self.assertIn("Compatible", result)

    def test_multiple_app_rows(self):
        """Vários apps devem gerar linhas correspondentes na tabela."""
        apps = [
            ("Alpha", "1.0", "Compatible"),
            ("Beta", "2.1", "Incompatible"),
            ("Gamma", "3.5", "Partial"),
        ]
        result = _transform(self.xslt, self._xml(apps))
        for name, version, status in apps:
            self.assertIn(name, result)
            self.assertIn(version, result)
            self.assertIn(status, result)

    def test_empty_apps_list(self):
        """Um elemento <apps> vazio deve produzir uma página HTML válida com tabela."""
        result = _transform(self.xslt, self._xml([]))
        self.assertIn("<table", result.lower())

    def test_apps_xml_file(self):
        """Transforma o arquivo Apps.xml fornecido no repositório."""
        xml_path = os.path.join(XSL_DIR, "Apps.xml")
        with open(xml_path, "rb") as fh:
            source = etree.parse(fh)
        result = str(self.xslt(source))
        self.assertIn("App One", result)
        self.assertIn("App Two", result)


# ---------------------------------------------------------------------------
# Appcompat_bidi.xsl
# ---------------------------------------------------------------------------


class TestAppcompatBidiXsl(unittest.TestCase):
    """Testa Appcompat_bidi.xsl — saída HTML com suporte bidirecional."""

    @classmethod
    def setUpClass(cls):
        """Compila a folha de estilo uma única vez para todos os testes."""
        cls.xslt = _load_xslt("Appcompat_bidi.xsl")

    def _xml(self, items=None, texts=None):
        """Gera um documento XML <root> com itens e textos opcionais.

        Args:
            items: Lista de tuplas ``(title, content)`` para elementos <item>.
            texts: Lista de strings para elementos <text>.

        Returns:
            Documento XML como bytes.
        """
        parts = []
        for title, content in (items or []):
            parts.append(f'<item title="{title}">{content}</item>')
        for t in (texts or []):
            parts.append(f"<text>{t}</text>")
        return f"<root>{''.join(parts)}</root>".encode()

    def test_produces_html(self):
        """A transformação deve produzir um documento HTML."""
        result = _transform(self.xslt, self._xml())
        self.assertIn("<html", result.lower())

    def test_default_bidi_direction_ltr(self):
        """A direção padrão deve ser LTR (esquerda para direita)."""
        result = _transform(self.xslt, self._xml())
        self.assertIn("direction: ltr;", result)

    def test_custom_bidi_direction_rtl(self):
        """Ao passar bidi-direction=rtl, a saída deve refletir a direção RTL."""
        result = _transform(
            self.xslt,
            self._xml(),
            **{"bidi-direction": etree.XSLT.strparam("rtl")},
        )
        self.assertIn("direction: rtl;", result)

    def test_item_title_rendered(self):
        """O título de um elemento <item> deve aparecer na saída HTML."""
        result = _transform(self.xslt, self._xml(items=[("My Title", "Content")]))
        self.assertIn("My Title", result)

    def test_item_content_rendered(self):
        """O conteúdo de um elemento <item> deve aparecer na saída HTML."""
        result = _transform(self.xslt, self._xml(items=[("T", "Hello World")]))
        self.assertIn("Hello World", result)

    def test_text_element_rendered(self):
        """O conteúdo de um elemento <text> deve aparecer na saída HTML."""
        result = _transform(self.xslt, self._xml(texts=["Sample text"]))
        self.assertIn("Sample text", result)

    def test_heading_present(self):
        """O cabeçalho 'Transformação Bidirecional' deve estar no HTML."""
        result = _transform(self.xslt, self._xml())
        self.assertIn("Transformação Bidirecional", result)


# ---------------------------------------------------------------------------
# Appcompat_detailed.xsl
# ---------------------------------------------------------------------------


class TestAppcompatDetailedXsl(unittest.TestCase):
    """Testa Appcompat_detailed.xsl — tabela HTML detalhada de compatibilidade."""

    @classmethod
    def setUpClass(cls):
        """Compila a folha de estilo uma única vez para todos os testes."""
        cls.xslt = _load_xslt("Appcompat_detailed.xsl")

    def _xml(self, apps=None):
        """Gera um documento XML <compatibility> com entradas de app opcionais.

        Args:
            apps: Lista de tuplas ``(nome, versão, status, descrição)``.

        Returns:
            Documento XML como bytes.
        """
        rows = "".join(
            f"<app><name>{n}</name><version>{v}</version>"
            f"<status>{s}</status><description>{d}</description></app>"
            for n, v, s, d in (apps or [])
        )
        return f"<compatibility>{rows}</compatibility>".encode()

    def test_produces_html(self):
        """A transformação deve produzir um documento HTML."""
        result = _transform(self.xslt, self._xml())
        self.assertIn("<html", result.lower())

    def test_page_title(self):
        """O título 'Compatibilidade de Aplicativos' deve estar no HTML."""
        result = _transform(self.xslt, self._xml())
        self.assertIn("Compatibilidade de Aplicativos", result)

    def test_column_headers(self):
        """Os cabeçalhos de coluna em português devem estar na tabela."""
        result = _transform(self.xslt, self._xml())
        for header in ["Aplicativo", "Versão", "Status", "Descrição"]:
            self.assertIn(header, result)

    def test_single_app_all_fields(self):
        """Um app deve ter todos os campos exibidos na tabela."""
        apps = [("TestApp", "1.2", "OK", "Works fine")]
        result = _transform(self.xslt, self._xml(apps))
        self.assertIn("TestApp", result)
        self.assertIn("1.2", result)
        self.assertIn("OK", result)
        self.assertIn("Works fine", result)

    def test_multiple_apps(self):
        """Vários apps devem ter todos os campos listados na tabela."""
        apps = [
            ("App A", "1.0", "Compatible", "Full support"),
            ("App B", "2.0", "Incompatible", "Not supported"),
        ]
        result = _transform(self.xslt, self._xml(apps))
        self.assertIn("App A", result)
        self.assertIn("App B", result)
        self.assertIn("Full support", result)
        self.assertIn("Not supported", result)

    def test_empty_compatibility(self):
        """Um elemento <compatibility> vazio deve produzir uma tabela HTML."""
        result = _transform(self.xslt, self._xml())
        self.assertIn("<table", result.lower())


# ---------------------------------------------------------------------------
# Appcompat_detailed_txt.xsl
# ---------------------------------------------------------------------------


class TestAppcompatDetailedTxtXsl(unittest.TestCase):
    """Testa Appcompat_detailed_txt.xsl — relatório em texto simples."""

    @classmethod
    def setUpClass(cls):
        """Compila a folha de estilo uma única vez para todos os testes."""
        cls.xslt = _load_xslt("Appcompat_detailed_txt.xsl")

    def _xml(self, applications=None):
        """Gera um documento XML <report> com aplicações opcionais.

        Args:
            applications: Lista de tuplas
                ``(nome, versão, fornecedor, status, detalhes)``.

        Returns:
            Documento XML como bytes.
        """
        rows = "".join(
            f"<application>"
            f"<name>{n}</name><version>{v}</version><vendor>{ve}</vendor>"
            f"<status>{s}</status><details>{d}</details>"
            f"</application>"
            for n, v, ve, s, d in (applications or [])
        )
        return f"<report>{rows}</report>".encode()

    def test_header_line(self):
        """O cabeçalho 'Application Compatibility Detailed Report' deve estar presente."""
        result = _transform(self.xslt, self._xml())
        self.assertIn("Application Compatibility Detailed Report", result)

    def test_separator_line(self):
        """Deve haver uma linha separadora de iguais (======)."""
        result = _transform(self.xslt, self._xml())
        self.assertIn("======", result)

    def test_single_application_fields(self):
        """Todos os campos de uma aplicação devem aparecer no relatório."""
        apps = [("Calculator", "3.0", "Microsoft", "Passed", "No issues")]
        result = _transform(self.xslt, self._xml(apps))
        self.assertIn("Calculator", result)
        self.assertIn("3.0", result)
        self.assertIn("Microsoft", result)
        self.assertIn("Passed", result)
        self.assertIn("No issues", result)

    def test_field_labels_present(self):
        """Os rótulos de cada campo devem aparecer no relatório."""
        apps = [("X", "1", "V", "S", "D")]
        result = _transform(self.xslt, self._xml(apps))
        for label in ["Application Name:", "Version:", "Vendor:", "Status:", "Details:"]:
            self.assertIn(label, result)

    def test_multiple_applications_separated(self):
        """Aplicações diferentes devem ser separadas por linha de hifens (------)."""
        apps = [
            ("App1", "1.0", "VendorA", "OK", "Fine"),
            ("App2", "2.0", "VendorB", "Fail", "Issues"),
        ]
        result = _transform(self.xslt, self._xml(apps))
        self.assertIn("App1", result)
        self.assertIn("App2", result)
        self.assertIn("------", result)

    def test_empty_report(self):
        """Um relatório vazio deve ainda exibir o cabeçalho."""
        result = _transform(self.xslt, self._xml())
        self.assertIn("Application Compatibility Detailed Report", result)


# ---------------------------------------------------------------------------
# Appcompt_detailed-bidi_txt.xsl
# ---------------------------------------------------------------------------


class TestAppcomptDetailedBidiTxtXsl(unittest.TestCase):
    """Testa Appcompt_detailed-bidi_txt.xsl — relatório de texto com bidi."""

    @classmethod
    def setUpClass(cls):
        """Compila a folha de estilo uma única vez para todos os testes."""
        cls.xslt = _load_xslt("Appcompt_detailed-bidi_txt.xsl")

    def _xml(self, apps=None):
        """Gera um documento XML <applications> com atributos de aplicação.

        Args:
            apps: Lista de tuplas ``(nome, versão, compatibilidade)``.

        Returns:
            Documento XML como bytes.
        """
        rows = "".join(
            f'<application name="{n}" version="{v}" compatibility="{c}"/>'
            for n, v, c in (apps or [])
        )
        return f"<applications>{rows}</applications>".encode()

    def test_report_header(self):
        """O cabeçalho 'AppCompat' deve estar no relatório."""
        result = _transform(self.xslt, self._xml())
        self.assertIn("AppCompat", result)

    def test_single_app_name(self):
        """O nome da aplicação deve aparecer no relatório."""
        result = _transform(self.xslt, self._xml([("WordPad", "1.0", "Compatible")]))
        self.assertIn("WordPad", result)

    def test_single_app_version(self):
        """A versão da aplicação deve aparecer no relatório."""
        result = _transform(self.xslt, self._xml([("X", "9.9", "OK")]))
        self.assertIn("9.9", result)

    def test_single_app_compatibility(self):
        """O status de compatibilidade deve aparecer no relatório."""
        result = _transform(self.xslt, self._xml([("X", "1", "Incompatible")]))
        self.assertIn("Incompatible", result)

    def test_multiple_apps(self):
        """Várias aplicações devem todas aparecer no relatório."""
        apps = [("A", "1", "Yes"), ("B", "2", "No")]
        result = _transform(self.xslt, self._xml(apps))
        self.assertIn("A", result)
        self.assertIn("B", result)

    def test_uses_bundled_applications_xml(self):
        """Transforma o arquivo Applications.xml fornecido no repositório."""
        xml_path = os.path.join(XSL_DIR, "Applications.xml")
        with open(xml_path, "rb") as fh:
            source = etree.parse(fh)
        result = str(self.xslt(source))
        self.assertIn("App1", result)
        self.assertIn("App2", result)

    def test_empty_applications(self):
        """Um elemento <applications> vazio deve ainda exibir o cabeçalho."""
        result = _transform(self.xslt, self._xml())
        self.assertIn("AppCompat", result)


# ---------------------------------------------------------------------------
# appcompat_delailed_bidi.xsl  (XSLT 2.0 — apenas verificação estrutural)
# ---------------------------------------------------------------------------


class TestAppcompatDetailedBidiXslParseable(unittest.TestCase):
    """
    Testa appcompat_delailed_bidi.xsl, que declara XSLT version="2.0".

    O lxml suporta apenas XSLT 1.0, portanto este arquivo não pode ser
    executado como transformador.  Os testes verificam apenas que o arquivo
    é XML bem-formado e contém os elementos esperados de uma folha de estilo.
    """

    XSL_FILE = os.path.join(XSL_DIR, "appcompat_delailed_bidi.xsl")

    def test_file_is_well_formed_xml(self):
        """O arquivo deve ser XML bem-formado e parseável pelo lxml."""
        with open(self.XSL_FILE, "rb") as fh:
            doc = etree.parse(fh)
        self.assertIsNotNone(doc)

    def test_declares_xslt_namespace(self):
        """O elemento raiz deve declarar o namespace XSLT."""
        with open(self.XSL_FILE, "rb") as fh:
            doc = etree.parse(fh)
        root = doc.getroot()
        self.assertIn("http://www.w3.org/1999/XSL/Transform", root.nsmap.values())

    def test_version_attribute_is_two(self):
        """O atributo version do elemento raiz deve ser '2.0'."""
        with open(self.XSL_FILE, "rb") as fh:
            doc = etree.parse(fh)
        root = doc.getroot()
        self.assertEqual(root.get("version"), "2.0")

    def test_contains_for_each_template(self):
        """O arquivo deve conter ao menos um elemento xsl:for-each."""
        with open(self.XSL_FILE, "rb") as fh:
            content = fh.read().decode()
        self.assertIn("xsl:for-each", content)

    def test_contains_xsl_choose(self):
        """O arquivo deve conter ao menos um elemento xsl:choose."""
        with open(self.XSL_FILE, "rb") as fh:
            content = fh.read().decode()
        self.assertIn("xsl:choose", content)


if __name__ == "__main__":
    unittest.main()
