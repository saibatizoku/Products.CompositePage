
// ZMI-specific editing scripts.  Referenced by zmi/bottom.pt.
// The variable "ui_url" is provided by common/header.pt.

function zmi_edit(element) {
  var path = escape(element.getAttribute("source_path"));
  document.location = ui_url + "/showElement?path=" + path;
}

function zmi_add(target) {
  // Note that target_index is also available, but the ZMI can't
  // make use of it easily.
  var path = escape(target.getAttribute("target_path"));
  document.location = ui_url + "/showSlot?path=" + path;
}
