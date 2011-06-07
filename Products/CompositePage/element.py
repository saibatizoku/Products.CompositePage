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
"""Composite element.

$Id: element.py,v 1.5 2004/04/14 16:15:29 sidnei Exp $
"""

import os

import Globals
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_get
from OFS.SimpleItem import SimpleItem
from OFS.PropertyManager import PropertyManager
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from DocumentTemplate.DT_Util import safe_callable

from zope.interface import implements

from Products.CompositePage.interfaces import ICompositeElement

_www = os.path.join(os.path.dirname(__file__), "www")


class CompositeElement(SimpleItem, PropertyManager):
    """A simple path-based reference to an object and a template.

    You can render it and choose which template to apply for rendering.
    """
    implements(ICompositeElement)
    meta_type = "Composite Element"
    security = ClassSecurityInfo()
    manage_options = PropertyManager.manage_options + SimpleItem.manage_options

    _properties = (
        {'id': 'path', 'type': 'string', 'mode': 'w',},
        {'id': 'template_name', 'type': 'string', 'mode': 'w',},
        )

    template_name = ''

    def __init__(self, id, obj):
        self.id = id
        self.path = '/'.join(obj.getPhysicalPath())

    def dereference(self):
        """Returns the object referenced by this composite element.
        """
        return self.restrictedTraverse(self.path)

    def renderInline(self):
        """Returns a representation of this object as a string.
        """
        obj = self.dereference()
        name = self.template_name
        if not name:
            # Default to the first allowable inline template.
            names = self.listAllowableInlineTemplates()
            if names:
                name = names[0]
        if name and name != "call":
            template = obj.restrictedTraverse(str(name))
            return template()
        # Special template name "call" means to call the object.
        if safe_callable(obj):
            return obj()
        return unicode(obj)

    def queryInlineTemplate(self, slot_class_name=None):
        """Returns the name of the inline template this object uses.
        """
        return self.template_name

    def setInlineTemplate(self, template):
        """Sets the inline template for this object.
        """
        self.template_name = str(template)

    def listAllowableInlineTemplates(self, slot_class_name=None):
        """Returns a list of inline template names allowable for this object.
        """
        tool = aq_get(self, "composite_tool", None, 1)
        if tool is not None:
            res = []
            for name in tool.default_inline_templates:
                template = obj.restrictedTraverse(str(name))
                res.append((name, template))
            return res
        # No tool found, so no inline templates are known.
        return ()

Globals.InitializeClass(CompositeElement)


addElementForm = PageTemplateFile("addElementForm.zpt", _www)

def manage_addElement(dispatcher, id, path, template_name=None, REQUEST=None):
    """Adds an element to a slot.
    """
    target = dispatcher.restrictedTraverse(path)
    ob = CompositeElement(str(id), target)
    if template_name:
        ob.template_name = str(template_name)
    dispatcher._setObject(ob.getId(), ob)
    if REQUEST is not None:
        return dispatcher.manage_main(dispatcher, REQUEST)
