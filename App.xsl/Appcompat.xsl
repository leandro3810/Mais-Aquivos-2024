<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- Modelo básico para transformar XML em HTML -->
    <xsl:output method="html" indent="yes" />

    <!-- Template principal -->
    <xsl:template match="/">
        <html>
            <head>
                <title>App Compatibility Report</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                    }
                    table {
                        width: 100%;
                        border-collapse: collapse;
                    }
                    th, td {
                        border: 1px solid #ddd;
                        padding: 8px;
                    }
                    th {
                        background-color: #f2f2f2;
                        text-align: left;
                    }
                </style>
            </head>
            <body>
                <h1>App Compatibility Report</h1>
                <table>
                    <tr>
                        <th>App Name</th>
                        <th>Version</th>
                        <th>Status</th>
                    </tr>
                    <!-- Exemplo de como iterar sobre elementos XML -->
                    <xsl:for-each select="apps/app">
                        <tr>
                            <td><xsl:value-of select="name" /></td>
                            <td><xsl:value-of select="version" /></td>
                            <td><xsl:value-of select="status" /></td>
                        </tr>
                    </xsl:for-each>
                </table>
            </body>
        </html>
    </xsl:template>

</xsl:stylesheet>
