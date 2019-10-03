#!python
# $Id: texml.py,v 1.20 2006-07-20 03:56:49 olpa Exp $

VERSION = "2.0.2"; # GREPVERSION # Format of this string is important
usage = """Convert TeXML markup to [La]TeX markup. v.%s. Usage:
python texml.py [-e encoding] [-w auto_width] [-c|--context] [-a|--ascii] in_file out_file""" % VERSION

#
# Check command line, print help
#
import sys
if len(sys.argv) < 3:
  print >>sys.stderr, usage
  sys.exit(1)

#
# Parse command line options
#
encoding      = 'ascii'
always_ascii  = 0
width         = 62
use_context   = 0
use_namespace = 1
import getopt
try:
  opts, args = getopt.getopt(sys.argv[1:], 'hcaw:e:', ['help', 'context', 'ascii', 'width=', 'encoding=', ])
except getopt.GetoptError, e:
  print >>sys.stderr, 'texml: Can\'t parse command line: %s' % e
  print >>sys.stderr, usage
  sys.exit(2)
for o, a in opts:
  if o in ('-h', '--help'):
    print >>sys.stderr, usage;
    sys.exit(1)
  if o in ('-c', '--context'):
    use_context = 1
  if o in ('-a', '--ascii'):
    always_ascii = 1
  if o in ('-w', '--width'):
    try:
      width = int(a)
    except:
      print >>sys.stderr, "texml: Width is not an integer: '%s'" % a
      sys.exit(1)
    if width < 3: # just a random value
      print >>sys.stderr, "texml: Width should be greater 3 but get '%s'" % a
      sys.exit(1)
  if o in ('-e', '--encoding'):
    encoding = a

#
# Get input and output file
#
if len(args) != 2:
  print >>sys.stderr, 'texml: Expected two command line arguments, but got %d' % len(args)
  sys.exit(3)
(infile, outfile) = args

#
# Prepare transformation-1: input file, XML parser
#
import xml.sax 
from xml.sax.handler import feature_namespaces

if '-' == infile:
  infile = sys.stdin

#
# Prepare transformation-2: output
#
if '-' == outfile:
  f = sys.stdout
else:
  f = file(outfile, 'wb')

#
# An error handler
#
def quit(msg):
    sys.stderr.write(msg)
    f.close()
    sys.exit(1)

#
# import main class and parse
#
import Texml.processor
try:
  Texml.processor.process(infile, f, encoding, width, always_ascii, use_context)
    
except Exception, msg:
  msg = 'texml: %s\n' % (str(msg))
  quit(msg)

f.close()
sys.exit(0)
