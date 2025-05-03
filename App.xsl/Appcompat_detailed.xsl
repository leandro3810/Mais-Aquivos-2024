<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output method="html" encoding="UTF-8" indent="yes" />

  <!-- Root template -->
  <xsl:template match="/">
    <html>
      <head>
        <title>Compatibilidade de Aplicativos - Detalhado</title>
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
            background-color: #f4f4f4;
            text-align: left;
          }
          tr:nth-child(even) {
            background-color: #f9f9f9;
          }
          tr:hover {
            background-color: #f1f1f1;
          }
        </style>
      </head>
      <body>
        <h1>Compatibilidade de Aplicativos - Detalhado</h1>
        <table>
          <thead>
            <tr>
              <th>Aplicativo</th>
              <th>Versão</th>
              <th>Status</th>
              <th>Descrição</th>
            </tr>
          </thead>
          <tbody>
            <!-- Itera sobre cada aplicativo -->
            <xsl:for-each select="compatibility/app">
              <tr>
                <td><xsl:value-of select="name" /></td>
                <td><xsl:value-of select="version" /></td>
                <td><xsl:value-of select="status" /></td>
                <td><xsl:value-of select="description" /></td>
              </tr>
            </xsl:for-each>
          </tbody>
        </table>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
