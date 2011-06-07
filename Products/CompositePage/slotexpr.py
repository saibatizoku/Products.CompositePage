##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Visible Source 
# License, Version 1.0 (ZVSL).  A copy of the ZVSL should accompany this 
# distribution.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Support for 'slot:' expression type in ZPT.

$Id: slotexpr.py,v 1.5 2004/05/03 16:02:40 sidnei Exp $
"""

import logging
import re

from zope.tales.tales import CompilerError

from Products.CompositePage.interfaces import IComposite

name_re = re.compile("\s*([a-zA-Z][a-zA-Z0-9_]*)")
class_name_re = re.compile("\s*[(]([a-zA-Z][a-zA-Z0-9_]*)[)]")
title_re = re.compile("\s*[']([^']+)[']")

log = logging.getLogger(__name__)


class SlotExpr(object):
    """Slot expression type.

    Provides a concise syntax for specifying composite slots in
    ZPT.  An example slot expression, in context of ZPT:

    <div tal:replace="slot: slot_name(class_name) 'Title'" />
    """

    def __init__(self, name, expr, engine):
        self._s = s = expr.strip()
        mo = name_re.match(s)
        if mo is None:
            raise CompilerError('Invalid slot expression "%s"' % s)
        self._name = mo.group(1)
        s = s[mo.end():]
        mo = class_name_re.match(s)
        if mo is not None:
            self._class_name = mo.group(1)
            s = s[mo.end():]
        else:
            self._class_name = None
        mo = title_re.match(s)
        if mo is not None:
            self._title = mo.group(1)
            s = s[mo.end():]
        else:
            self._title = None
        if s.strip():
            # Can't interpret some of the expression
            raise CompilerError(
                'Slot expression syntax error near %s' % repr(s))

    def __call__(self, econtext):
        context = econtext.contexts.get('options')
        if context is None:
            raise RuntimeError("Could not find options")
        composite = context.get('composite')
        if IComposite.providedBy(composite):
            slot = composite.slots.get(
                self._name, self._class_name, self._title)
            # Render the slot
            return unicode(slot)
        else:
            # Show the default content
            return econtext.getDefault()

    def __repr__(self):
        return '<SlotExpr %s>' % repr(self._s)


def registerSlotExprType():
    # Register the 'slot:' expression type.

    # Register with Products.PageTemplates.
    try:
        from Products.PageTemplates.Expressions import getEngine
    except ImportError:
        log.exception("Unable to register the slot expression type")
    else:
        engine = getEngine()
        if not engine.getTypes().has_key('slot'):
            engine.registerType('slot', SlotExpr)

    # Register with zope.tales.
    try:
        from zope.tales.engine import Engine
    except ImportError:
        log.exception("Unable to register the slot expression type")
    else:
        if not Engine.getTypes().has_key('slot'):
            Engine.registerType('slot', SlotExpr)
