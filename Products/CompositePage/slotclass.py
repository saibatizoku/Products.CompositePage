##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
# All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
# 
##############################################################################
"""Slot classes.

$Id: slotclass.py,v 1.1 2004/03/02 20:41:44 shane Exp $
"""

import os

from Acquisition import aq_inner, aq_parent
from OFS.SimpleItem import SimpleItem
from OFS.PropertyManager import PropertyManager
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from zope.interface import implements

from Products.CompositePage.interfaces import ISlotClass


_www = os.path.join(os.path.dirname(__file__), "www")


class SlotClass(SimpleItem, PropertyManager):
    """Parameters and constraints for a slot.
    """
    implements(ISlotClass)
    meta_type = "Composite Slot Class"
    find_script = ""

    manage_options = (PropertyManager.manage_options
                      + SimpleItem.manage_options)

    _properties = (
        {'id': 'find_script', 'mode': 'w', 'type': 'string',
         'label': 'Script that finds available elements',},
        )

    def findAvailableElements(self, slot):
        if not self.find_script:
            return None
        tool = aq_parent(aq_inner(aq_parent(aq_inner(self))))
        s = tool.restrictedTraverse(self.find_script)
        return s(slot)


addSlotClassForm = PageTemplateFile("addSlotClassForm.zpt", _www)

def manage_addSlotClass(dispatcher, id, REQUEST=None):
    """Adds a slot class to a composite tool.
    """
    ob = SlotClass()
    ob._setId(id)
    dispatcher._setObject(ob.getId(), ob)
    if REQUEST is not None:
        return dispatcher.manage_main(dispatcher, REQUEST)

