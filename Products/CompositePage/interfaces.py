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
"""Interfaces and exceptions in the CompositePage product.

$Id: interfaces.py,v 1.14 2004/04/15 22:13:44 shane Exp $
"""

from zope.interface import Attribute
from zope.interface import Interface


class CompositeError(Exception):
    """An error in constructing a composite
    """


class IComposite(Interface):
    """An object whose rendering is composed of a layout and elements.
    """
    slots = Attribute("An ISlotGenerator.")

    def __call__():
        """Renders the composite as a string.
        """


class ISlotGenerator(Interface):

    def get(name, class_name=None, title=None):
        """Returns a slot, creating it if it does not yet exist.

        The 'class_name' and 'title' arguments allow the caller to
        specify a slot class and title.  Both are used for composite
        design purposes, not rendering.
        """

    def __getitem__(name):
        """Returns a slot, creating it if it does not yet exist.
        """


class ISlot(Interface):
    """A slot in a composite.
    """

    def single():
        """Renders to a string as a single-element slot.
        """

    def multiple():
        """Renders to a sequence of strings as a multiple-element slot.
        """

    def reorder(name, new_index):
        """Moves an item to a new index.
        """

    def nullify(name):
        """Removes an item from the slot, returning the old item.

        Leaves a null element in its place.  The null element ensures
        that other items temporarily keep their index within the slot.
        """

    def pack():
        """Removes all null elements from the slot.
        """


class ISlotClass(Interface):
    """Parameters and constraints for a slot.
    """

    # inline_templates is an attribute listing allowed template names.  If
    # this list is not empty, it is intersected with the inline templates
    # provided by the object type to determine what templates are
    # available.  If this list is empty, all inline templates provided by
    # the object type are available.

    def findAvailableElements():
        """Returns a list of elements available for this slot.

        Generally returns catalog results.
        """


class ICompositeElement(Interface):
    """Interface of objects that can be part of a composite.
    """

    def renderInline():
        """Returns a representation of this object as a string.
        """

    def queryInlineTemplate(slot_class_name=None):
        """Returns the name of the inline template this object uses.

        Returns None if none has been chosen and there is no default.

        The slot_class_name may be provided as an optimization.
        """

    def setInlineTemplate(template):
        """Sets the inline template for this object.
        """

    def listAllowableInlineTemplates(slot_class_name=None):
        """Returns a list of templates allowable for this object.

        Returns a list of (template_name, template_object).

        The slot_class_name may be provided as an optimization.
        """

    def dereference():
        """Returns the object to be rendered.
        """
