"""
Using TeXML in Python
---------------------

The module Texml.process converts a TeXML file to a TeX file.

Basic use requires the following:

1. Import the needed libraries
2. Set up the input and output streams
3. Call on the function process
4. Use a try-except block around the call to process
5. Clean up resources

Parameters for the function process
-----------------------------------

in_stream
       An input TeXML document as a file object or the path to a file.
       Mandatory.

out_stream
       An output TeX document as a file object. Mandatory.

autonl_width
       Recommended   width  to  split  long  lines  on  smaller  ones.
       Optional, default is 62.

encoding
       Output   encoding.  Should  be  known  to  the  Python  codecs.
       Optional, default is ascii.

always_ascii
       Use  only ASCII symbols for output. Non-ASCII bytes are escaped
       using  the  ^^XX  form,  where  XX is a hexadecimal code of the
       character.  Optional,  default  is  0  (False, do not encode as
       ASCII).

use_context
       ConTeXt  is  an  alternative  to  LaTeX. In ConTeXt mode, TeXML
       translation  is slightly different. Set to 1 (True) to activate
       this mode. Optional, default is 0 (False, LaTeX mode).

If the input file doesn't conform to the TeXML specification, then the
exception  TeXML.handler.InvalidXmlException  is  raised. If the input
parameters  are  invalid,  then  the  exception  ValueError is raised.
Expect that the underlying libraries might also raise exceptions, such
as xml.sax.SAXException.

Simplest example
----------------

#!/usr/bin/python

# Import the needed libraries
import sys
import Texml.processor

# Use the standard input and output
in_stream  = sys.stdin
out_stream = sys.stdout

# Convert
Texml.processor.process(in_stream, out_stream)

Full example
------------

#!/usr/bin/python

# Import the needed libraries
import sys
import Texml.processor

# Input can be given by a path, output should be a file object
infile = 'document.xml'
out    = file('out.tex', 'w')
# Older versions of python need the following code:
# out = open('out.tex', 'w')

# Parameters
width        = 75
encoding     = 'UTF-8'
always_ascii = 1
use_context  = 1

# Convert TeXML inside a try-except block
try:
  Texml.processor.process(
      in_stream    = infile,
      out_stream   = out,
      autonl_width = width,
      encoding     = encoding,
      always_ascii = always_ascii,
      use_context  = use_context)
except Exception, msg:
  print sys.stderr, 'texml: %s' % str(msg)

# Clean up resources
out.close()
"""
# $Id: processor.py,v 1.2 2006-06-06 03:37:18 olpa Exp $

import Texml.texmlwr
import Texml.handler

def process(in_stream, out_stream, encoding='ascii', autonl_width=62, always_ascii=0, use_context=0):
  transform_obj = Texml.handler.ParseFile()
  texml_writer =  Texml.texmlwr.texmlwr(
      stream       = out_stream,
      encoding     = encoding,
      autonl_width = autonl_width,
      use_context  = use_context,
      always_ascii = always_ascii,
      )
  transform_obj.parse_file(
      read_obj     = in_stream,
      texml_writer = texml_writer,
      use_context  = use_context,
      )

