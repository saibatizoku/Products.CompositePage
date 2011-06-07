// Copyright (c) 2004 Zope Foundation and Contributors.
// All Rights Reserved.
//
// This software is subject to the provisions of the Zope Public License,
// Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
// THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
// WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
// WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
// FOR A PARTICULAR PURPOSE.

// Composite editing scripts (based on PDLib)

function setUpSlotTarget(node) {
  pd_setupDropTarget(node, 0);
}

pd_node_setup['slot_target'] = setUpSlotTarget;

function setUpSlotElement(node) {
  pd_setupDragUI(node, composite_move, composite_checkmove);
}

pd_node_setup['slot_element'] = setUpSlotElement;


function getSelectedElements() {
  var f = document.forms.manual_composite_ui;
  var p, e, i, res=[];
  for (i = 0; i < f.elements.length; i++) {
    e = f.elements[i];
    if (e.name == "source_paths:list" && e.checked) {
      res[res.length] = e;
    }
  }
  return res;
}

function findSourceNode(node) {
  while (node) {
    if (node.getAttribute("source_path"))
      return node;
    node = node.parentNode;
  }
}

function findTargetNode(node) {
  while (node) {
    if (node.getAttribute("target_path"))
      return node;
    node = node.parentNode;
  }
}

function manual_edit(element) {
  element = findSourceNode(element);
  var path = escape(element.getAttribute("source_path"));
  window.top.document.location = ui_url + "/showElement?path=" + path;
}

function manual_preview(element) {
  element = findSourceNode(element);
  var path = escape(element.getAttribute("source_path"));
  var url = ui_url + "/previewElement?path=" + path;
  window.open(url, '', 'width=640, height=480, resizable, scrollbars, status');
}

function manual_move(element) {
  var s = findSourceNode(element);
  var t = findTargetNode(element);
  composite_move([s], t);
}

function manual_add(target) {
  // Note that target_index is also available.
  target = findTargetNode(target);
  var path = target.getAttribute("target_path");
  var index = target.getAttribute("target_index");
  var url = ui_url + '/add_element_dialog?target_path=' + escape(path);
  if (index) {
    url = url + '&target_index=' + escape(index);
  }
  window.open(url, '', 'width=640, height=480, resizable, scrollbars, status');
}

function manual_delete() {
  var nodes = getSelectedElements();
  if (!nodes.length) {
    window.alert("To remove, select elements then click 'Remove'.");
    return;
  }
  composite_delete(nodes);
}

function manual_copy() {
  var nodes = getSelectedElements();
  if (!nodes.length) {
    window.alert("To copy, select elements then click 'Copy'.");
    return;
  }
  composite_copycut(nodes, false);
}

function manual_cut() {
  var nodes = getSelectedElements();
  if (!nodes.length) {
    window.alert("To cut, select elements then click 'Cut'.");
    return;
  }
  composite_copycut(nodes, true);
}

function manual_paste(target) {
  target = findTargetNode(target);
  composite_paste(target);
}

function manual_changeTemplate(node) {
  var f = document.forms.changeTemplate;
  var element = findSourceNode(node);
  f.elements.paths.value = element.getAttribute("source_path");
  f.elements.template.value = node.options[node.selectedIndex].value;
  f.submit();
}

function rollover(node) {
  var src = node.src;
  if (src && src.substr(src.length - 5) == "_icon")
    node.src = src.substr(0, src.length - 5) + "_rollover";
}

function rollout(node) {
  var src = node.src;
  if (src && src.substr(src.length - 9) == "_rollover")
    node.src = src.substr(0, src.length - 9) + "_icon";
}
