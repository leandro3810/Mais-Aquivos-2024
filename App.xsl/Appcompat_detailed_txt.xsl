<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
    <xsl:output method="text" encoding="UTF-8" />

    <!-- Root template -->
    <xsl:template match="/">
        <xsl:text>Application Compatibility Detailed Report</xsl:text>
        <xsl:text>&#10;======================================&#10;&#10;</xsl:text>
        <xsl:apply-templates select="report" />
    </xsl:template>

    <!-- Template for the report node -->
    <xsl:template match="report">
        <xsl:for-each select="application">
            <xsl:text>Application Name: </xsl:text>
            <xsl:value-of select="name" />
            <xsl:text>&#10;Version: </xsl:text>
            <xsl:value-of select="version" />
            <xsl:text>&#10;Vendor: </xsl:text>
            <xsl:value-of select="vendor" />
            <xsl:text>&#10;Status: </xsl:text>
            <xsl:value-of select="status" />
            <xsl:text>&#10;Details: </xsl:text>
            <xsl:value-of select="details" />
            <xsl:text>&#10;--------------------------------------&#10;</xsl:text>
        </xsl:for-each>
    </xsl:template>
</xsl:stylesheet>
