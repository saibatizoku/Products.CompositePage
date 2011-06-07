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
"""Composite class and supporting code.

$Id: composite.py,v 1.24 2004/04/15 22:13:44 shane Exp $
"""

import os
import re

import Globals
import Acquisition
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from Acquisition import aq_get
from OFS.Folder import Folder
from OFS.SimpleItem import SimpleItem
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from AccessControl import ClassSecurityInfo
from AccessControl.ZopeGuards import guarded_getattr
from zope.interface import implements

from Products.CompositePage.interfaces import IComposite
from Products.CompositePage.interfaces import ISlot
from Products.CompositePage.interfaces import ISlotGenerator
from Products.CompositePage.interfaces import CompositeError
from Products.CompositePage.slot import Slot
from Products.CompositePage.slot import getIconURL
from Products.CompositePage.slot import formatException
from Products.CompositePage.perm_names import view_perm
from Products.CompositePage.perm_names import change_composites_perm

_www = os.path.join(os.path.dirname(__file__), "www")


class SlotGenerator(Acquisition.Explicit):
    """Automatically makes slots available to the template.

    Note: instances of this class are shared across threads.
    """
    _slot_class = Slot

    def get(self, name, class_name=None, title=None):
        """Returns a slot by name.

        This is designed to be called in the middle of a page
        template.  Assigns attributes (class_name and title) to the
        slot at the same time.
        """
        name = str(name)
        composite = aq_parent(aq_inner(self))
        composite._usingSlot(name, class_name, title)
        slots = composite.filled_slots
        if slots.hasObject(name):
            return slots[name]
        else:
            # Generate a new slot.
            s = self._slot_class(name)
            if composite.isEditing():
                # Persist the slot.
                slots._setObject(s.getId(), s)
            # else don't persist the slot.
            return s.__of__(slots)

    __getitem__ = get


class CompositeMixin:
    """Base class for editable composite pages.

    Composite pages are assemblies of templates and composite
    elements.  This base class provides the nuts and bolts of a
    composite editing interface.
    """
    implements(IComposite)
    meta_type = "Composite"

    security = ClassSecurityInfo()

    manage_options = (
        {"label": "Design", "action": "manage_designForm",},
        {"label": "View", "action": "view",},
        )

    default_ui = "common"
    template_path = "template"
    _v_editing = 0
    _v_rendering = 0
    _v_slot_specs = None  # [{'name', 'class', 'title'}]

    security.declarePublic("slots")
    slots = SlotGenerator()

    _properties = (
        {"id": "template_path", "mode": "w", "type": "string",
         "label": "Path to template"},
        )

    security.declareProtected(view_perm, "hasTemplate")
    def hasTemplate(self):
        if self.template_path:
            return 1
        return 0

    security.declareProtected(view_perm, "getTemplate")
    def getTemplate(self):
        if not self.template_path:
            raise CompositeError("No template set")
        return self.restrictedTraverse(str(self.template_path))

    security.declareProtected(change_composites_perm, "generateSlots")
    def generateSlots(self):
        """Creates the slots defined by the template.
        """
        self._v_editing = 1
        try:
            self()
        finally:
            self._v_editing = 0

    security.declareProtected(view_perm, "__call__")
    def __call__(self):
        """Renders the composite.
        """
        if self._v_rendering:
            raise CompositeError("Circular composite reference")
        self._v_rendering = 1
        try:
            template = self.getTemplate()
            return template(composite=self)
        finally:
            self._v_rendering = 0

    view = __call__

    index_html = None

    security.declareProtected(change_composites_perm, "design")
    def design(self, ui=None):
        """Renders the composite with editing features.
        """
        # Never cache a design view.
        req = getattr(self, "REQUEST", None)
        if req is not None:
            req["RESPONSE"].setHeader("Cache-Control", "no-cache")
        ui_obj = self.getUI(ui)
        self._v_editing = 1
        try:
            return ui_obj.render(self)
        finally:
            self._v_editing = 0

    security.declareProtected(change_composites_perm, "manage_designForm")
    def manage_designForm(self):
        """Renders the composite with editing and ZMI features.
        """
        return self.design("zmi")

    security.declareProtected(change_composites_perm, "getUI")
    def getUI(self, ui=None):
        """Returns a UI object.
        """
        if not ui:
            ui = self.default_ui
        tool = aq_get(self, "composite_tool", None, 1)
        if tool is None:
            raise CompositeError("No composite_tool found")
        return guarded_getattr(tool.uis, ui)

    def _usingSlot(self, name, class_name, title):
        """Receives notification that the template is using a slot.

        Even though slots are persisted, only the template knows
        exactly what slots are in use.  This callback gives the
        composite a chance to learn about the slots in use.  This is
        designed for editing purposes, not rendering.
        """
        if self._v_slot_specs is not None:
            # Record the slot spec.
            self._v_slot_specs.append({
                'name': name,
                'class_name': class_name,
                'title': title,
                })

    security.declareProtected(change_composites_perm, "getSlotSpecs")
    def getSlotSpecs(self):
        """Returns the slot specs within the template.

        Returns [{'name', 'class_name', 'title'}].  May return duplicates.
        """
        self._v_editing = 1
        self._v_slot_specs = []
        try:
            self()
            slots = self._v_slot_specs
            return slots
        finally:
            self._v_editing = 0
            self._v_slot_specs = None

    security.declareProtected(change_composites_perm, "getSlotClassName")
    def getSlotClassName(self, slot_name):
        """Returns the class_name of a slot.

        Returns None if no class is defined for the slot.  Raises
        KeyError if no such slot exists.
        """
        specs = self.getSlotSpecs()
        for spec in specs:
            if spec['name'] == slot_name:
                return spec['class_name']
        raise KeyError(slot_name)

    security.declareProtected(change_composites_perm, "getManifest")
    def getManifest(self):
        """Returns a manifest of slot contents.

        Designed for use by page templates that implement a manual
        slotting user interface.
        """
        contents = []  # [{name, slot_info}]
        seen = {}
        specs = self.getSlotSpecs()
        if hasattr(self, 'portal_url'):
            icon_base_url = self.portal_url()
        else:
            request = getattr(self, 'REQUEST', None)
            if request is not None:
                icon_base_url = request['BASEPATH1']
            else:
                icon_base_url = ''
        for spec in specs:
            name = spec['name']
            if seen.has_key(name):
                # Don't show duplicate uses of a slot.
                continue
            seen[name] = 1
            slot = self.slots[name]
            elements = []
            index = 0
            slot_values = slot.objectValues()
            for element in slot_values:
                error = None
                template = None
                templates = ()
                try:
                    ob = element.dereference()
                    template = element.queryInlineTemplate(spec['class_name'])
                    templates = element.listAllowableInlineTemplates(
                        spec['class_name'])
                except:
                    error = formatException(self, editing=1)
                    ob = FailedElement().__of__(self)
                icon = getIconURL(ob, icon_base_url)
                available_templates = []
                for name, t in templates:
                    if hasattr(aq_base(t), 'title_or_id'):
                        title = t.title_or_id()
                    else:
                        title = name
                    available_templates.append({'id': name, 'title': title})
                element_info = {
                    'title': ob.title_or_id(),
                    'icon': icon,
                    'error': error,
                    'source_path': '/'.join(element.getPhysicalPath()),
                    'index': index,
                    'next_index': index + 1,
                    'can_move_up': (index > 0),
                    'can_move_down': (index < len(slot_values) - 1),
                    'template': template,
                    'available_templates': available_templates,
                    }
                elements.append(element_info)
                index += 1
            slot_info = {
                'name': name,
                'title': spec['title'] or name,
                'class_name': spec['class_name'],
                'target_path': '/'.join(slot.getPhysicalPath()),
                'elements': elements,
                }
            contents.append(slot_info)
        return contents

    security.declareProtected(view_perm, "isEditing")
    def isEditing(self):
        """Returns true if currently rendering in design mode.
        """
        return self._v_editing

Globals.InitializeClass(CompositeMixin)


class SlotCollection(Folder):
    """Stored collection of composite slots.
    """
    meta_type = "Slot Collection"

    def all_meta_types(self):
        return Folder.all_meta_types(self, interfaces=(ISlot,))


class Composite(CompositeMixin, Folder):
    """An HTML fragment composed from a template and fragments.

    Fragments are stored on a container called 'filled_slots'.
    """

    manage_options = (
        Folder.manage_options[:1]
        + CompositeMixin.manage_options
        + Folder.manage_options[2:]
        )

    _properties = Folder._properties + CompositeMixin._properties

    def __init__(self):
        f = SlotCollection()
        f._setId("filled_slots")
        self._setObject(f.getId(), f)

Globals.InitializeClass(Composite)


class FailedElement(SimpleItem):
    meta_type = "Failed Element"
    icon = 'p_/broken'
    id = 'error'
    title = 'Error'


addCompositeForm = PageTemplateFile("addCompositeForm.zpt", _www)

def manage_addComposite(dispatcher, id, title="", create_sample="",
                        REQUEST=None):
    """Adds a composite to a folder.
    """
    ob = Composite()
    ob._setId(id)
    ob.title = unicode(title)
    dispatcher._setObject(ob.getId(), ob)
    if create_sample:
        ob = dispatcher.this()._getOb(ob.getId())
        f = open(os.path.join(_www, 'sample_template.zpt'), "rt")
        try:
            text = f.read()
        finally:
            f.close()
        pt = ZopePageTemplate(
            id="template", text=text, content_type="text/html")
        ob._setObject(pt.getId(), pt)
    if REQUEST is not None:
        return dispatcher.manage_main(dispatcher, REQUEST)
