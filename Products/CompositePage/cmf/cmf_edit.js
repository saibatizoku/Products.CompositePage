
// CMF-specific editing scripts.  Referenced by cmf/bottom.pt.
// The variable "ui_url" is provided by common/header.pt.

function cmf_edit(element) {
  var path = escape(element.getAttribute("source_path"));
  window.top.document.location = ui_url + "/showElement?path=" + path;
}

function cmf_add(target) {
  // Note that target_index is also available.
  var path = escape(target.getAttribute("target_path"));
  window.top.document.location = ui_url + "/showSlot?path=" + path;
}
