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
"""Composite tool tests.

$Id: test_tool.py,v 1.4 2004/05/03 16:02:40 sidnei Exp $
"""

import unittest

from OFS.Folder import Folder
from AccessControl.SecurityManagement import noSecurityManager
from AccessControl.SecurityManager import setSecurityPolicy
import AccessControl.User  # Get the "nobody" user defined

from Products.CompositePage.tool import CompositeTool
from Products.CompositePage.slot import Slot
from Products.CompositePage.interfaces import CompositeError


class PermissiveSecurityPolicy:
    def validate(*args, **kw):
        return 1

    def checkPermission(*args, **kw):
        return 1


class ToolTests(unittest.TestCase):

    def setUp(self):
        self.root = Folder()
        self.root.getPhysicalPath = lambda: ()
        self.root.getPhysicalRoot = lambda r=self.root: r
        self.root.composite_tool = CompositeTool()
        self.tool = self.root.composite_tool
        self.tool._check_security = 0
        self.root.slot = Slot("slot")
        self.slot = self.root.slot
        f = Folder()
        f._setId("f")
        self.slot._setObject(f.id, f)
        g = Folder()
        g._setId("g")
        self.slot._setObject(g.id, g)
        self.root.otherslot = Slot("otherslot")
        self.old_policy = setSecurityPolicy(PermissiveSecurityPolicy())
        noSecurityManager()

    def tearDown(self):
        setSecurityPolicy(self.old_policy)
        noSecurityManager()

    def testPreventParentageLoop(self):
        self.assertRaises(CompositeError, self.tool.moveElements,
                          ["/slot/foo"], "/slot/foo/zzz", 0)
        self.assertRaises(CompositeError, self.tool.moveElements,
                          ["/foo/bar"], "/foo/bar/baz/zip", 0)

    def testDelete(self):
        self.assertEqual(list(self.slot.objectIds()), ["f", "g"])
        self.tool.deleteElements(["/slot/g"])
        self.assertEqual(list(self.slot.objectIds()), ["f"])

    def testMoveWithinSlot(self):
        self.assertEqual(list(self.slot.objectIds()), ["f", "g"])
        self.tool.moveElements(["/slot/g"], "/slot", 0)
        self.assertEqual(list(self.slot.objectIds()), ["g", "f"])
        self.tool.moveElements(["/slot/g"], "/slot", 2)
        self.assertEqual(list(self.slot.objectIds()), ["f", "g"])
        self.tool.moveElements(["/slot/g"], "/slot", 1)
        self.assertEqual(list(self.slot.objectIds()), ["f", "g"])

    def testMoveToOtherSlot(self):
        self.assertEqual(list(self.slot.objectIds()), ["f", "g"])
        self.tool.moveElements(["/slot/f"], "/otherslot", 0)
        self.assertEqual(list(self.slot.objectIds()), ["g"])
        self.assertEqual(list(self.root.otherslot.objectIds()), ["f"])
        self.tool.moveElements(["/slot/g"], "/otherslot", 0)
        self.assertEqual(list(self.slot.objectIds()), [])
        self.assertEqual(list(self.root.otherslot.objectIds()), ["g", "f"])
        self.tool.moveElements(["/otherslot/f", "/otherslot/g"], "/slot", 0)
        # The new order is deterministic because of sorting in moveElements().
        self.assertEqual(list(self.slot.objectIds()), ["f", "g"])
        self.assertEqual(list(self.root.otherslot.objectIds()), [])

    def testMoveAndDelete(self):
        self.assertEqual(list(self.slot.objectIds()), ["f", "g"])
        self.assertEqual(list(self.root.otherslot.objectIds()), [])
        self.tool.moveAndDelete(move_source_paths="/slot/f:/slot/g",
                                move_target_path="/otherslot",
                                move_target_index="2")
        self.assertEqual(list(self.slot.objectIds()), [])
        self.assertEqual(list(self.root.otherslot.objectIds()), ["f", "g"])
        self.tool.moveAndDelete(
            delete_source_paths="/otherslot/f:/otherslot/g")
        self.assertEqual(list(self.slot.objectIds()), [])
        self.assertEqual(list(self.root.otherslot.objectIds()), [])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ToolTests))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

