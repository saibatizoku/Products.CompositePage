##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
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
"""Utilities for handling ZODB objects.

(Copied from the Ape product.)

$Id: utils.py,v 1.1 2003/12/28 04:32:47 shane Exp $
"""

from cStringIO import StringIO
from cPickle import Pickler, Unpickler


def copyOf(source):
    """Copies a ZODB object, loading subobjects as needed.

    Re-ghostifies objects along the way to save memory.
    """
    former_ghosts = []
    zclass_refs = {}

    def persistent_id(ob, former_ghosts=former_ghosts,
                      zclass_refs=zclass_refs):
        if getattr(ob, '_p_changed', 0) is None:
            # Load temporarily.
            former_ghosts.append(ob)
            ob._p_changed = 0
        if hasattr(ob, '__bases__'):
            m = getattr(ob, '__module__', None)
            if (m is not None
                and isinstance(m, basestring)
                and m.startswith('*')):
                n = getattr(ob, '__name__', None)
                if n is not None:
                    # Pickling a ZClass instance.  Store the reference to
                    # the ZClass class separately, so that the pickler
                    # and unpickler don't trip over the apparently
                    # missing module.
                    ref = (m, n)
                    zclass_refs[ref] = ob
                    return ref
        return None

    def persistent_load(ref, zclass_refs=zclass_refs):
        return zclass_refs[ref]

    stream = StringIO()
    p = Pickler(stream, 1)
    p.persistent_id = persistent_id
    p.dump(source)
    if former_ghosts:
        for g in former_ghosts:
            del g._p_changed
        del former_ghosts[:]
    stream.seek(0)
    u = Unpickler(stream)
    u.persistent_load = persistent_load
    return u.load()

