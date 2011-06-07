##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""CompositePage product initialization.

$Id: __init__.py,v 1.7 2004/03/05 21:41:04 shane Exp $
"""

import tool, element, composite, slot, slotclass, designuis, interfaces
import slotexpr

slotexpr.registerSlotExprType()

tool.registerUI("common", designuis.CommonUI())
tool.registerUI("zmi", designuis.ZMIUI())
tool.registerUI("cmf", designuis.CMFUI())
tool.registerUI("manual", designuis.ManualUI())


def initialize(context):

    context.registerClass(
        tool.CompositeTool,
        constructors=(tool.manage_addCompositeTool,),
        icon="www/comptool.gif",
        )

    context.registerClass(
        element.CompositeElement,
        constructors=(element.addElementForm,
                      element.manage_addElement,
                      ),
        visibility=None,
        icon="www/element.gif",
        )

    context.registerClass(
        slotclass.SlotClass,
        constructors=(slotclass.addSlotClassForm,
                      slotclass.manage_addSlotClass,
                      ),
        interfaces=(interfaces.ISlotClass,),
        visibility=None,
        icon="www/slot.gif",
        )

    context.registerClass(
        composite.Composite,
        constructors=(composite.addCompositeForm,
                      composite.manage_addComposite,
                      ),
        icon="www/composite.gif",
        )

    context.registerClass(
        slot.Slot,
        constructors=(slot.addSlotForm,
                      slot.manage_addSlot,
                      slot.manage_generateSlots,
                      ),
        visibility=None,
        icon="www/slot.gif",
        )
