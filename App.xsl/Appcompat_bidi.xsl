<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <!-- Definições de compatibilidade para aplicativos com suporte bidi (bidirecionalidade) -->

    <!-- Parâmetro opcional para configurações -->
    <xsl:param name="bidi-direction" select="'ltr'" />

    <xsl:template match="/">
        <!-- Modelo principal para transformação -->
        <html>
            <head>
                <title>Compatibilidade Bidi</title>
            </head>
            <body>
                <h1>Transformação Bidirecional</h1>
                <p>Direção configurada: <xsl:value-of select="$bidi-direction" /></p>
                <div>
                    <h2>Conteúdo Transformado</h2>
                    <xsl:apply-templates />
                </div>
            </body>
        </html>
    </xsl:template>

    <!-- Exemplo de template para elementos -->
    <xsl:template match="item">
        <div>
            <h3><xsl:value-of select="@title" /></h3>
            <p><xsl:value-of select="." /></p>
        </div>
    </xsl:template>

    <!-- Transformação para texto -->
    <xsl:template match="text">
        <span style="direction: <xsl:value-of select='$bidi-direction' />;">
            <xsl:value-of select="." />
        </span>
    </xsl:template>
</xsl:stylesheet>
