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
"""Composite tool.

$Id: tool.py,v 1.11 2004/03/02 20:41:44 shane Exp $
"""

import Globals
from Acquisition import aq_base, aq_parent, aq_inner
from OFS.SimpleItem import SimpleItem
from OFS.Folder import Folder
from OFS.CopySupport import _cb_encode, _cb_decode, cookie_path
from AccessControl import ClassSecurityInfo
from AccessControl.ZopeGuards import guarded_getattr

from Products.CompositePage.interfaces import ICompositeElement
from Products.CompositePage.interfaces import ISlot
from Products.CompositePage.interfaces import ISlotClass
from Products.CompositePage.interfaces import CompositeError
from Products.CompositePage.element import CompositeElement
from Products.CompositePage.utils import copyOf


_uis = {}

def registerUI(name, obj):
    """Registers a page design UI for use with the composite tool.

    Replaces any existing registration.
    """
    obj._setId(name)
    _uis[name] = obj



class DesignUIs(SimpleItem):
    """The container of design user interface objects.

    Makes page design UIs accessible through URL traversal.
    """

    def __init__(self, id):
        self._setId(id)

    def __getattr__(self, name):
        try:
            return _uis[name]
        except KeyError:
            raise AttributeError, name


class SlotClassFolder(Folder):
    """Container of slot classes.
    """
    meta_type = "Slot Class Folder"

    def all_meta_types(self):
        return Folder.all_meta_types(self, interfaces=(ISlotClass,))


class CompositeTool(Folder):
    """Page composition helper tool.
    """
    meta_type = "Composite Tool"
    id = "composite_tool"

    security = ClassSecurityInfo()

    security.declarePublic("uis")
    uis = DesignUIs("uis")

    _properties = Folder._properties + (
        {'id': 'default_inline_templates', 'mode': 'w', 'type': 'lines',
         'label': 'Default inline template names',},
        )

    default_inline_templates = ()

    _check_security = 1  # Turned off in unit tests

    def __init__(self):
        scf = SlotClassFolder()
        scf._setId("slot_classes")
        self._setObject(scf.id, scf)
        self._reserved_names = ('slot_classes',)

    security.declarePublic("moveElements")
    def moveElements(self, source_paths, target_path, target_index, copy=0):
        """Moves or copies elements to a slot.
        """
        target_index = int(target_index)
        # Coerce the paths to sequences of path elements.
        if hasattr(target_path, "split"):
            target_path = target_path.split('/')
        sources = []
        for p in source_paths:
            if hasattr(p, "split"):
                p = p.split('/')
            if p:
                sources.append(p)

        # Ignore descendants when an ancestor is already listed.
        i = 1
        sources.sort()
        while i < len(sources):
            prev = sources[i - 1]
            if sources[i][:len(prev)] == prev:
                del sources[i]
            else:
                i = i + 1

        # Prevent parents from becoming their own descendants.
        for source in sources:
            if target_path[:len(source)] == source:
                raise CompositeError(
                    "Can't make an object a descendant of itself")

        # Gather the sources, checking interfaces and security before
        # making any changes.
        root = self.getPhysicalRoot()
        elements = []
        target = root.restrictedTraverse(target_path)
        assert ISlot.providedBy(target), repr(target)
        for source in sources:
            slot = root.restrictedTraverse(source[:-1])
            assert ISlot.providedBy(slot), repr(slot)
            element = slot.restrictedTraverse(source[-1])
            elements.append(element)
            if self._check_security:
                target._verifyObjectPaste(element)

        changed_slots = {}  # id(aq_base(slot)) -> slot
        try:
            if not copy:
                # Replace items with nulls to avoid changing indexes
                # while moving.
                for source in sources:
                    slot = root.restrictedTraverse(source[:-1])
                    slot_id = id(aq_base(slot))
                    if not changed_slots.has_key(slot_id):
                        changed_slots[slot_id] = slot
                    # Check security
                    nullify = guarded_getattr(slot, "nullify")
                    nullify(source[-1])

            # Add the elements and reorder.
            for element in elements:

                if not ICompositeElement.providedBy(element):
                    # Make a composite element wrapper.
                    element = CompositeElement(element.getId(), element)

                element = aq_base(element)
                new_id = target._get_id(element.getId())
                if copy:
                    element = copyOf(element)
                element._setId(new_id)
                target._setObject(new_id, element)
                # Check security
                reorder = guarded_getattr(target, "reorder")
                reorder(new_id, target_index)
                target_index += 1
        finally:
            # Clear the nulls just added.
            for slot in changed_slots.values():
                slot.pack()


    security.declarePublic("deleteElements")
    def deleteElements(self, source_paths):
        sources = []
        for p in source_paths:
            if hasattr(p, "split"):
                p = p.split('/')
            if p:
                sources.append(p)

        # Replace with nulls to avoid changing indexes while deleting.
        orig_slots = {}
        try:
            for source in sources:
                slot = self.restrictedTraverse(source[:-1])
                assert ISlot.providedBy(slot), repr(slot)
                slot_id = id(aq_base(slot))
                if not orig_slots.has_key(slot_id):
                    orig_slots[slot_id] = slot
                nullify = guarded_getattr(slot, "nullify")  # Check security
                nullify(source[-1])
        finally:
            # Clear the nulls just added.
            for slot in orig_slots.values():
                slot.pack()


    security.declarePublic("moveAndDelete")
    def moveAndDelete(self, move_source_paths="", move_target_path="",
                      move_target_index="", delete_source_paths="",
                      REQUEST=None):
        """Move and/or delete elements.
        """
        if move_source_paths:
            p = move_source_paths.split(':')
            self.moveElements(p, move_target_path, int(move_target_index))
        if delete_source_paths:
            p = delete_source_paths.split(':')
            self.deleteElements(p)
        if REQUEST is not None:
            # Return to the page the user was looking at.
            REQUEST["RESPONSE"].redirect(REQUEST["HTTP_REFERER"])


    security.declarePublic("useClipboard")
    def useClipboard(self, func, REQUEST,
                     source_paths=None, target_path=None, target_index=None):
        """Clipboard interaction.
        """
        resp = REQUEST['RESPONSE']
        if func in ("cut", "copy"):
            assert source_paths
            items = []  # list of path tuples
            cut = (func == 'cut')
            for p in str(source_paths).split(':'):
                items.append(p.split('/'))
            data = _cb_encode((cut, items))
            resp.setCookie('__cp', data, path=cookie_path(REQUEST))
        elif func == 'paste':
            assert target_path
            assert target_index
            assert REQUEST is not None
            data = REQUEST['__cp']
            cut, items = _cb_decode(data)
            self.moveElements(
                items, target_path, int(target_index), not cut)
            resp.expireCookie('__cp', path=cookie_path(REQUEST))
        else:
            raise ValueError("Clipboard function %s unknown" % func)
        resp.redirect(REQUEST["HTTP_REFERER"])

Globals.InitializeClass(CompositeTool)


def manage_addCompositeTool(dispatcher, REQUEST=None):
    """Adds a composite tool to a folder.
    """
    ob = CompositeTool()
    dispatcher._setObject(ob.getId(), ob)
    if REQUEST is not None:
        return dispatcher.manage_main(dispatcher, REQUEST)

