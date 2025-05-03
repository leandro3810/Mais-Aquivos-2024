<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
    <!-- Definição inicial -->
    <xsl:output method="text" encoding="UTF-8" />

    <!-- Template principal -->
    <xsl:template match="/">
        <!-- Cabeçalho -->
        ***********************************************
        Compatibilidade Detalhada de Aplicativos (AppCompat)
        ***********************************************
        <xsl:text>&#10;</xsl:text>
        
        <!-- Iteração pelos aplicativos -->
        <xsl:for-each select="applications/application">
            Aplicativo: <xsl:value-of select="@name" />
            <xsl:text>&#10;</xsl:text>
            Versão: <xsl:value-of select="@version" />
            <xsl:text>&#10;</xsl:text>
            Compatibilidade: <xsl:value-of select="@compatibility" />
            <xsl:text>&#10;</xsl:text>
            -----------------------------------------------
            <xsl:text>&#10;</xsl:text>
        </xsl:for-each>
    </xsl:template>
</xsl:stylesheet>
