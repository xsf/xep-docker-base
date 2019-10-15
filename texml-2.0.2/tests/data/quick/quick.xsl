<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output indent="yes"/>

<!-- document skeleton -->
<xsl:template match="/">
  <TeXML>
    <cmd name="documentclass">
      <opt>a4paper,12pt</opt>
      <parm>article</parm>
    </cmd>
    <env name="document">
      <!-- title page -->
      <cmd name="author" nl2="1">
        <parm><xsl:value-of
            select="//span[@class='author']"/>
        </parm>
      </cmd>
      <cmd name="title" nl2="1">
        <parm><xsl:value-of
            select="/html/head/title"/></parm>
      </cmd>
      <cmd name="maketitle" nl2="1" gr="0"/>
      <!-- document body -->
      <xsl:apply-templates select="/html/body"/>
    </env>
  </TeXML>
</xsl:template>

<!-- document body -->
<xsl:template match="body">
  <cmd name="section*" nl2="1">
    <parm><xsl:value-of select="h1"/></parm>
  </cmd>
  <xsl:apply-templates select="*"/>
</xsl:template>

<!-- text -->
<xsl:template match="p">
  <TeXML>
    <xsl:apply-templates/>
    <cmd name="par" nl2="1" gr="0"/>
  </TeXML>
</xsl:template>

<!-- quotes -->
<xsl:template match="q">
  <cmd name="lq"/><cmd name="lq"/>
  <xsl:apply-templates/>
  <cmd name="rq"/><cmd name="rq"/>
</xsl:template>

<!-- line -->
<xsl:template match="hr">
  <cmd name="bigskip" gr="0" nl2="1"/>
  <cmd name="hrule"   gr="0" nl2="1"/>
</xsl:template>

<!-- ignore h1 and author in body -->
<xsl:template match="h1 | p[@align]"/>

</xsl:stylesheet>
