""" TeXML Writer and string services """
# $Id: texmlwr.py,v 1.9 2006-07-20 03:56:27 olpa Exp $

#
# Modes of processing of special characters
#
DEFAULT = 0
TEXT    = 1
MATH    = 2
ASIS    = 3
PDF     = 4
WEAK_WS_IS_NEWLINE = 2

import unimap
import specmap
import codecs
import os
import sys
import string

#
# Writer&Co class
#
class texmlwr:
  
  #
  # Object variables
  #
  # Handling of '--', '---' and other ligatures
  # last_char
  #
  # Modes of transformation can be tuned and nested
  # mode
  # mode_stack
  # escape
  # escape_stack
  # ligatures
  # ligatures_stack
  # emptylines
  # emptylines_stack
  #
  # Current length of a line that is being written. Value usually
  # incorrect, but always correct to detect the start of a line (0)
  # > approx_current_line_len
  # If length of a current line is greater the value
  # then writer converts weak whitespaces into newlines.
  # And flag if it is possible
  # > autonewline_after_len
  # > allow_weak_ws_to_nl
  # > is_after_weak_ws
  # We usually don't allow empty lines in output because such lines
  # cause a paragraph break in TeX.
  # > line_is_blank
  #
  # always_ascii: If attempts to write a character to the output
  # stream have failed, then the code converts the symbol to bytes,
  # and these bytes are written in the ^^xx format.
  #
  # bad_enc_warned: TeXML issues warning if it fails to convert
  # a symbol. This flag controls that warning was issued only once.
  #
  
  def __init__(self, stream, encoding, autonl_width, use_context = 0, always_ascii = 0):
    """ Remember output stream, initialize data structures """
    # Tune output stream
    self.always_ascii = always_ascii
    self.encoding     = encoding
    try:
      if always_ascii:
        encoding        = 'ascii'
      self.stream     = stream_encoder(stream, encoding)
    except Exception, e:
      raise ValueError("Can't create encoder: '%s'" % e)
    # Continue initialization
    self.after_char0d     = 1
    self.after_char0a     = 1
    self.last_ch          = None
    self.line_is_blank    = 1
    self.mode             = TEXT
    self.mode_stack       = []
    self.escape           = 1
    self.escape_stack     = []
    self.ligatures        = 0
    self.ligatures_stack  = []
    self.emptylines       = 0
    self.emptylines_stack = []
    self.approx_current_line_len = 0
    self.autonewline_after_len   = autonl_width
    self.allow_weak_ws_to_nl     = 1
    self.is_after_weak_ws        = 0
    self.use_context      = use_context
    self.bad_enc_warned   = 0

  def stack_mode(self, mode):
    """ Put new mode into the stack of modes """
    self.mode_stack.append(self.mode)
    if mode != DEFAULT:
      self.mode = mode

  def unstack_mode(self):
    """ Restore mode """
    self.mode = self.mode_stack.pop()

  def stack_escape(self, ifdo):
    """ Set if escaping is required. Remember old value. """
    self.escape_stack.append(self.escape)
    if ifdo != None:
      self.escape = ifdo

  def unstack_escape(self):
    """ Restore old policy of escaping """
    self.escape = self.escape_stack.pop()

  def stack_ligatures(self, ifdo):
    """ Set if breaking of ligatures is required. Remember old value. """
    self.ligatures_stack.append(self.ligatures)
    if ifdo != None:
      self.ligatures = ifdo

  def unstack_ligatures(self):
    """ Restore old policy of breaking ligatures """
    self.ligatures = self.ligatures_stack.pop()

  def stack_emptylines(self, ifdo):
    """ Set if empty lines are required. Remember old value. """
    self.emptylines_stack.append(self.emptylines)
    if ifdo != None:
      self.emptylines = ifdo

  def unstack_emptylines(self):
    """ Restore old policy of handling of empty lines """
    self.emptylines = self.emptylines_stack.pop()

  def set_allow_weak_ws_to_nl(self, flag):
    """ Set flag if weak spaces can be converted to new lines """
    self.allow_weak_ws_to_nl = flag

  def conditionalNewline(self):
    """ Write a new line unless already at the start of a line """
    if self.approx_current_line_len != 0:
      self.writech('\n', 0)

  def writeWeakWS(self, hint=1):
    """ Write a whitespace instead of whitespaces deleted from source XML. Parameter 'hint' is a hack to make <opt/> and <parm/> in <env/> working good. hint=WEAK_WS_IS_NEWLINE if weak space should be converted to newline, not to a space """
    # weak WS that is newline can not be converted to ws that is space
    if hint <= self.is_after_weak_ws:
      # return or avoid next if(). I prefer return.
      return                                               # return
    self.is_after_weak_ws = hint
    #self.last_ch          = ' ' # no, setting so is an error: new lines are not corrected after it. Anyway, check for weak ws is the first action in writech, so it should not lead to errors
    #
    # Break line if it is too long
    # We should not break lines if we regard spaces
    # Check for WEAK_WS_IS_NEWLINE in order to avoid line break in
    #   \begin{foo}[aa.....aa]<no line break here!>[bbb]
    #
    if (self.approx_current_line_len > self.autonewline_after_len) and self.allow_weak_ws_to_nl and (hint != WEAK_WS_IS_NEWLINE):
      self.conditionalNewline()
      return                                               # return

  def ungetWeakWS(self):
    """ Returns whitespace state and clears WS flag """
    hint = self.is_after_weak_ws
    self.is_after_weak_ws = 0
    return hint

  def writech(self, ch, esc_specials):
    """ Write a char, (maybe) escaping specials """
    #
    # Write for PDF string
    #
    if  PDF == self.mode:
      self.stack_mode(TEXT)
      self.writepdfch(ch)
      self.unstack_mode()
      return                                               # return
    #
    # Write a suspended whitespace
    #
    if self.is_after_weak_ws:
      hint = self.is_after_weak_ws
      self.is_after_weak_ws = 0
      if hint == WEAK_WS_IS_NEWLINE:
        if ('\n' != ch) and ('\r' != ch):
          self.conditionalNewline()
      else:
        if (self.approx_current_line_len != 0) and not(ch in string.whitespace):
          self.writech(' ', 0)
    #
    # Update counter
    #
    self.approx_current_line_len = self.approx_current_line_len + 1
    #
    # Handle well-known standard TeX ligatures
    #
    if not(self.ligatures):
      if '-' == ch:
        if '-' == self.last_ch:
          self.writech('{', 0)
          self.writech('}', 0)
      elif "'" == ch:
        if "'" == self.last_ch:
          self.writech('{', 0)
          self.writech('}', 0)
      elif '`' == ch:
        if ('`' == self.last_ch) or ('!' == self.last_ch) or ('?' == self.last_ch):
          self.writech('{', 0)
          self.writech('}', 0)
    #
    # Handle end-of-line symbols.
    # XML spec says: 2.11 End-of-Line Handling:
    # ... contains either the literal two-character sequence "#xD#xA" or
    # a standalone literal #xD, an XML processor must pass to the
    # application the single character #xA.
    #
    if ('\n' == ch) or ('\r' == ch):
      #
      # We should never get '\r', but only '\n'.
      # Anyway, someone will copy and paste this code, and code will
      # get '\r'. In this case rewrite '\r' as '\n'.
      #
      if '\r' == ch:
        ch = '\n'
      #
      # TeX interprets empty line as \par, fix this problem
      #
      if self.line_is_blank and (not self.emptylines):
        self.writech('%', 0)
      #
      # Now create newline, update counters and return
      #
      self.stream.write(os.linesep)
      self.approx_current_line_len = 0
      self.last_ch                 = ch
      self.line_is_blank           = 1
      return                                               # return
    #
    # Remember the last character
    #
    self.last_ch = ch
    #
    # Reset the flag of a blank line
    #
    if not ch in ('\x20', '\x09'):
      self.line_is_blank = 0
    #
    # Handle specials
    #
    if esc_specials:
      try:
        if self.mode == TEXT:
            # Paul Tremblay changed this code on 2005-03-08
          if self.use_context:
            self.write(specmap.textescmap_context[ch], 0)
          else:
            self.write(specmap.textescmap[ch], 0)
        else:
          self.write(specmap.mathescmap[ch], 0)
        return                                             # return
      except:
        pass
    #
    # First attempt to write symbol as-is
    #
    try:
      self.stream.write(ch)
      return                                               # return
    except:
      pass
    #
    # Try write the symbol in the ^^XX form
    #
    if self.always_ascii:
      try:
        bytes = ch.encode(self.encoding)
        for by in bytes:
          self.write('^^%02x' % ord(by), 0)
        return
      except Exception, e:
        pass
    #
    # Symbol have to be rewritten. Let start with math mode.
    #
    chord = ord(ch)
    if self.mode == TEXT:
      #
      # Text mode, lookup text map
      #
      try:
        self.write(unimap.textmap[chord], 0)
        return                                             # return
      except:
        #
        # Text mode, lookup math map
        #
        tostr = unimap.mathmap.get(chord, None)
    else: # self.mode == MATH:
      #
      # Math mode, lookup math map
      #
      try:
        self.write(unimap.mathmap[chord], 0)
        return                                             # return
      except:
        #
        # Math mode, lookup text map
        #
        tostr = unimap.textmap.get(chord, None)
    #
    # If mapping in another mode table is found, use a wrapper
    #
    if tostr != None:
      if self.mode == TEXT:
        self.write('\\ensuremath{', 0)
      else:
        self.write('\\ensuretext{', 0)
      self.write(tostr, 0)
      self.writech('}', 0)
      return                                               # return
    #
    # Finally, warn about bad symbol and write it in the &#xNNN; form
    #
    if not self.bad_enc_warned:
      sys.stderr.write("texml: not all XML symbols are converted\n");
      self.bad_enc_warned = 1
    self.write('\\unicodechar{%d}' % chord, 0)

  def write(self, str, escape = None):
    """ Write symbols char-by-char in current mode of escaping """
    if None == escape:
      escape = self.escape
    for ch in str:
      self.writech(ch, escape)

  def writepdfch(self, ch):
    """ Write char in Acrobat utf16be encoding """
    bytes = ch.encode('utf_16_be')
    for by in bytes:
      self.write('\\%03o' % ord(by), 0)
      
#
# Wrapper over output stream to write is desired encoding
#
class stream_encoder:

  def __init__(self, stream, encoding):
    """ Construct a wrapper by stream and encoding """
    self.stream = stream
    self.encode = codecs.getencoder(encoding)

  def write(self, str):
    """ Write string encoded """
    self.stream.write(self.encode(str)[0])

  def close(self):
    """ Close underlying stream """
    self.stream.close()

