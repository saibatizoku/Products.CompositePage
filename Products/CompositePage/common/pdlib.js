// Copyright (c) 2002 Zope Foundation and Contributors.
// All Rights Reserved.
//
// This software is subject to the provisions of the Zope Public License,
// Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
// THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
// WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
// WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
// FOR A PARTICULAR PURPOSE.

// Page design Javascript library

// A library for manipulating objects on a page with object selection,
// context menus, and drag and drop.  Mostly DOM 2 oriented, with bits
// for IE compatibility.
// $Id: pdlib.js,v 1.6 2004/05/21 08:59:35 gotcha Exp $

// The following variables and functions are documented for use by
// scripts that use this library:
//
//   pd_node_setup
//   pd_selected_item
//   pd_selected_items
//   pd_library_version
//   pd_filter_object
//
//   pd_stopEvent()
//   pd_findEventTarget()
//   pd_hideContextMenu()
//   pd_isSelected()
//   pd_select()
//   pd_deselect()
//   pd_clearSelection()
//   pd_setupContextMenu()     -- adds a context menu to an element
//   pd_setupDragUI()          -- adds drag/drop functionality to an element
//   pd_setupDropTarget()      -- turns an element into a drop target
//   pd_setupContextMenuDefinition() -- turns an element into a context menu
//   pd_setupPage()            -- Page initialization (call at bottom of page)
//
// See the documentation for descriptions.
// All other names are subject to change in future revisions.

var pd_library_version = '0.3';  // The pdlib version. Avoid depending on this!
var pd_open_context_menu = null; // The context menu node being displayed
var pd_drag_event = null;        // A pd_DragEvent object while dragging
var pd_selected_items = null;    // List of selected items
var pd_selected_item = null;     // Non-null when exactly one item is selected
var pd_drag_select_mode = null;  // -1 or 1 in drag-select mode, otherwise null
var pd_node_setup = {};          // Object containing node setup functions
var pd_max_contextmenu_width = 250; // Threshold for faulty browsers
var pd_invisible_targets = [];   // A list of normally invisible drop targets
var pd_filter_object = null;  // The object being filtered


function pd_hasAncestor(node, ancestor) {
  var p = node;
  while (p) {
    if (p == ancestor)
      return true;
    p = p.parentNode;
  }
  return false;
}

function pd_stopEvent(e) {
  if (!e)
    e = event;
  if (e.stopPropagation)
    e.stopPropagation();
  else
    e.cancelBubble = true;
  return false;
}

function pd_findEventTarget(e, className, stop_className) {
  // Search for a node of the given class among the ancestors of the
  // target of an event, stopping if stop_className is encountered.
  // Note that elements with multiple classes are not supported by
  // this function.
  var node = e.target || e.srcElement;
  while (node) {
    if (node.className == className)
      return node;
    if (stop_className && node.className == stop_className)
      return null;
    node = node.parentNode;
  }
  // Not found.
  return null;
}

function pd_highlight(node, state) {
  var cn = node.className;
  if (state) {
    if (cn.length < 12 || cn.substr(cn.length - 12) != "_highlighted")
      node.className = cn + "_highlighted";
  }
  else {
    if (cn.length >= 12 && cn.substr(cn.length - 12) == "_highlighted")
      node.className = cn.substr(0, cn.length - 12);
  }
}

//
// Context menu functions
//

function pd_showContextMenu(menunode, e) {
  if (!e)
    e = event;
  // Close any open menu
  pd_hideContextMenu();
  var page_w = window.innerWidth || document.body.clientWidth;
  var page_h = window.innerHeight || document.body.clientHeight;
  // have to check documentElement in some IE6 releases
  var page_x = window.pageXOffset || document.documentElement.scrollLeft || document.body.scrollLeft;
  var page_y = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop;

  if (menunode.offsetWidth >= pd_max_contextmenu_width) {
    // It's likely that the browser ignored "display: table"
    // and used the full width of the page.  Use a workaround.
    menunode.style.width = '' + (pd_max_contextmenu_width) + 'px';
  }

  // Choose a location for the menu based on where the user clicked
  if (page_w - e.clientX < menunode.offsetWidth) {
    // Close to the right edge
    menunode.style.left = '' + (
      page_x + e.clientX - menunode.offsetWidth - 1) + 'px';
  }
  else {
    menunode.style.left = '' + (page_x + e.clientX + 1) + 'px';
  }
  if (page_h - e.clientY < menunode.offsetHeight) {
    // Close to the bottom
    menunode.style.top = '' + (
      page_y + e.clientY - menunode.offsetHeight - 1) + 'px';
  }
  else {
    menunode.style.top = '' + (page_y + e.clientY + 1) + 'px';
  }

  pd_open_context_menu = menunode;
  menunode.style.visibility = "visible";
  return false;
}

function pd_hideContextMenu() {
  if (pd_open_context_menu) {
    pd_open_context_menu.style.visibility = "hidden";
    pd_open_context_menu = null;
  }
}

function pd_filterContextMenuItems(node) {
  // Execute filter scripts and set the "display" style property
  var i, f, enabled;
  if (node.getAttribute) {
    f = node.getAttribute("filter");
    if (f) {
      pd_filter_object = node;
      enabled = eval(f);
      if (!enabled)
        node.style.display = "none";
      else if (node.style.display == "none")
        node.style.display = "";
    }
  }
  for (i = 0; i < node.childNodes.length; i++)
    pd_filterContextMenuItems(node.childNodes[i]);
}

//
// Drag functions
//

function pd_DragEvent(e, move_func, checkmove_func) {
  this.target = null;
  this.move_func = move_func;
  this.checkmove_func = checkmove_func;
  this.start_x = e.pageX ? e.pageX : e.clientX + document.body.scrollLeft;
  this.start_y = e.pageY ? e.pageY : e.clientY + document.body.scrollTop;
  this.feedback_node = document.getElementById("drag-feedback-box");
  this.began_moving = false;
  this.revealed = [];
}

function pd_allowDrop(target) {
  if (!pd_drag_event)
    return false;
  var i;
  for (i = 0; i < pd_selected_items.length; i++) {
    if (pd_hasAncestor(target, pd_selected_items[i])) {
      // Don't let the user drag an element inside itself.
      return false;
    }
  }
  if (pd_drag_event.checkmove_func) {
    if (!pd_drag_event.checkmove_func(pd_selected_items, target))
      return false;
  }
  return true;
}

function pd_unhighlightTarget() {
  if (pd_drag_event && pd_drag_event.target) {
    pd_highlight(pd_drag_event.target, "");
    pd_drag_event.target = null;
  }
}

function pd_setHighlightedTarget(target) {
  if (pd_allowDrop(target)) {
    pd_unhighlightTarget();
    pd_highlight(target, "target");
    pd_drag_event.target = target;
  }
}

function pd_firstDrag(x, y) {
  if (!pd_drag_event)
    return;
  var i, target;
  var feedback_node_style = pd_drag_event.feedback_node.style;
  var item = pd_selected_items[0];  // TODO: expand box to include all items

  pd_drag_event.began_moving = true;
  feedback_node_style.left = '' + (x + 5) + 'px';
  feedback_node_style.top = '' + (y + 5) + 'px';
  feedback_node_style.width = '' + (item.offsetWidth - 2) + 'px';
  feedback_node_style.height = '' + (item.offsetHeight - 2) + 'px';
  feedback_node_style.display = "block";

  // Show some of the normally invisible targets.
  for (i = 0; i < pd_invisible_targets.length; i++) {
    target = pd_invisible_targets[i];
    if (pd_allowDrop(target)) {
      if (pd_drag_event.revealed.push)
        pd_drag_event.revealed.push(target);
      else
        pd_drag_event.revealed = pd_drag_event.revealed.concat([target]);
      target.style.visibility = "visible";
    }
  }
}

function pd_dragging(e) {
  if (!pd_drag_event)
    return;
  if (!e)
    e = event;
  var x = e.pageX ? e.pageX : e.clientX + document.body.scrollLeft;
  var y = e.pageY ? e.pageY : e.clientY + document.body.scrollTop;

  if (!pd_drag_event.began_moving) {
    if (Math.abs(x - pd_drag_event.start_x) <= 3 &&
        Math.abs(y - pd_drag_event.start_y) <= 3) {
      // Didn't move far enough yet.
      return;
    }
    pd_firstDrag(x, y);
  }
  pd_drag_event.feedback_node.style.left = '' + (x + 5) + 'px';
  pd_drag_event.feedback_node.style.top = '' + (y + 5) + 'px';
}

function pd_finishDrag() {
  var i;
  for (i = 0; i < pd_drag_event.revealed.length; i++)
    pd_drag_event.revealed[i].style.visibility = '';

  document.onmousemove = null;
  document.onmouseup = null;
  document.onselectstart = null;
  pd_drag_event.feedback_node.style.display = "none";
  var ev = pd_drag_event;
  pd_drag_event = null;

  if (ev.target) {
    pd_highlight(ev.target, "wait");
    if (ev.move_func)
      ev.move_func(pd_selected_items, ev.target);
  }
}

function pd_startDrag(e, move_func, checkmove_func) {
  if (pd_drag_event) {
    // Already dragging
    return;
  }
  if (!e)
    e = event;
  pd_drag_event = new pd_DragEvent(e, move_func, checkmove_func);
  document.onmousemove = pd_dragging;
  document.onmouseup = pd_finishDrag;
  document.onselectstart = pd_stopEvent;  // IE: Don't start a selection.
  if (e.preventDefault)
    e.preventDefault();  // NS 6: Don't start a selection.
}

//
// Selection management functions
//

function pd_isSelected(node) {
  if (pd_selected_items) {
    for (var i = 0; i < pd_selected_items.length; i++) {
      if (node == pd_selected_items[i]) {
        return true;
      }
    }
  }
  return false;
}

function pd_changedSelection() {
  if (pd_selected_items && pd_selected_items.length == 1)
    pd_selected_item = pd_selected_items[0];
  else
    pd_selected_item = null;
}

function pd_deselect(node) {
  var i, n;
  if (pd_selected_items) {
    var newsel = [];
    // There must be a better way.  This could be slow.
    for (i = 0; i < pd_selected_items.length; i++) {
      n = pd_selected_items[i];
      if (n != node) {
        if (newsel.push)
          newsel.push(n)
        else
          newsel = newsel.concat([n]);
      }
    }
    pd_selected_items = newsel;
    pd_changedSelection();
  }
  pd_highlight(node, "");
}

function pd_select(node) {
  if (!pd_isSelected(node)) {
    if (!pd_selected_items)
      pd_selected_items = [node];
    else if (pd_selected_items.push)
      pd_selected_items.push(node);
    else
      pd_selected_items = pd_selected_items.concat([node]);
    pd_changedSelection();
  }
  pd_highlight(node, "selected");
}

function pd_clearSelection() {
  var i, node, n;
  if (pd_selected_items) {
    for (i = 0; i < pd_selected_items.length; i++)
      pd_highlight(pd_selected_items[i], "");
  }
  pd_selected_items = [];
  pd_changedSelection();
}

function pd_dragSelecting(node) {
  if (pd_drag_select_mode == 1)
    pd_select(node);
  else if (pd_drag_select_mode == -1)
    pd_deselect(node);
}

function pd_endDragSelect() {
  pd_drag_select_mode = null;
  document.onmouseup = null;
}

function pd_startDragSelect(v) {
  document.onmouseup = pd_endDragSelect;
  pd_drag_select_mode = v;
}


//
// On-page object management functions
//

function pd_itemOnMousedown(mo, e, move_func, checkmove_func, box) {
  if (!e)
    e = event;
  var target = e.target || e.srcElement;
  if (target.nodeName) {
    var name = target.nodeName.toLowerCase();
    if (name == "input" || name == "select" || name == "a") {
      // Allow interaction with the widget or link.
      return true;
    }
  }
  if (e.button == 0 || e.button == 1) {
    pd_hideContextMenu();
    if (!box)
      box = mo;
    if (e.shiftKey) {
      // Toggle the selected state of this item and start drag select.
      if (pd_isSelected(box)) {
        pd_deselect(box);
        pd_startDragSelect(-1);
      }
      else {
        pd_select(box);
        pd_startDragSelect(1);
      }
    }
    else if (e.ctrlKey) {
      if (pd_isSelected(box))
        pd_deselect(box);
      else
        pd_select(box);
    }
    else {
      if (!pd_isSelected(box)) {
        pd_clearSelection();
        pd_select(box);
      }
      pd_startDrag(e, move_func, checkmove_func);
    }
  }
  return pd_stopEvent(e);
}

function pd_itemOnMouseover(mo, e, box) {
  if (pd_drag_select_mode) {
    pd_dragSelecting(box || mo);
    return pd_stopEvent(e);
  }
}

function pd_itemOnContextMenu(mo, e, contextMenuId, box) {
  if (!e)
    e = event;
  if (!box)
    box = mo;
  if (!pd_isSelected(box)) {
    pd_clearSelection();
    pd_select(box);
  }
  var menu = document.getElementById(contextMenuId);
  if (menu) {
    pd_filterContextMenuItems(menu);
    pd_showContextMenu(menu, e);
    return pd_stopEvent(e);
  }
}

function pd_ie_ondragstart() {
  event.dataTransfer.effectAllowed = "move";
}

function pd_ie_ondragend() {
  if (pd_drag_event) {
    pd_drag_event.target = null;
    pd_finishDrag();
  }
}

function pd_setupDragUI(mo, move_func, checkmove_func, box) {
  // Adds selection and drag and drop functionality to an element
  mo.onmousedown = function(e) {
    return pd_itemOnMousedown(mo, e, move_func, checkmove_func, box);
  };
  mo.onmouseover = function(e) {
    return pd_itemOnMouseover(mo, e, box);
  };
  mo.onselectstart = pd_stopEvent;  // IE: Don't start a selection.
  // IE: drag and drop
  mo.ondragstart = pd_ie_ondragstart;
  mo.ondrag = pd_dragging;
  mo.ondragend = pd_ie_ondragend;
}

function pd_setupContextMenu(mo, contextMenuId, box, onclick) {
  // Adds context menu functionality to an element
  mo.oncontextmenu = function(e) {
    return pd_itemOnContextMenu(mo, e, contextMenuId, box);
  };
  if (onclick)
    mo.onclick = mo.oncontextmenu;
}

function pd_documentOnMouseDown() {
  pd_hideContextMenu();
  pd_clearSelection();
}

function pd_setupNodeAndDescendants(node) {
  var i, f, names;
  if (node.className) {
    names = node.className.split(" ");
    for (i = 0; i < names.length; i++) {
      if (names[i]) {
        f = pd_node_setup[names[i]];
        if (f)
          f(node);
      }
    }
  }
  for (i = 0; i < node.childNodes.length; i++) {
    pd_setupNodeAndDescendants(node.childNodes[i]);
  }
}

function pd_setupPage(node) {
  if (!node)
    node = document;
  if (!document.onmousedown)
    document.onmousedown = pd_documentOnMouseDown;
  pd_setupNodeAndDescendants(node);
}

function pd_ie_ondrag() {
  event.returnValue = false;
  event.dataTransfer.dropEffect = "move";
}

function pd_setupDropTarget(node, selectable) {
  node.onmouseover = function() {
    return pd_setHighlightedTarget(node);
  };
  node.onmouseout = pd_unhighlightTarget;
  if (!selectable)
    node.onmousedown = pd_stopEvent; // Prevent accidental selection
  // IE: drag and drop
  node.ondrop = function() {
    pd_setHighlightedTarget(node);
    pd_finishDrag();
  };
  node.ondragenter = pd_ie_ondrag;
  node.ondragover = pd_ie_ondrag;
}

function pd_setupContextMenuDefinition(node) {
  node.onmousedown = pd_stopEvent;
  node.onmouseup = pd_hideContextMenu;
}

function pd_setupContextMenuItem(node) {
  node.onmouseover = function() {
    pd_highlight(node, "hover");
  };
  node.onmouseout = function() {
    pd_highlight(node, "");
  };
}

pd_node_setup['drop-target'] = pd_setupDropTarget;
pd_node_setup['context-menu'] = pd_setupContextMenuDefinition;
pd_node_setup['context-menu-item'] = pd_setupContextMenuItem;
