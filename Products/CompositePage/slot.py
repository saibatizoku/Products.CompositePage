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
"""Slot class and supporting code.

$Id: slot.py,v 1.21 2004/04/26 09:30:25 gotcha Exp $
"""

import os
import sys
from cgi import escape

import Globals
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from Acquisition import aq_get
from ZODB.POSException import ConflictError
from OFS.SimpleItem import SimpleItem
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from AccessControl import ClassSecurityInfo
from zLOG import LOG, ERROR
from zope.interface import implements

from Products.CompositePage.interfaces import ICompositeElement
from Products.CompositePage.interfaces import ISlot
from Products.CompositePage.perm_names import view_perm
from Products.CompositePage.perm_names import change_composites_perm


try:
    # Use OrderedFolder if it's available.
    from OFS.OrderedFolder import OrderedFolder
except ImportError:
    # Fall back to normal folders, which happen to retain order anyway.
    from OFS.Folder import Folder as OrderedFolder

_www = os.path.join(os.path.dirname(__file__), "www")

target_tag = '''<div class="slot_target" title="Slot: %s [%d]"
target_path="%s" target_index="%d"></div>'''

edit_tag = '''<div class="slot_element" source_path="%s" icon="%s" title="%s">
<div class="slot_element_body">%s</div>
</div>'''

# view_tag includes a <div> just to ensure that the element is
# rendered as an HTML block in both editing mode and view mode.
view_tag = '''<div>
%s
</div>'''

# error_tag lets the user click on the 'log' link even if the
# container normally stops clicks.
error_tag = '''<span class="slot_error">%s
(<a href="%s" onmousedown="document.location=this.href">log</a>)</span>'''


class NullElement(SimpleItem):
    """Empty placeholder for slot content
    """
    meta_type = "Temporary Empty Slot Content"

    def __init__(self, id):
        self.id = id


class Slot(OrderedFolder):
    """A slot in a composite.
    """
    implements(ISlot)
    meta_type = "Composite Slot"

    security = ClassSecurityInfo()

    null_element = NullElement("null_element")


    def __init__(self, id):
        self.id = id

    def all_meta_types(self):
        return OrderedFolder.all_meta_types(
            self, interfaces=(ICompositeElement,))

    security.declareProtected(view_perm, "single")
    def single(self):
        """Renders as a single-element slot.

        Attempts to prevent the user from adding multiple elements
        by not providing insertion points when the slot already
        contains elements.
        """
        allow_add = (not self._objects)
        return "".join(self.renderToList(allow_add))

    security.declareProtected(view_perm, "multiple")
    def multiple(self):
        """Renders as a list containing multiple elements.
        """
        return self.renderToList(1)

    def __str__(self):
        """Renders as a string containing multiple elements.
        """
        return "".join(self.renderToList(1))

    __unicode__ = __str__

    security.declareProtected(change_composites_perm, "reorder")
    def reorder(self, name, new_index):
        if name not in self.objectIds():
            raise KeyError, name
        objs = [info for info in self._objects if info['id'] != name]
        objs.insert(new_index,
                    {'id': name, 'meta_type': getattr(self, name).meta_type})
        self._objects = tuple(objs)

    security.declareProtected(change_composites_perm, "nullify")
    def nullify(self, name):
        res = self[name]
        objs = list(self._objects)
        # Replace the item with a pointer to the null element.
        for info in objs:
            if info["id"] == name:
                info["id"] = "null_element"
        delattr(self, name)
        return res

    security.declareProtected(change_composites_perm, "nullify")
    def pack(self):
        objs = [info for info in self._objects if info["id"] != "null_element"]
        self._objects = tuple(objs)

    security.declareProtected(view_perm, "renderToList")
    def renderToList(self, allow_add):
        """Renders the items to a list.
        """
        res = ['<div class="slot_header"></div>']
        composite = aq_parent(aq_inner(aq_parent(aq_inner(self))))
        editing = composite.isEditing()
        items = self.objectItems()
        if editing:
            mypath = escape('/'.join(self.getPhysicalPath()))
            myid = self.getId()
            if hasattr(self, 'portal_url'):
                icon_base_url = self.portal_url()
            else:
                request = getattr(self, 'REQUEST', None)
                if request is not None:
                    icon_base_url = request['BASEPATH1']
                else:
                    icon_base_url = '/'

        if editing and allow_add:
            res.append(self._render_add_target(myid, 0, mypath))

        for index in range(len(items)):
            name, obj = items[index]

            try:
                assert ICompositeElement.providedBy(obj), (
                    "Not a composite element: %s" % repr(obj))
                text = obj.renderInline()
            except ConflictError:
                # Ugly ZODB requirement: don't catch ConflictErrors
                raise
            except:
                text = formatException(self, editing)


            if editing:
                res.append(self._render_editing(obj, text, icon_base_url))
            else:
                res.append(view_tag % text)
            
            if editing and allow_add:
                res.append(self._render_add_target(myid, index+1, mypath, obj.getId()))

        return res

    def _render_editing(self, obj, text, icon_base_url):
        o2 = obj.dereference()
        icon = getIconURL(o2, icon_base_url)
        title = o2.title_and_id()
        path = escape('/'.join(obj.getPhysicalPath()))
        return edit_tag % (path,
                               escape(icon), escape(title), text)

    def _render_add_target(self, slot_id, index, path, obj_id=''):
         return target_tag % (slot_id, index, path, index)
         
Globals.InitializeClass(Slot)


def getIconURL(obj, icon_base_url):
    base = aq_base(obj)
    if hasattr(base, 'getIcon'):
        icon = obj.getIcon()
    elif hasattr(base, 'icon'):
        icon = obj.icon
    else:
        icon = ""
    if icon and '://' not in icon:
        if not icon.startswith('/'):
            icon = '/' + icon
        icon = icon_base_url + icon
    return icon


def formatException(context, editing):
    """Returns an HTML-ified error message.

    If not editing, the message includes no details.
    """
    exc_info = sys.exc_info()
    try:
        if editing:
            # Show editors the real error
            t, v = exc_info[:2]
            t = getattr(t, '__name__', t)
            msg = "An error occurred. %s" % (
                escape(('%s: %s' % (t, v))[:80]))
        else:
            # Show viewers a simplified error.
            msg = ("An error occurred while generating "
                    "this part of the page.")
        try:
            log = aq_get(context, '__error_log__', None, 1)
            raising = getattr(log, 'raising', None)
        except AttributeError:
            raising = None

        if raising is not None:
            error_log_url = raising(exc_info)
            return error_tag % (msg, error_log_url)
        else:
            LOG("Composite", ERROR, "Error in a page element",
                error=exc_info)
            return msg
    finally:
        del exc_info


addSlotForm = PageTemplateFile("addSlotForm.zpt", _www)

def manage_addSlot(dispatcher, id, REQUEST=None):
    """Adds a slot to a composite.
    """
    ob = Slot(id)
    dispatcher._setObject(ob.getId(), ob)
    if REQUEST is not None:
        return dispatcher.manage_main(dispatcher, REQUEST)


def manage_generateSlots(dispatcher, REQUEST=None):
    """Adds all slots requested by a template to a composite.
    """
    dispatcher.this().generateSlots()
    if REQUEST is not None:
        return dispatcher.manage_main(dispatcher, REQUEST)
