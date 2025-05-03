<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="2.0">
    <!-- Declaração de template raiz -->
    <xsl:template match="/">
        <html>
            <head>
                <title>Compatibilidade de Aplicativos - Detalhes Bidi</title>
                <meta charset="UTF-8"/>
            </head>
            <body>
                <h1>Relatório de Compatibilidade de Aplicativos</h1>
                <xsl:apply-templates select="apps"/>
            </body>
        </html>
    </xsl:template>

    <!-- Template para lista de aplicativos -->
    <xsl:template match="apps">
        <ul>
            <xsl:for-each select="app">
                <li>
                    <strong>Nome:</strong> <xsl:value-of select="name"/>
                    <br/>
                    <strong>Compatibilidade:</strong> <xsl:value-of select="compatibility"/>
                    <br/>
                    <strong>Direção Bidi:</strong> 
                    <xsl:choose>
                        <xsl:when test="bidi='rtl'">Direita para Esquerda (RTL)</xsl:when>
                        <xsl:otherwise>Esquerda para Direita (LTR)</xsl:otherwise>
                    </xsl:choose>
                </li>
            </xsl:for-each>
        </ul>
    </xsl:template>
</xsl:stylesheet>
