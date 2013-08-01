#!/usr/bin/python
# twisted_pep8.py - Check Python source code formatting, according to the
# Twisted Coding Standard.
#
# This monkey-patches the pep8 module to replace checks that conflict with the
# Twisted Coding Standard, and uses pep8 to check the Python source code.

"""
Check Python source code formatting, according to the Twisted Coding Standard
(http://twistedmatrix.com/trac/browser/trunk/doc/core/development/policy/coding-standard.xhtml?format=raw)

This script is dependent upon the pep8 module which can be found at:
http://github.com/jcrocholl/pep8
"""

try:
    # Try to import SublimeLinter to guarantee that it runs before we do, so
    # there's something to patch.
    import sublimelinter.modules.python
    sublimelinter
except ImportError:
    pass


import re
import fnmatch
import os

from pep8 import DOCSTRING_REGEX, expand_indent

if 'original_blank_lines' not in globals():
    from pep8 import blank_lines as original_blank_lines



class StyleDeterminer(object):

    def readConfig(self):
        conf = os.path.expanduser("~/.twisted-pep8-paths.txt")
        if os.path.exists(conf):
            with open(conf) as f:
                lines = f.read().split("\n")
            regex = '({0})'.format('|'.join(map(fnmatch.translate, lines)))
            self.regex = re.compile(regex)
        else:
            self.regex = re.compile('.*')


    def isTwistedStyle(self, pathname):
        """
        Should this function be PEP style-checked according to Twisted or vanilla
        PEP8 style?  Attempt to guess based on the file name.
        """
        return self.regex.match(pathname)


determiner = StyleDeterminer()

isTwistedStyle = determiner.isTwistedStyle


def inFunctionBody(line_number, lines):
    """
    Return (unfortunately just, an educated guess as to) whether the given line
    number in the given list of lines is in a function body (as opposed to a
    class body, or some other kind of suite) or not.
    """
    current_indent = expand_indent(lines[line_number])
    for x in xrange(line_number, 0, -1):
        line = lines[x-1]
        if expand_indent(line) < current_indent:
            if line.startswith("def "):
                return True
            if line.startswith("class "):
                return False
    return False



checkingFilename = None
lastLine = None

def twisted_blank_lines(logical_line, blank_lines, indent_level, line_number,
                        previous_logical, previous_indent_level,
                        # Not required by previous implementation:
                        filename, lines):
    r"""
    Twisted Coding Standard:

    Separate top-level function and class definitions with three blank lines.
    Method definitions inside a class are separated by two blank lines.

    Extra blank lines may be used (sparingly) to separate groups of related
    functions.  Blank lines may be omitted between a bunch of related
    one-liners (e.g.  a set of dummy implementations).

    Use blank lines in functions, sparingly, to indicate logical sections.::

        Okay: def a():\n    pass\n\n\n\ndef b():\n    pass
        Okay: class A():\n    pass\n\n\n\nclass B():\n    pass
        Okay: def a():\n    pass\n\n\n# Foo\n# Bar\n\ndef b():\n    pass

        E301: class Foo:\n    b = 0\n    def bar():\n        pass
        E302: def a():\n    pass\n\ndef b(n):\n    pass
        E303: def a():\n    pass\n\n\n\ndef b(n):\n    pass
        E303: def a():\n\n\n\n    pass
        E304: @decorator\n\ndef a():\n    pass
        E305: "comment"\n\n\ndef a():\n    pass
        E306: variable="value"\ndef a():   pass
    """
    global checkingFilename, lastLine
    if ((checkingFilename is None or lastLine is None or
         checkingFilename != filename or lastLine < line_number)):
        # If we're running a new check, re-read the configuration.
        determiner.readConfig()

    if checkingFilename != filename:
        pass
    # Don't expect blank lines before the first line
    if line_number == 1:
        return

    if not isTwistedStyle(filename):
        for value in original_blank_lines(logical_line, blank_lines,
                                          indent_level, line_number,
                                          previous_logical,
                                          previous_indent_level):
            yield value
        return

    def isClassDefDecorator(thing):
        return (thing.startswith('def ') or
                thing.startswith('class ') or
                thing.startswith('@'))

    previous_is_comment = DOCSTRING_REGEX.match(previous_logical)

    # no blank lines after a decorator
    if previous_logical.startswith('@'):
        if blank_lines:
            yield 0, "E304 blank lines found after function decorator <T>"

    # should not have more than 3 blank lines
    elif blank_lines > 3 or (indent_level and blank_lines > 2):
        yield 0, "E303 too many blank lines (%d) <T>" % blank_lines

    elif isClassDefDecorator(logical_line):
        if indent_level:
            # There should only be 1 line or less between docstrings and
            # the next function
            if previous_is_comment:
                if blank_lines > 1:
                    yield 0, (
                        "E305 too many blank lines after docstring (%d) <T>" %
                        blank_lines)

            # between first level functions, there should be 2 blank lines.
            # any further indended functions can have one or zero lines
            else:
                if not (blank_lines == 2 or
                        indent_level > 4 or
                        previous_indent_level <= indent_level or
                        inFunctionBody(line_number, lines)):
                    yield 0, ("E301 expected 2 blank lines, found %d <T>" %
                              blank_lines)

        # top level, there should be 3 blank lines between class/function
        # definitions (but not necessarily after varable declarations)
        elif previous_indent_level and blank_lines != 3:
            yield 0, "E302 expected 3 blank lines, found %d <T>" % blank_lines

    elif blank_lines > 1 and indent_level:
        yield 0, "E303 too many blank lines, expected (%d) <T>" % blank_lines


try:
    import pep8
    for name in ['blank_lines']:
        setattr(pep8, name, globals()['twisted_'+name])
    pep8._checks = {'physical_line': {}, 'logical_line': {}, 'tree': {}}
    pep8.init_checks_registry()
except:
    print("Unable to import PEP8.")



def _main():
    try:
        import pep8
        pep8._main()
    except:
        print 'Unable to import pep8'



if __name__ == '__main__':
    _main()
