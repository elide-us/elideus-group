# Migration: Remove ``db:account:account`` aliases

Historically the account security helpers exposed duplicate operation names
(``db:account:account:*``) to provide a temporary compatibility layer while the
registry naming scheme was being aligned with the ``db:<domain>:<subdomain>``
pattern.  That shim has been removed—every consumer must now invoke the plural
``accounts`` subdomain explicitly:

* ``db:account:accounts:get_security_profile:1``
* ``db:account:accounts:exists:1``

Update any hard-coded references or request builders that still target the old
``db:account:account`` prefix before upgrading to this release.
