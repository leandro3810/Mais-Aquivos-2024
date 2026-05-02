"""
Tests for XSLT stylesheets in the App.xsl/ directory.

Each test applies a stylesheet to a sample XML document and asserts that the
expected content appears in the transformed output.  All stylesheets use
XSLT 1.0 and are processed with lxml.etree.XSLT.

Note: appcompat_delailed_bidi.xsl declares version="2.0" which is not
supported by lxml; that stylesheet is tested for parse/load correctness only.
"""

import os
import textwrap
import unittest

from lxml import etree

XSL_DIR = os.path.join(os.path.dirname(__file__), "..", "App.xsl")


def _load_xslt(filename):
    """Parse an XSL file and return an lxml.etree.XSLT transformer."""
    xsl_path = os.path.join(XSL_DIR, filename)
    with open(xsl_path, "rb") as fh:
        xsl_doc = etree.parse(fh)
    return etree.XSLT(xsl_doc)


def _transform(xslt, xml_string, **params):
    """Apply *xslt* to *xml_string* and return the result as a string."""
    source = etree.fromstring(xml_string)
    result = xslt(source, **params)
    return str(result)


class TestAppcompatXsl(unittest.TestCase):
    """Tests for Appcompat.xsl — transforms apps/app elements to an HTML table."""

    @classmethod
    def setUpClass(cls):
        cls.xslt = _load_xslt("Appcompat.xsl")

    def _xml(self, apps):
        rows = "".join(
            f"<app><name>{a}</name><version>{v}</version>"
            f"<status>{s}</status></app>"
            for a, v, s in apps
        )
        return f"<apps>{rows}</apps>".encode()

    def test_produces_html_output(self):
        result = _transform(self.xslt, self._xml([("App One", "1.0", "Compatible")]))
        self.assertIn("<html", result.lower())

    def test_title_in_output(self):
        result = _transform(self.xslt, self._xml([]))
        self.assertIn("App Compatibility Report", result)

    def test_table_headers_present(self):
        result = _transform(self.xslt, self._xml([]))
        self.assertIn("App Name", result)
        self.assertIn("Version", result)
        self.assertIn("Status", result)

    def test_single_app_row(self):
        result = _transform(self.xslt, self._xml([("MyApp", "2.0", "Compatible")]))
        self.assertIn("MyApp", result)
        self.assertIn("2.0", result)
        self.assertIn("Compatible", result)

    def test_multiple_app_rows(self):
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
        """An empty <apps> element should still produce a valid HTML page."""
        result = _transform(self.xslt, self._xml([]))
        self.assertIn("<table", result.lower())

    def test_apps_xml_file(self):
        """Transform the bundled Apps.xml fixture."""
        xml_path = os.path.join(XSL_DIR, "Apps.xml")
        with open(xml_path, "rb") as fh:
            source = etree.parse(fh)
        result = str(self.xslt(source))
        self.assertIn("App One", result)
        self.assertIn("App Two", result)


class TestAppcompatBidiXsl(unittest.TestCase):
    """Tests for Appcompat_bidi.xsl — bidi-aware HTML output."""

    @classmethod
    def setUpClass(cls):
        cls.xslt = _load_xslt("Appcompat_bidi.xsl")

    def _xml(self, items=None, texts=None):
        parts = []
        for title, content in (items or []):
            parts.append(f'<item title="{title}">{content}</item>')
        for t in (texts or []):
            parts.append(f"<text>{t}</text>")
        return f"<root>{''.join(parts)}</root>".encode()

    def test_produces_html(self):
        result = _transform(self.xslt, self._xml())
        self.assertIn("<html", result.lower())

    def test_default_bidi_direction_ltr(self):
        result = _transform(self.xslt, self._xml())
        self.assertIn("direction: ltr;", result)

    def test_custom_bidi_direction_rtl(self):
        result = _transform(
            self.xslt,
            self._xml(),
            **{"bidi-direction": etree.XSLT.strparam("rtl")},
        )
        self.assertIn("direction: rtl;", result)

    def test_item_title_rendered(self):
        result = _transform(self.xslt, self._xml(items=[("My Title", "Content")]))
        self.assertIn("My Title", result)

    def test_item_content_rendered(self):
        result = _transform(self.xslt, self._xml(items=[("T", "Hello World")]))
        self.assertIn("Hello World", result)

    def test_text_element_rendered(self):
        result = _transform(self.xslt, self._xml(texts=["Sample text"]))
        self.assertIn("Sample text", result)

    def test_heading_present(self):
        result = _transform(self.xslt, self._xml())
        self.assertIn("Transformação Bidirecional", result)


class TestAppcompatDetailedXsl(unittest.TestCase):
    """Tests for Appcompat_detailed.xsl — detailed HTML table."""

    @classmethod
    def setUpClass(cls):
        cls.xslt = _load_xslt("Appcompat_detailed.xsl")

    def _xml(self, apps=None):
        rows = "".join(
            f"<app><name>{n}</name><version>{v}</version>"
            f"<status>{s}</status><description>{d}</description></app>"
            for n, v, s, d in (apps or [])
        )
        return f"<compatibility>{rows}</compatibility>".encode()

    def test_produces_html(self):
        result = _transform(self.xslt, self._xml())
        self.assertIn("<html", result.lower())

    def test_page_title(self):
        result = _transform(self.xslt, self._xml())
        self.assertIn("Compatibilidade de Aplicativos", result)

    def test_column_headers(self):
        result = _transform(self.xslt, self._xml())
        for header in ["Aplicativo", "Versão", "Status", "Descrição"]:
            self.assertIn(header, result)

    def test_single_app_all_fields(self):
        apps = [("TestApp", "1.2", "OK", "Works fine")]
        result = _transform(self.xslt, self._xml(apps))
        self.assertIn("TestApp", result)
        self.assertIn("1.2", result)
        self.assertIn("OK", result)
        self.assertIn("Works fine", result)

    def test_multiple_apps(self):
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
        result = _transform(self.xslt, self._xml())
        self.assertIn("<table", result.lower())


class TestAppcompatDetailedTxtXsl(unittest.TestCase):
    """Tests for Appcompat_detailed_txt.xsl — plain-text report output."""

    @classmethod
    def setUpClass(cls):
        cls.xslt = _load_xslt("Appcompat_detailed_txt.xsl")

    def _xml(self, applications=None):
        rows = "".join(
            f"<application>"
            f"<name>{n}</name><version>{v}</version><vendor>{ve}</vendor>"
            f"<status>{s}</status><details>{d}</details>"
            f"</application>"
            for n, v, ve, s, d in (applications or [])
        )
        return f"<report>{rows}</report>".encode()

    def test_header_line(self):
        result = _transform(self.xslt, self._xml())
        self.assertIn("Application Compatibility Detailed Report", result)

    def test_separator_line(self):
        result = _transform(self.xslt, self._xml())
        self.assertIn("======", result)

    def test_single_application_fields(self):
        apps = [("Calculator", "3.0", "Microsoft", "Passed", "No issues")]
        result = _transform(self.xslt, self._xml(apps))
        self.assertIn("Calculator", result)
        self.assertIn("3.0", result)
        self.assertIn("Microsoft", result)
        self.assertIn("Passed", result)
        self.assertIn("No issues", result)

    def test_field_labels_present(self):
        apps = [("X", "1", "V", "S", "D")]
        result = _transform(self.xslt, self._xml(apps))
        for label in ["Application Name:", "Version:", "Vendor:", "Status:", "Details:"]:
            self.assertIn(label, result)

    def test_multiple_applications_separated(self):
        apps = [
            ("App1", "1.0", "VendorA", "OK", "Fine"),
            ("App2", "2.0", "VendorB", "Fail", "Issues"),
        ]
        result = _transform(self.xslt, self._xml(apps))
        self.assertIn("App1", result)
        self.assertIn("App2", result)
        self.assertIn("------", result)

    def test_empty_report(self):
        result = _transform(self.xslt, self._xml())
        self.assertIn("Application Compatibility Detailed Report", result)


class TestAppcomptDetailedBidiTxtXsl(unittest.TestCase):
    """Tests for Appcompt_detailed-bidi_txt.xsl — text report with bidi."""

    @classmethod
    def setUpClass(cls):
        cls.xslt = _load_xslt("Appcompt_detailed-bidi_txt.xsl")

    def _xml(self, apps=None):
        rows = "".join(
            f'<application name="{n}" version="{v}" compatibility="{c}"/>'
            for n, v, c in (apps or [])
        )
        return f"<applications>{rows}</applications>".encode()

    def test_report_header(self):
        result = _transform(self.xslt, self._xml())
        self.assertIn("AppCompat", result)

    def test_single_app_name(self):
        result = _transform(self.xslt, self._xml([("WordPad", "1.0", "Compatible")]))
        self.assertIn("WordPad", result)

    def test_single_app_version(self):
        result = _transform(self.xslt, self._xml([("X", "9.9", "OK")]))
        self.assertIn("9.9", result)

    def test_single_app_compatibility(self):
        result = _transform(self.xslt, self._xml([("X", "1", "Incompatible")]))
        self.assertIn("Incompatible", result)

    def test_multiple_apps(self):
        apps = [("A", "1", "Yes"), ("B", "2", "No")]
        result = _transform(self.xslt, self._xml(apps))
        self.assertIn("A", result)
        self.assertIn("B", result)

    def test_uses_bundled_applications_xml(self):
        """Transform the bundled Applications.xml fixture."""
        xml_path = os.path.join(XSL_DIR, "Applications.xml")
        with open(xml_path, "rb") as fh:
            source = etree.parse(fh)
        result = str(self.xslt(source))
        self.assertIn("App1", result)
        self.assertIn("App2", result)

    def test_empty_applications(self):
        result = _transform(self.xslt, self._xml())
        self.assertIn("AppCompat", result)


class TestAppcompatDetailedBidiXslParseable(unittest.TestCase):
    """
    appcompat_delailed_bidi.xsl declares XSLT version="2.0".
    lxml only supports XSLT 1.0, so we verify the file is well-formed XML
    and contains the expected stylesheet elements rather than running it.
    """

    XSL_FILE = os.path.join(XSL_DIR, "appcompat_delailed_bidi.xsl")

    def test_file_is_well_formed_xml(self):
        with open(self.XSL_FILE, "rb") as fh:
            doc = etree.parse(fh)
        self.assertIsNotNone(doc)

    def test_declares_xslt_namespace(self):
        with open(self.XSL_FILE, "rb") as fh:
            doc = etree.parse(fh)
        root = doc.getroot()
        self.assertIn("http://www.w3.org/1999/XSL/Transform", root.nsmap.values())

    def test_version_attribute_is_two(self):
        with open(self.XSL_FILE, "rb") as fh:
            doc = etree.parse(fh)
        root = doc.getroot()
        self.assertEqual(root.get("version"), "2.0")

    def test_contains_for_each_template(self):
        with open(self.XSL_FILE, "rb") as fh:
            content = fh.read().decode()
        self.assertIn("xsl:for-each", content)

    def test_contains_xsl_choose(self):
        with open(self.XSL_FILE, "rb") as fh:
            content = fh.read().decode()
        self.assertIn("xsl:choose", content)


if __name__ == "__main__":
    unittest.main()
