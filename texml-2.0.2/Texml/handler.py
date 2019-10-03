""" Tranform TeXML SAX stream """
# $Id: handler.py,v 1.14 2006-06-14 04:45:06 olpa Exp $

import xml.sax.handler
from xml.sax.handler import feature_namespaces

import texmlwr
import specmap
import StringIO
import string
import os, sys

# Unbreakable spaces should not be deleted by strip(), but it happens:
# http://uucode.com/blog/2010/06/01/python-wtf-strip-eats-too-much/
# The solution from the web page does not work with old versions
# of python, therefore let's define a fallback functionality.
try:
  "dummy".strip(string.whitespace)
  strip_args = (string.whitespace, )
except:
  strip_args = ()

#
# TeXML SAX handler works correct but misfeaturely when SAX parser
# reports characters in several calls instead of one call.
# This wrappers fixes the problem
#

class ParseFile:
    """

    Wrapper class to make the library easier to use.

    See the above notes for use.

    """

    def __init__(self):
        pass

    def parse_file(self, texml_writer, read_obj, use_context):

        handle = glue_handler(texml_writer, use_context)

        parser = xml.sax.make_parser()
        parser.setFeature(feature_namespaces, 1)
        parser.setContentHandler(handle)
        parser.setFeature("http://xml.org/sax/features/external-general-entities", True)


        parser.parse(read_obj)             

class InvalidXmlException(Exception):
    """
    handle invalid xml

    """
    pass

class glue_handler(xml.sax.ContentHandler):

  """
  Not really a public class. use ParseFile instead.

  """
  
  def __init__(self, texml_writer, use_context,
        name_space = 'http://getfo.sourceforge.net/texml/ns1'):
    self.h = Handler(texml_writer, use_context)
    self.c = None

    self.__name_space = name_space
    self.__current_name_space = None

  def startDocument(self):
    self.c = None
    self.h.startDocument()

  def flushChars(self):
    if self.c != None:
      self.h.characters(self.c)
      self.c = None

  def endDocument(self):
    self.flushChars()
    self.h.endDocument()

  # no longer use
  def startElement_off(self, name, attrs):
    self.flushChars()
    self.h.startElement(name, attrs)

  def setDocumentLocator(self, locator):
      self.locator = locator

  def startElementNS(self, name, qname, attrs):
    # change attrs to regular dictionary
    the_attrs = {}
    keys = attrs.keys()
    for key in keys:
        att = key[1]
        value = attrs[key]
        the_attrs[att] = value

    name_space = name[0]
    self.__current_name_space = name_space
    local_name = name[1]

    # get the column and line number and use the handler
    col_num = self.locator.getColumnNumber()
    line_num =  self.locator.getLineNumber()
    self.h.set_location(col_num, line_num)
    self.h.set_namespace(name_space)

    if name_space == self.__name_space or name_space == None:
        self.flushChars()
        self.h.startElement(local_name, the_attrs)
    # report an error and quit
    else:
        self.h.invalid_xml(local_name)
    
  # no longer use
  def endElement_off(self, name):
    self.flushChars()
    self.h.endElement(name)

  def endElementNS(self, name, qname):
    col_num = self.locator.getColumnNumber()
    line_num =  self.locator.getLineNumber()
    self.h.set_location(col_num, line_num)
    name_space = name[0]
    local_name = name[1]
    if name_space == self.__name_space or name_space == None:
        self.flushChars()
        self.h.endElement(local_name)
    # otherwise, ignore!


  def processingInstruction(self, target, data):
    self.flushChars()
    # No action. The only effect is that chunk
    # ... aa  <!-- xx -->  bb ...
    # is reported twice ('... aa  ' and ' bb ...')
    # instead of onece ('... aa    bb ...')

  def characters(self, content):
    col_num = self.locator.getColumnNumber()
    line_num =  self.locator.getLineNumber()
    self.h.set_location(col_num, line_num)
    if None == self.c:
      self.c = content
    else:
      self.c = self.c + content

# WhiteSpace (WS) elimination
# In most cases, WS around tags (both opening and closing) are removed.
# But these tags save ws: <ctrl/> and <spec/>.
# WS processing is allowed or disallowed by "process_ws".

class Handler:

  """
  Not really a public class.

  Handles the infile, using the glue_handle class to get the data as 
  elements or characters.

  """

  # Object variables
  # writer
  # no_text_content
  # text_is_only_spaces
  #
  # Whitespace handling:
  # process_ws
  # process_ws_stack
  # nl_spec
  # nl_spec_stack
  # 
  # For <env/> support:
  # cmdname
  # cmdname_stack
  # endenv
  # endenv_stack
  #
  # For <cmd/> support:
  # has_parm # Stacking is not required: if <cmd/> is in <cmd/>,
  #          # then is it wrapped by <parm/> or <opt/>

  def __init__(self, texml_writer, use_context):
    """ Create writer, create maps """
    self.__use_context = use_context
    # Paul Tremblay added this on 2005-03-08
    self.writer        = texml_writer
    self.cmdname_stack = []
    self.endenv_stack  = []
    self.cmdname       = ''
    self.endenv        = ''
    self.has_parm      = 0
    self.no_text_content     = 0
    self.text_is_only_spaces = 0
    self.process_ws          = 1
    self.process_ws_stack    = []
    self.nl_spec             = None
    self.nl_spec_stack       = []
    self.__name_space        = None
    #
    # Create handler maps
    #
    self.model_nomath = {
      'TeXML':  self.on_texml,
      'cmd':    self.on_cmd,
      'env':    self.on_env,
      'group':  self.on_group,
      'ctrl':   self.on_ctrl,
      'spec':   self.on_spec,
      'pdf':    self.on_pdf
    }
    self.model_content          = self.model_nomath.copy()
    self.model_content['math']  = self.on_math
    self.model_content['dmath'] = self.on_dmath
    self.model_cmd    = {
      'opt':    self.on_opt,
      'parm':   self.on_parm
    }
    self.model_env    = self.model_content.copy() # copy, so == will true only for environment, not for any tag that shares model_content
    self.model_env.update(self.model_cmd)
    self.model_opt    = self.model_content
    self.model_parm   = self.model_content
    self.end_handlers = {
      'TeXML':  self.on_texml_end,
      'cmd':    self.on_cmd_end,
      'env':    self.on_env_end,
      'group':  self.on_group_end,
      'ctrl':   self.on_ctrl_end,
      'spec':   self.on_spec_end,
      'opt':    self.on_opt_end,
      'parm':   self.on_parm_end,
      'math':   self.on_math_end,
      'dmath':  self.on_dmath_end,
      'pdf':    self.on_pdf_end
    }

  def set_location(self, col, line):
      self.__col_num = col
      self.__line_num = line

  def set_namespace(self, name):
      self.__name_space = name

  def invalid_xml(self,  local_name):
      msg = 'Invalid XML %s, %s: ' % (self.__col_num, self.__line_num)
      if self.__name_space:
        msg += 'Element "%s" for namespace "%s" not expected' % (local_name, self.__name_space)
      else:
        msg += '%s not expected' % (local_name)

      raise InvalidXmlException, msg

  def invalid_xml_other(self, msg):
      # for other types of invalid XML
      raise InvalidXmlException, msg

  # -------------------------------------------------------------------
  
  def startDocument(self):
    """ Initialize data structures before parsing """
    self.model       = {'TeXML': self.on_texml}
    self.model_stack = []

  def endDocument(self):
    """ Finalize document """
    self.writer.conditionalNewline()

  def startElement(self, name, attrs):
    """ Handle start of an element"""
    if name in self.model:
      self.model[name](attrs)
    else:
      self.invalid_xml(name)

  def characters(self, content):
    """ Handle text data """
    #
    # First, check if content allowed at all
    #
    # Elements like <spec/> should be empty
    if self.no_text_content:
      msg = 'Invalid XML %s, %s: ' % (self.__col_num, self.__line_num)
      msg  += "Text content is not expected: '%s'" % content.encode('latin-1', 'replace')
      self.invalid_xml_other(msg)
    # Element <cmd/> should not have text content,
    # but it also may contain spaces due to indenting
    # Element <env/> may have <opt/> and <parm/>, so we do
    # magic to delete whitespace at beginning of environment
    if self.text_is_only_spaces:
      stripped = content.lstrip(*strip_args)
      if 0 != len(stripped):
        msg = 'Invalid XML %s, %s: ' % (self.__col_num, self.__line_num)
        msg += "Only whitespaces are expected, not text content: '%s'" % content.encode('latin-1', 'replace')
        self.invalid_xml_other(msg)
      return                                               # return
    #
    # Eliminate whitespaces
    #
    post_content_ws = 0
    if self.process_ws:
      content2 = content.lstrip(*strip_args)
      if len(content2) != len(content):
        self.writer.writeWeakWS()
      content  = content2.rstrip(*strip_args)
      if len(content2) != len(content):
        post_content_ws = 1
    #
    # Finally, write content
    #
    self.writer.write(content)
    if post_content_ws:
      self.writer.writeWeakWS()

  def endElement(self, name):
    """ Handle end of en element """
    self.end_handlers[name]()
    self.unstack_model()

  def stack_model(self, model):
    """ Remember content model of parent and set model for current node """
    self.model_stack.append(self.model)
    self.model = model

  def unstack_model(self):
    """ Restore content model of parent """
    self.model = self.model_stack.pop()

  # -----------------------------------------------------------------

  def get_boolean(self, attrs, aname, default):
    """ Returns true if value of attribute "aname" is "1", false if "0" and None if attribute not exists. Raises error in other cases."""
    aval = attrs.get(aname, None)
    if None == aval:
      return default
    elif '1' == aval:
      return 1
    elif '0' == aval:
      return 0
    raise ValueError("Value of boolean attribute '%s' is not '0' or '1', but '%s'" % (aname, aval))

    msg = 'Invalid XML %s, %s: ' % (self.__col_num, self.__line_num)
    msg += "Value of boolean attribute '%s' is not '0' or '1', but '%s'" % (aname, aval)
    self.invalid_xml_other(msg)

  def on_texml(self, attrs):
    """ Handle TeXML element """
    self.stack_model(self.model_content)
    #
    # Set new mode ("text" or "math")
    #
    str = attrs.get('mode', None)
    if None == str:
      mode = texmlwr.DEFAULT
    elif 'text' == str:
      mode = texmlwr.TEXT
    elif 'math' == str:
      mode = texmlwr.MATH
    else:
      msg = 'Invalid XML %s, %s: ' % (self.__col_num, self.__line_num)
      msg += "Unknown value of TeXML/@mode attribute: '%s'" % str
      self.invalid_xml_other(msg)
    emptylines = self.get_boolean(attrs, 'emptylines', None)
    escape     = self.get_boolean(attrs, 'escape',     None)
    ligatures  = self.get_boolean(attrs, 'ligatures',  None)
    self.writer.stack_mode(mode)
    self.writer.stack_emptylines(emptylines)
    self.writer.stack_escape(escape)
    self.writer.stack_ligatures(ligatures)
    ws = self.get_boolean(attrs, 'ws', None)
    self.process_ws_stack.append(self.process_ws)
    if ws != None:
      self.process_ws  =  0 == ws
      self.writer.set_allow_weak_ws_to_nl(not ws)

  def on_texml_end(self):
    """ Handle TeXML element. Restore old mode. """
    self.writer.unstack_ligatures()
    self.writer.unstack_escape()
    self.writer.unstack_emptylines()
    self.writer.unstack_mode()
    self.process_ws = self.process_ws_stack.pop()
    self.writer.set_allow_weak_ws_to_nl(self.process_ws)

  # -----------------------------------------------------------------

  def on_cmd(self, attrs):
    """ Handle 'cmd' element """
    self.stack_model(self.model_cmd)
    #
    # Get name of the command
    #
    name = attrs.get('name', '')
    if 0 == len(name):
      msg = 'Invalid XML %s, %s: ' % (self.__col_num, self.__line_num)
      msg += "Attribute cmd/@name is empty" 
      self.invalid_xml_other(msg)
    if self.get_boolean(attrs, 'nl1', 0):
      self.writer.conditionalNewline()
    self.writer.writech('\\', 0)
    self.writer.write(name, 0)
    #
    # Setup in-cmd processing
    #
    self.has_parm            = 0
    self.text_is_only_spaces = 1
    self.nl_spec_stack.append(self.nl_spec)
    self.nl_spec = (self.get_boolean(attrs, 'nl2', 0), self.get_boolean(attrs, 'gr', 1))

  def on_cmd_end(self):
    self.text_is_only_spaces = 0
    #
    # Write additional space or newline if command has no parameters
    #
    (nl, gr) = self.nl_spec
    self.nl_spec = self.nl_spec_stack.pop()
    if not(self.has_parm):
      if gr:
        self.writer.write('{}', 0)
      else:
        self.writer.writeWeakWS()
    if nl:
      self.writer.conditionalNewline()

  def on_opt(self, attrs):
    """ Handle 'opt' element """
    self.on_opt_parm('[', attrs)

  def on_parm(self, attrs):
    """ Handle 'parm' element """
    self.on_opt_parm('{', attrs)
 
  def on_opt_end(self):
    self.on_opt_parm_end(']')

  def on_parm_end(self):
    self.on_opt_parm_end('}')

  def on_opt_parm(self, ch, attrs):
    """ Handle 'parm' and 'opt' """
    self.stack_model(self.model_opt)
    if self.model_stack[-1] == self.model_env:
      self.nl_spec_stack.append(self.nl_spec)
      self.nl_spec = self.writer.ungetWeakWS()
    self.writer.writech(ch, 0)
    self.text_is_only_spaces = 0

  def on_opt_parm_end(self, ch):
    self.writer.writech(ch, 0)
    self.has_parm            = 1 # At the end to avoid collision of nesting
    # <opt/> can be only inside <cmd/> or (very rarely) in <env/>
    if self.model_stack[-1] != self.model_env:
      self.text_is_only_spaces = 1
    else:
      self.text_is_only_spaces = 0
      if self.nl_spec:
        self.writer.writeWeakWS(self.nl_spec)
      self.nl_spec = self.nl_spec_stack.pop()

  # -----------------------------------------------------------------

  def on_env(self, attrs):
    """ Handle 'cmd' element """
    self.stack_model(self.model_env)
    #
    # Get name of the environment, and begin and end commands
    #
    name = attrs.get('name', '')
    if 0 == len(name):
      msg = 'Invalid XML %s, %s: ' % (self.__col_num, self.__line_num)
      msg += 'Attribute env/@name is empty'
      self.invalid_xml_other(msg)
    # added by Paul Tremblay on 2004-02-19
    # the environment in context is \startenvironmentname ...
    # \stopenvironmentname
    if self.__use_context:
        begenv = attrs.get('start', 'start')
    else:
        begenv = attrs.get('begin', 'begin')
    self.cmdname_stack.append(self.cmdname)
    self.endenv_stack.append(self.endenv)
    self.cmdname = name

    # added by Paul Tremblay on 2004-02-19
    if self.__use_context:
        self.endenv  = attrs.get('stop',   'stop')
    else:
        self.endenv  = attrs.get('end',   'end')
    #
    # Write <env/> and setup newline processing
    #
    if self.get_boolean(attrs, 'nl1', 1):
      self.writer.conditionalNewline()

    # added by Paul Tremblay on 2004-02-19
    # See note above
    if self.__use_context:
        self.writer.write('\%s%s' % (begenv, name), 0)
    else:
        self.writer.write('\%s{%s}' % (begenv, name), 0)
    if self.get_boolean(attrs, 'nl2', 1):
      self.writer.writeWeakWS(texmlwr.WEAK_WS_IS_NEWLINE)
    self.nl_spec_stack.append(self.nl_spec)
    self.nl_spec = (self.get_boolean(attrs, 'nl3', 1), self.get_boolean(attrs, 'nl4', 1))

  def on_env_end(self):
    nl3, nl4 = self.nl_spec
    self.nl_spec = self.nl_spec_stack.pop()
    if nl3:
      self.writer.conditionalNewline()

    # added by Paul Tremblay on 2004-02-19
    if self.__use_context:
        self.writer.write('\%s%s' % (self.endenv, self.cmdname), 0)
    else:
        self.writer.write('\%s{%s}' % (self.endenv, self.cmdname), 0)
    if nl4:
      self.writer.conditionalNewline()
    self.cmdname = self.cmdname_stack.pop()
    self.endenv  = self.endenv_stack.pop()

  def on_group(self, attrs):
    """ Handle 'group' element """
    self.stack_model(self.model_content)
    self.writer.writech('{', 0)

  def on_group_end(self):
    self.writer.writech('}', 0)

  # -----------------------------------------------------------------

  def on_ctrl(self, attrs):
    #
    # Get character, check and print tex command
    #
    ch = attrs.get('ch', '')
    if 1 != len(ch):
      msg = 'Invalid XML %s, %s: ' % (self.__col_num, self.__line_num)
      msg += "Attribute ctrl/@ch is not a char: '%s'" % ch 
      self.invalid_xml_other(msg)
    self.writer.writech('\\', 0)
    self.writer.writech(ch,   0)
    #
    # Content of this element is empty
    #
    self.stack_model({})
    self.no_text_content = 1

  def on_ctrl_end(self):
    self.no_text_content = 0

  def on_spec(self, attrs):
    #
    # Get category, get corresponding character
    #
    cat = attrs.get('cat', '')
    if 'nl?' == cat:
      self.writer.conditionalNewline()
    else:
      if not (cat in specmap.tocharmap):
        msg = 'Invalid XML %s, %s: ' % (self.__col_num, self.__line_num)
        msg += "Attribute spec/@cat unknown: '%s'" % cat 
        self.invalid_xml_other(msg)
      ch = specmap.tocharmap[cat]
      if '\n' == ch:
        self.writer.stack_emptylines(1)
      self.writer.write(ch, 0)
      if '\n' == ch:
        self.writer.unstack_emptylines()
    #
    # Content of this element is empty
    #
    self.stack_model({})
    self.no_text_content = 1

  def on_spec_end(self):
    self.no_text_content = 0

  # -----------------------------------------------------------------

  def on_math(self, attrs):
    self.stack_model(self.model_nomath)
    self.writer.writech('$', 0)
    self.writer.stack_mode(texmlwr.MATH)

  def on_math_end(self):
    self.writer.unstack_mode()
    self.writer.writech('$', 0)

  def on_dmath(self, attrs):
    self.writer.writech('$', 0)
    self.on_math(attrs)

  def on_dmath_end(self):
    self.on_math_end()
    self.writer.writech('$', 0)
    
  # -----------------------------------------------------------------

  def on_pdf(self, attrs):
    self.stack_model({})
    self.writer.stack_mode(texmlwr.PDF)

  def on_pdf_end(self):
    self.writer.unstack_mode()
