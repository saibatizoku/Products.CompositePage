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
"""Page design UI classes.

$Id: designuis.py,v 1.10 2004/04/06 16:50:25 shane Exp $
"""

import os
import re

import Globals
from Acquisition import aq_base, aq_inner, aq_parent
from OFS.SimpleItem import SimpleItem
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from AccessControl import ClassSecurityInfo
from AccessControl.ZopeGuards import guarded_getattr

from Products.CompositePage.rawfile import RawFile
from Products.CompositePage.rawfile import InterpolatedFile
from Products.CompositePage.interfaces import ICompositeElement


_common = os.path.join(os.path.dirname(__file__), "common")
_zmi = os.path.join(os.path.dirname(__file__), "zmi")
_cmf = os.path.join(os.path.dirname(__file__), "cmf")
_manual = os.path.join(os.path.dirname(__file__), "manual")

start_of_head_search = re.compile("(<head[^>]*>)", re.IGNORECASE).search
start_of_body_search = re.compile("(<body[^>]*>)", re.IGNORECASE).search
end_of_body_search = re.compile("(</body[^>]*>)", re.IGNORECASE).search

default_html_page = """<html>
<head>
<title>Composite Page</title>
</head>
<body>
%s
</body>
</html>
"""

close_dialog_html = '''<html>
<script type="text/javascript">
if (window.opener)
  window.opener.location.reload();
window.close();
</script>
</html>
'''

class CommonUI(SimpleItem):
    """Basic page design UI.

    Adds editing features to a rendered composite.
    """

    security = ClassSecurityInfo()

    security.declarePublic(
        "pdlib_js", "design_js", "pdstyles_css", "designstyles_css")
    pdlib_js = RawFile("pdlib.js", "text/javascript", _common)
    edit_js = RawFile("edit.js", "text/javascript", _common)
    pdstyles_css = RawFile("pdstyles.css", "text/css", _common)
    editstyles_css = InterpolatedFile("editstyles.css", "text/css", _common)
    target_image = RawFile("target.gif", "image/gif", _common)
    target_image_hover = RawFile("target_hover.gif", "image/gif", _common)
    target_image_active = RawFile("target_active.gif", "image/gif", _common)
    element_image = RawFile("element.gif", "image/gif", _common)

    header_templates = (PageTemplateFile("header.pt", _common),)
    top_templates = ()
    bottom_templates = (PageTemplateFile("bottom.pt", _common),)

    changeTemplateForm = PageTemplateFile("changeTemplateForm.pt", _common)

    workspace_view_name = "view"  # To be overridden

    security.declarePublic("getFragments")
    def getFragments(self, composite):
        """Returns the fragments to be inserted in design mode.
        """
        params = {
            "tool": aq_parent(aq_inner(aq_parent(aq_inner(self)))),
            "ui": self,
            "composite": composite,
            }
        header = ""
        top = ""
        bottom = ""
        for t in self.header_templates:
            header += t.__of__(self)(**params)
        for t in self.top_templates:
            top += t.__of__(self)(**params)
        for t in self.bottom_templates:
            bottom += t.__of__(self)(**params)
        return {"header": header, "top": top, "bottom": bottom}


    security.declarePrivate("render")
    def render(self, composite):
        """Renders a composite, adding scripts and styles.
        """
        text = composite()
        fragments = self.getFragments(composite)
        match = start_of_head_search(text)
        if match is None:
            # Turn it into a page.
            text = default_html_page % text
            match = start_of_head_search(text)
            if match is None:
                raise CompositeError("Could not find header")
        if fragments['header']:
            index = match.end(0)
            text = "%s%s%s" % (text[:index], fragments['header'], text[index:])
        if fragments['top']:
            match = start_of_body_search(text)
            if match is None:
                raise CompositeError("No 'body' tag found")
            index = match.end(0)
            text = "%s%s%s" % (text[:index], fragments['top'], text[index:])
        if fragments['bottom']:
            match = end_of_body_search(text)
            if match is None:
                raise CompositeError("No 'body' end tag found")
            m = match
            while m is not None:
                # Find the *last* occurrence of "</body>".
                match = m
                m = end_of_body_search(text, match.end(0))
            index = match.start(0)
            text = "%s%s%s" % (text[:index], fragments['bottom'], text[index:])
        return text


    security.declarePublic("showElement")
    def showElement(self, path, RESPONSE):
        """Redirects to the workspace for an element.
        """
        root = self.getPhysicalRoot()
        obj = root.restrictedTraverse(path)
        if ICompositeElement.providedBy(obj):
            obj = obj.dereference()
        RESPONSE.redirect("%s/%s" % (
            obj.absolute_url(), self.workspace_view_name))


    security.declarePublic("previewElement")
    def previewElement(self, path, RESPONSE):
        """Redirects to the preview for an element.
        """
        root = self.getPhysicalRoot()
        obj = root.restrictedTraverse(path)
        if ICompositeElement.providedBy(obj):
            obj = obj.dereference()
        RESPONSE.redirect(obj.absolute_url())


    security.declarePublic("showSlot")
    def showSlot(self, path, RESPONSE):
        """Redirects to (and possibly creates) the workspace for a slot.
        """
        from composite import Composite

        obj = self.getPhysicalRoot()
        parts = str(path).split('/')
        for name in parts:
            obj = obj.restrictedTraverse(name)
            if IComposite.providedBy(obj):
                gen = guarded_getattr(obj, "generateSlots")
                gen()
        RESPONSE.redirect("%s/%s" % (
            obj.absolute_url(), self.workspace_view_name))


    security.declarePublic("getTemplateChangeInfo")
    def getTemplateChangeInfo(self, paths):
        """Returns information for changing the template applied to objects.
        """
        root = self.getPhysicalRoot()
        tool = aq_parent(aq_inner(self))
        obs = []
        all_choices = None  # {template -> 1}
        current = None
        for path in str(paths).split(':'):
            ob = root.unrestrictedTraverse(path)
            obs.append(ob)
            if not ICompositeElement.providedBy(ob):
                raise ValueError("Not a composite element: %s" % path)
            m = guarded_getattr(ob, "queryInlineTemplate")
            template = m()
            if current is None:
                current = template
            elif current and current != template:
                # The current template isn't the same for all of the elements,
                # so there is no common current template.  Spell this condition
                # using a non-string value.
                current = 0
            m = guarded_getattr(ob, "listAllowableInlineTemplates")
            templates = m()
            d = {}
            for name, template in templates:
                d[name] = template
            if all_choices is None:
                all_choices = d
            else:
                for template in all_choices.keys():
                    if not d.has_key(template):
                        del all_choices[template]
        return {
            "obs": obs,
            "templates": all_choices,
            "current_template": current,
            }


    security.declarePublic("changeTemplate")
    def changeTemplate(self, paths, template, reload=0, close=1, REQUEST=None):
        """Changes the template for objects.
        """
        info = self.getTemplateChangeInfo(paths)
        if template not in info["templates"]:
            raise KeyError("Template %s is not among the choices" % template)
        tool = aq_parent(aq_inner(self))
        for ob in info["obs"]:
            assert ICompositeElement.providedBy(ob)
            m = guarded_getattr(ob, "setInlineTemplate")
            m(template)
        if REQUEST is not None:
            if reload:
                REQUEST["RESPONSE"].redirect(REQUEST["HTTP_REFERER"])
            elif close:
                return close_dialog_html

Globals.InitializeClass(CommonUI)



class ZMIUI (CommonUI):
    """Page design UI meant to fit the Zope management interface.

    Adds editing features to a rendered composite.
    """
    security = ClassSecurityInfo()

    workspace_view_name = "manage_workspace"

    security.declarePublic("zmi_edit_js")
    zmi_edit_js = RawFile("zmi_edit.js", "text/javascript", _zmi)

    header_templates = CommonUI.header_templates + (
        PageTemplateFile("header.pt", _zmi),)
    top_templates = CommonUI.top_templates + (
        PageTemplateFile("top.pt", _zmi),)
    bottom_templates = (PageTemplateFile("bottom.pt", _zmi),
                        ) + CommonUI.bottom_templates

Globals.InitializeClass(ZMIUI)



class CMFUI (CommonUI):
    """Page design UI meant to fit CMF.

    Adds CMF-specific scripts and styles to a page.
    """
    security = ClassSecurityInfo()

    workspace_view_name = "view"

    security.declarePublic("cmf_edit_js")
    cmf_edit_js = RawFile("cmf_edit.js", "text/javascript", _cmf)

    header_templates = CommonUI.header_templates + (
        PageTemplateFile("header.pt", _cmf),)
    bottom_templates = (PageTemplateFile("bottom.pt", _cmf),
                        ) + CommonUI.bottom_templates

Globals.InitializeClass(CMFUI)



class ManualUI (CommonUI):
    """Non-WYSIWYG page design UI.
    """
    security = ClassSecurityInfo()

    body = PageTemplateFile("body.pt", _manual)
    manual_styles_css = InterpolatedFile(
        "manual_styles.css", "text/css", _manual)
    header_templates = (PageTemplateFile("header.pt", _manual),)
    bottom_templates = CommonUI.bottom_templates + (
        PageTemplateFile("bottom.pt", _manual),)
    manual_js = RawFile("manual.js", "text/javascript", _manual)
    add_icon = RawFile("add.gif", "image/gif", _manual)
    add_rollover = RawFile("add_rollover.gif", "image/gif", _manual)
    remove_icon = RawFile("remove.gif", "image/gif", _manual)
    remove_rollover = RawFile("remove_rollover.gif", "image/gif", _manual)
    cut_icon = RawFile("cut.gif", "image/gif", _manual)
    cut_rollover = RawFile("cut_rollover.gif", "image/gif", _manual)
    copy_icon = RawFile("copy.gif", "image/gif", _manual)
    copy_rollover = RawFile("copy_rollover.gif", "image/gif", _manual)
    paste_icon = RawFile("paste.gif", "image/gif", _manual)
    paste_rollover = RawFile("paste_rollover.gif", "image/gif", _manual)

    security.declarePublic("renderBody")
    def renderBody(self, composite):
        """Renders the slotting interface for a composite.

        Returns an HTML fragment without the required scripts and
        styles.
        """
        manifest = composite.getManifest()
        pt = self.body.__of__(composite)
        return pt(ui=self, manifest=manifest)

    security.declarePublic("render")
    def render(self, composite):
        """Renders a ZMI slotting interface for a composite.

        Returns a full HTML page with scripts and styles.
        """
        fragments = self.getFragments(composite)
        body = self.renderBody(composite)
        res = []
        res.append(composite.manage_page_header())
        res.append(composite.manage_tabs())
        res.append(fragments["header"])
        res.append(fragments["top"])
        res.append(body)
        res.append(fragments["bottom"])
        res.append(composite.manage_page_footer())
        return '\n'.join(res)

Globals.InitializeClass(ManualUI)
