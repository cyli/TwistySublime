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

from pep8 import DOCSTRING_REGEX

import sys


def blank_lines(logical_line, blank_lines, indent_level, line_number,
                previous_logical, previous_indent_level,
                blank_lines_before_comment):
    """
    Twisted Coding Standard:

    Separate top-level function and class definitions with three blank lines.
    Method definitions inside a class are separated by two blank lines.

    Extra blank lines may be used (sparingly) to separate groups of related
    functions.  Blank lines may be omitted between a bunch of related
    one-liners (e.g. a set of dummy implementations).

    Use blank lines in functions, sparingly, to indicate logical sections.

    Okay: def a():\n    pass\n\n\n\ndef b():\n    pass
    Okay: class A():\n    pass\n\n\n\nclass B():\n    pass
    Okay: def a():\n    pass\n\n\n# Foo\n# Bar\n\ndef b():\n    pass

    E301: class Foo:\n    b = 0\n    def bar():\n        pass
    E302: def a():\n    pass\n\ndef b(n):\n    pass
    E303: def a():\n    pass\n\n\n\ndef b(n):\n    pass
    E303: def a():\n\n\n\n    pass
    E304: @decorator\n\ndef a():\n    pass
    E305: "comment"\n\n\ndef a():\n    pass
    """

    def isClassDefDecorator(thing):
        return (thing.startswith('def ') or
                thing.startswith('class ') or
                thing.startswith('@'))

    if line_number == 1:
        return  # Don't expect blank lines before the first line
    max_blank_lines = max(blank_lines, blank_lines_before_comment)
    if previous_logical.startswith('@'):
        if max_blank_lines:
            return 0, "E304 blank lines found after function decorator"
    elif max_blank_lines > 3 or (indent_level and max_blank_lines == 3):
        return 0, "E303 too many blank lines (%d)" % max_blank_lines
    elif isClassDefDecorator(logical_line):
        if indent_level:
            # There should only be 1 line or less between docstrings and
            # the next function
            if DOCSTRING_REGEX.match(previous_logical) and max_blank_lines > 1:
                return (0, "E305 too many blank lines after docstring (%d)" %
                    max_blank_lines)
            # between first level functions, there should be 2 blank lines.
            # any further indended functions can have one or zero lines
            if not (max_blank_lines == 2 or
                    indent_level > 4 or
                    previous_indent_level < indent_level or
                    not isClassDefDecorator(previous_logical)):
                return 0, ("E301 expected 2 blank lines, found %d" %
                           max_blank_lines)
        elif max_blank_lines != 3:
            return 0, "E302 expected 3 blank lines, found %d" % max_blank_lines
    elif max_blank_lines > 1 and indent_level:
        return 0, "E303 too many blank lines expected (%d)" % max_blank_lines



try:
    import pep8

    for name in ['blank_lines']:
        setattr(sys.modules['pep8'], name, globals()[name])
except:
    pass



def _main():
    try:
        import pep8
        pep8._main()
    except:
        print 'Unable to import pep8'



if __name__ == '__main__':
    _main()
