// Copyright (c) 2002 Zope Foundation and Contributors.
// All Rights Reserved.
//
// This software is subject to the provisions of the Zope Public License,
// Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
// THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
// WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
// WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
// FOR A PARTICULAR PURPOSE.

// Composite editing scripts (based on PDLib)

function composite_getsources(selected_items) {
  var i, s, sources = "";
  for (i = 0; i < selected_items.length; i++) {
    s = selected_items[i].getAttribute("source_path");
    if (s) {
      if (sources)
        sources = sources + ":" + s;
      else
        sources = s;
    }
  }
  return sources;
}

function composite_move(selected_items, target_node) {
  var f, i, path, sources;
  f = document.forms.modify_composites;
  i = target_node.getAttribute("target_index");
  path = target_node.getAttribute("target_path");
  f.elements.move_target_index.value = i;
  f.elements.move_target_path.value = path;
  sources = composite_getsources(selected_items);
  f.elements.move_source_paths.value = sources;
  f.submit();
}

function composite_checkmove(selected_items, target_node) {
  var target_path, source_path, i;
  target_path = target_node.getAttribute("target_path");
  for (i = 0; i < selected_items.length; i++) {
    source_path = selected_items[i].getAttribute("source_path");
    if (source_path) {
      source_path = source_path + "/";  // Terminate on full names
      // window.status = "From " + source_path + " to " + dest_path;
      if (target_path.slice(0, source_path.length) == source_path) {
        // Don't allow a parent to become its own child.
        return false;
      }
    }
  }
  return true;
}

function composite_delete(selected_items) {
  var f, sources;
  if (!selected_items)
    return;
  f = document.forms.modify_composites;
  sources = composite_getsources(selected_items);
  f.elements.delete_source_paths.value = sources;
  f.submit();
}

function composite_change_template(elems) {
  var url, sources;
  sources = composite_getsources(elems);
  url = ui_url + "/changeTemplateForm?paths=" + sources;
  window.open(url, '', 'width=320, height=400, resizable, scrollbars, status');
}

function composite_copycut(selected_items, cut) {
  var f, sources;
  f = document.forms.useClipboard;
  sources = composite_getsources(selected_items);
  if (cut)
    f.elements.func.value = "cut";
  else
    f.elements.func.value = "copy";
  f.elements.source_paths.value = sources;
  f.submit();
}

function composite_paste(target_node) {
  var f, path, i;
  path = target_node.getAttribute("target_path");
  i = target_node.getAttribute("target_index");
  f = document.forms.useClipboard;
  f.elements.func.value = "paste";
  f.elements.target_path.value = path;
  f.elements.target_index.value = i;
  f.submit();
}

function composite_prepare_element_menu(header) {
  // Prepares the header of the element context menu.
  var node;
  if (!pd_selected_item) {
    icon = null;
    text = '' + pd_selected_items.length + ' Elements Selected';
  }
  else {
    icon = pd_selected_item.getAttribute('icon');
    text = pd_selected_item.getAttribute('title');
  }
  while (header.childNodes.length)
    header.removeChild(header.childNodes[0]);
  if (icon) {
    node = document.createElement("img");
    node.setAttribute("src", icon);
    node.setAttribute("width", "16");
    node.setAttribute("height", "16");
    header.appendChild(node);
  }
  node = document.createTextNode(text);
  header.appendChild(node);
  return true;
}

function composite_prepare_target_menu(header) {
  // Prepares the header of the target context menu.
  while (header.childNodes.length)
    header.removeChild(header.childNodes[0]);
  text = pd_selected_item.getAttribute('title') || 'Slot';
  node = document.createTextNode(text);
  header.appendChild(node);
  return true;
}


function setUpSlotTarget(node) {
  pd_setupDropTarget(node, 0);
  pd_setupContextMenu(node, 'slot-target-context-menu', null, true);
}

pd_node_setup['slot_target'] = setUpSlotTarget;


function setUpSlotElement(node) {
  var elem = document.getElementById('slot-element-grip');
  var icon = node.getAttribute('icon');
  if (elem) {
    elem = elem.cloneNode(true);
    if (icon)
      elem.src = icon;
    var iconShowed = node.getAttribute('iconShowed');
    if (!iconShowed) {
      node.insertBefore(elem, node.childNodes[0]);
      elem.style.display = 'inline';
      node.setAttribute('iconShowed', '1');
    }
  }
  pd_setupDragUI(node, composite_move, composite_checkmove);
  pd_setupContextMenu(node, 'slot-element-context-menu', null, true);
}

pd_node_setup['slot_element'] = setUpSlotElement;

