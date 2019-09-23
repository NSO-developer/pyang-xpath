# pyang-xpath

XPath plugin for pyang
 -- lists the XPath paths for all or selected YANG elements

This plugin prints the name of each YANG node on a separate line with
its full XPath path. This is useful when looking for a particular 
element in a large YANG file, and looking for the exact path it
(or they) are at.

```
  XPath output specific options:
    --xpath-help        Print help on tree symbols and exit
    --xpath-depth=XPATH_DEPTH
                        Max number of levels to search
    --xpath-path=XPATH_PATH
                        Limit search to this subtree
    --xpath-name=XPATH_NAME
                        Only print nodes with this exact name
    --xpath-substring=XPATH_SUBSTRING
                        Only print nodes containing this substring
```

A couple of examples:

```
$ pyang -f xpath tailf-ncs.yang --xpath-substring back-track
tailf-ncs-devices.yang:22: warning: imported module tailf-ncs-monitoring not used
>>> module: tailf-ncs
/zombies/service/plan/component/back-track
/zombies/service/plan/component/back-track-goal
/zombies/service/plan/component/force-back-track
/zombies/service/plan/component/force-back-track/back-tracking-goal

>>>  augment /kicker:kickers:

>>>  notifications:
```

```
$ pyang -f xpath tailf-ncs.yang --xpath-name name --xpath-path /zombies
tailf-ncs-devices.yang:22: warning: imported module tailf-ncs-monitoring not used
>>> module: tailf-ncs
/zombies/service/plan/component/name
/zombies/service/plan/component/state/name
/zombies/service/plan/component/private/property-list/property/name
/zombies/service/re-deploy/commit-queue/failed-device/name

>>>  augment /kicker:kickers:
/notification-kicker/variable/name
```

Note that unless you copy the plugin to your pyang installation's 
plugin directory, you will need to add a --plugindir= option to
point out where you have your xpath.py plugin.
