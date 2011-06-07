

Contents
========

- `Introduction`_
- `How to use CompositePage`_
- `How to write a template`_
- `How it works`_
- `Adapting CompositePage to other applications`_



Introduction
============

CompositePage is a way to assemble web pages from page fragments.
Through the use of Zope page templates, browser-based drag and drop, and
custom context menus, CompositePage makes it easy to visually combine
page fragments into complete pages.

CompositePage supercedes the PageDesign product and makes use of
PDLib, a Javascript library.  CompositePage is designed for browsers
that support the DOM (Document Object Model) and CSS (Cascading Style
Sheets) level 2: Firefox, Internet Explorer 5+, Opera, Konqueror, etc.



How to use CompositePage
========================

Follow these steps:

- Install the CompositePage product in Zope by unpacking the archive
  into your Products directory.  I've tested only with a current Zope
  checkout, which is something like Zope 2.7.

- Create a Composite Tool instance in a central location, possibly the
  root folder.

- Create a Composite object.  On the creation form, there is a
  checkbox for creating a sample template.  Leave the checkbox checked.

- Visit the Composite object and select the "Design" tab.  You should
  see a three-column layout with blue dotted lines in the places where
  you are allowed to insert content.

- Click just beneath one of the blue lines.  A context menu will pop
  up.  Select "Add...".

- You will be directed to a slot (a folderish object.)  In slots, you
  can add composite elements.  Add a composite element that points to a
  script.

- Find the composite created earlier and select the "Design" tab
  again.  Your new object should now show up in the slot.

- Move the object to a different slot using drag and drop.  When the
  mouse cursor is hovering over a permitted target (the blue dotted
  lines are targets), the target will be highlighted.  Let go and watch
  your object appear in the new place.

- Right-click over your object and select "Delete" from the context
  menu.


How to write a template
=======================

Templates can be any Zope object, but ZPTs (Zope Page Templates) are
the most common.  A template designed for use with composites uses the
'slots' attribute of the composite.  The 'slots' attribute is a
mapping-like object.

Here is a simple composite-aware page template::

  <html>
   <head>
   </head>
  <body>
   <div tal:content="structure here/slots/center/single">
   This will be replaced with one element from one slot.
   </div>
  </body>
  </html>

The expression 'here/slots/center/single' gets the 'slots' attribute
of the composite, finds a slot named 'center', and calls the single()
method of the slot, returning a string containing an HTML structure.

The only place you have to name a slot is in the template.  If the
template refers to a slot that does not yet exist, the composite will
create and return an empty slot.  If you place something in that slot
using the drag and drop interface, the composite will transparently
add a new slot to the 'filled_slots' folder.  Note that Zope prevents
you from storing slots with names that start with an underscore or
that clash existing folder attributes.

Templates use either the single() or the multiple() method of a slot.
single() returns a string, while multiple() returns a list of strings.
Use single() when you expect the slot to never contain more than one
element.  Use multiple() to allow more than one element.  In either
case, don't forget to use the ZPT 'structure' keyword, since the
returned strings contain HTML that should not be escaped.

``slot`` expressions
--------------------

You can also use the special ``slot`` expression type to define
slots in a template::

  <html>
   <head>
   </head>
  <body>
   <div tal:content="slot: center">
   This will be replaced with elements in the center slot.
   </div>
  </body>
  </html>

This syntax allows the template author to define slot titles
in addition to slot names.  The template author could write::

  <div tal:content="slot: center 'Page Center'">

The slot title will be shown to page designers.


How it works
============

Rendering
---------

When you render (view) a composite, it calls its template.  When the
template refers to a slot, the composite looks for the named slot in
the filled_slots folder.  If it finds the slot, it returns it; if it
doesn't find it, the composite creates a temporary empty slot.  Then
the template calls either the single() or multiple() method and the
slot renders and returns its contents.


Rendering in edit mode
----------------------

When requested, the composite calls upon a "UI" object to render its
template and slots with edit mode turned on.  In edit mode, slots add
'class', 'source_path', 'target_path', and 'target_index' attributes
to HTML tags to mark movable objects and available drop targets.
Slots add HTML markup for drop targets automatically.  When rendering
using the single() method, slots provide a drop target only if the
slot is empty.  When rendering using the multiple() method, slots
insert drop targets between the elements and to the beginning and end
of the slot.

The UI object can use various mechanisms to make the page editable.
Most UI objects use regular expressions to find the 'head' and 'body'
tags.  Then the UI object inserts scripts, styles, and HTML elements.
The result of the transformation is sent back to the browser.


Drag and drop
-------------

At the bottom of a page rendered in edit mode is a call to the
pd_setupPage() Javascript function.  pd_setupPage() searches all of
the elements on the page, looking for elements with particular 'class'
attributes.  When it finds a 'slot_element', a handler adds event
listeners to that element that react when the user presses the mouse
button in that element.  When pd_setupPage() finds a 'slot_target',
another handler adds event listeners that react when the user drags
into that element.

If the user releases the mouse while dragging into a target, the
Javascript code puts the appropriate source paths, target paths, and
target indexes into a hidden form and submits that form to the
composite tool in Zope.  The composite tool moves the elements then
redirects the browser to the original page.  The browser loads the
page in edit mode again and the moved element gets rendered in its new
spot.


Context menus
-------------

Like drag and drop, context menus depend on pd_setupPage().  When
pd_setupPage() finds a 'slot_element', a handler adds a context menu
listener to that element.  The context menu listener, when activated,
positions and displays an otherwise invisible HTML element that looks
just like a context menu.  Once displayed, the user is expected to
either select an item from the context menu or click outside the
context menu to make it disappear.  A similar process exists for
'slot_target' elements, but a different invisible HTML element is
used.

Just before popping up a context menu, its contents are filtered using
Javascript expressions.  Some actions are valid only when the user has
selected at least one item, and other actions are valid only when
exactly one item item is selected.  Filter expressions provide a way
to express these constraints.



Adapting CompositePage to other applications
============================================

CompositePage provides a default user interface that integrates with
the Zope management interface, but mechanisms are provided for
integrating with any user interface.  Look at design.py, the 'common'
subdirectory, and the 'zmi' subdirectory for guidance.  Simple
customizations probably do not require more code than the ZMI UI.
