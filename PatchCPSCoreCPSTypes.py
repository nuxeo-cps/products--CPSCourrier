"""temporary partial fix for http://svn.nuxeo.org/trac/pub/ticket/1554::

  - manage_CPSpasteObjects and friends do not send the right Z3 events

For CPSCourrier, we only need to fix the cut/paste events.
"""
from zope.event import notify
from zope.app.container.contained import ObjectMovedEvent
from zope.app.container.contained import notifyContainerModified

from Acquisition import aq_base, aq_inner, aq_parent
from OFS.event import ObjectWillBeRemovedEvent
from OFS import Moniker
from OFS.CopySupport import CopyError, _cb_decode, sanity_check
from Products.CPSCore.CPSTypes import TypeContainer
from Products.CMFCore.utils import getToolByName

if True:
    def manage_CPSpasteObjects(self, cp):
        """Paste objects (from an earlier copy).
        """
        wftool = getToolByName(self, 'portal_workflow')
        pxtool = getToolByName(self, 'portal_proxies')
        try:
            cp = _cb_decode(cp)
        except: # XXX
            raise CopyError, 'Invalid copy data.'

        # Verify pastable into self.
        ok, why = wftool.isBehaviorAllowedFor(self, 'paste', get_details=1)
        if not ok:
            raise CopyError, 'Paste not allowed, %s' % why

        op = cp[0]
        root = self.getPhysicalRoot()

        oblist = []
        containers = []
        behavior = (op == 0) and 'copy' or 'cut'
        for mdata in cp[1]:
            m = Moniker.loadMoniker(mdata)
            try:
                ob = m.bind(root)
            except: # XXX
                raise CopyError, 'Object not found'
            # Verify copy/cutable from source container.
            container = aq_parent(aq_inner(ob))
            if container not in containers:
                ok, why = wftool.isBehaviorAllowedFor(container, behavior,
                                                      get_details=1)
                if not ok:
                    raise CopyError, '%s not allowed, %s' % (behavior, why)
                containers.append(container)
            # verify self ACTs
            act = self.getTypeInfo().allowed_content_types
            if ob.getPortalTypeName() not in act:
                why = 'Wrong content type'
                raise CopyError, '%s not allowed, %s' % (behavior, why)
            oblist.append(ob)

        result = []
        containers = []
        if op == 0:
            # Copy operation
            for ob in oblist:
                orig_id = ob.getId()
                if not ob.cb_isCopyable():
                    raise CopyError, 'Copy not supported for %s' % orig_id
                ob._notifyOfCopyTo(self, op=0)
                ob = ob._getCopy(self)
                id = self._get_id(orig_id)
                result.append({'id': orig_id, 'new_id': id})
                ob._setId(id)
                self._setObject(id, ob)
                ob = self._getOb(id)
                ob.manage_afterClone(ob)
                # unshare content after copy
                pxtool.unshareContentRecursive(ob)
                # notify interested parties
                if hasattr(aq_base(ob), 'manage_afterCMFAdd'):
                    ob.manage_afterCMFAdd(ob, self)
        elif op == 1:
            # Move operation
            for ob in oblist:
                orig_id = ob.getId()
                if not ob.cb_isMoveable():
                    raise CopyError, 'Move not supported for %s' % orig_id
                ob._notifyOfCopyTo(self, op=1)
                if not sanity_check(self, ob):
                    raise CopyError, 'This object cannot be pasted into itself'

                orig_container = aq_parent(aq_inner(ob))
                if self == orig_container:
                    raise CopyError, 'Cannot cut/paste in the same place'

                # try to make ownership explicit so that it gets carried
                # along to the new location if needed.
                ob.manage_changeOwnershipType(explicit=1)

                # this is a move operation: do not send IObjectRemovedEvent
                orig_container._delObject(orig_id, suppress_events=True)

                # XXX: the following is necessary because of the wierd semantics
                # of CPS notifyCompat
                notify(ObjectWillBeRemovedEvent(ob, orig_container, orig_id))

                ob = aq_base(ob)
                id = self._get_id(orig_id)
                result.append({'id':orig_id, 'new_id':id })
                ob._setId(id)
                self._setObject(id, ob, set_owner=0)
                # try to make ownership implicit if possible
                ob = self._getOb(id)
                ob.manage_changeOwnershipType(explicit=0)
                # notify interested parties
                if hasattr(aq_base(ob), 'manage_afterCMFAdd'):
                    ob.manage_afterCMFAdd(ob, self)
                notify(ObjectMovedEvent(ob, orig_container, orig_id, self, id))
                notifyContainerModified(orig_container)
                if aq_base(orig_container) is not aq_base(self):
                    notifyContainerModified(self)

        # Do not move this import from here: causes import problems at
        # initialization time because of weird dependencies
        from Products.CPSWorkflow import transitions

        # Insert the new pasted object within the workflow if the
        # workflows are differents in between the orig and the dest.
        for new_id in [x['new_id'] for x in result]:
            ob = getattr(self, new_id)
            if wftool.getInfoFor(ob, 'review_state') is None:
                type_name = getattr(ob, 'portal_type', '')
                inserted = False
                for behavior in (transitions.TRANSITION_INITIAL_CREATE,
                                 transitions.TRANSITION_INITIAL_PUBLISHING):
                    if inserted:
                        break
                    crtrans = wftool.getInitialTransitions(
                        self, type_name, behavior)
                    for initial_transition in crtrans:
                        initial_behavior = behavior
                        try:
                            wftool._insertWorkflowRecursive(
                                ob, initial_transition, initial_behavior, {})
                            inserted = True
                            break
                        except (WorkflowException, Unauthorized):
                            # Let's try other transitions
                            pass
                if not inserted:
                    raise WorkflowException(
                        "You are not allowed to copy / paste here !")
        return result

    TypeContainer.manage_CPSpasteObjects = manage_CPSpasteObjects
