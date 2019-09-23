"""XPath output plugin

Much code stolen from the pyang tree plugin.
"""

import optparse
import sys
import re

from pyang import plugin
from pyang import statements

def pyang_plugin_init():
    plugin.register_plugin(XPathPlugin())

class XPathPlugin(plugin.PyangPlugin):
    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts['xpath'] = self

    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--xpath-help",
                                 dest="xpath_help",
                                 action="store_true",
                                 help="Print help on tree symbols and exit"),
            optparse.make_option("--xpath-depth",
                                 type="int",
                                 dest="xpath_depth",
                                 help="Max number of levels to search"),
            optparse.make_option("--xpath-path",
                                 dest="xpath_path",
                                 help="Limit search to this subtree"),
            optparse.make_option("--xpath-name",
                                 dest="xpath_name",
                                 help="Only print nodes with this exact name"),
            optparse.make_option("--xpath-substring",
                                 dest="xpath_substring",
                                 help="Only print nodes containing this substring"),
            ]
        g = optparser.add_option_group("XPath output specific options")
        g.add_options(optlist)

    def setup_ctx(self, ctx):
        if ctx.opts.xpath_help:
            print_help()
            sys.exit(0)

    def setup_fmt(self, ctx):
        ctx.implicit_errors = False

    def emit(self, ctx, modules, fd):
        if ctx.opts.xpath_path is not None:
            path = ctx.opts.xpath_path.split('/')
            if path[0] == '':
                path = path[1:]
        else:
            path = None
        emit_tree(ctx, modules, fd, ctx.opts.xpath_depth, path)

def print_help():
    print("""
Each node is printed as one line with its XPath location, e.g.:
$ pyang -f xpath tailf-ncs.yang --xpath-substring back-track
tailf-ncs-devices.yang:22: warning: imported module tailf-ncs-monitoring not used
>>> module: tailf-ncs
/zombies/service/plan/component/back-track
/zombies/service/plan/component/back-track-goal
/zombies/service/plan/component/force-back-track
/zombies/service/plan/component/force-back-track/back-tracking-goal

>>>  augment /kicker:kickers:

>>>  notifications:

$ pyang -f xpath tailf-ncs.yang --xpath-name name --xpath-path /zombies
tailf-ncs-devices.yang:22: warning: imported module tailf-ncs-monitoring not used
>>> module: tailf-ncs
/zombies/service/plan/component/name
/zombies/service/plan/component/state/name
/zombies/service/plan/component/private/property-list/property/name
/zombies/service/re-deploy/commit-queue/failed-device/name

>>>  augment /kicker:kickers:
/notification-kicker/variable/name

""")

def emit_tree(ctx, modules, fd, depth, path):
    for module in modules:
        printed_header = False

        def print_header():
            bstr = ""
            b = module.search_one('belongs-to')
            if b is not None:
                bstr = " (belongs-to %s)" % b.arg
            fd.write(">>> %s: %s%s\n" % (module.keyword, module.arg, bstr))
            printed_header = True

        chs = [ch for ch in module.i_children
               if ch.keyword in statements.data_definition_keywords]
        if path is not None and len(path) > 0:
            chs = [ch for ch in chs if ch.arg == path[0]]
            path = path[1:]

        if len(chs) > 0:
            if not printed_header:
                print_header()
                printed_header = True
            print_children(ctx, chs, module, fd, '', path, 'data', depth)

        mods = [module]
        for i in module.search('include'):
            subm = ctx.get_module(i.arg)
            if subm is not None:
                mods.append(subm)
        for m in mods:
            section_delimiter_printed=False
            for augment in m.search('augment'):
                if (hasattr(augment.i_target_node, 'i_module') and
                    augment.i_target_node.i_module not in modules + mods):
                    if not section_delimiter_printed:
                        fd.write('\n')
                        section_delimiter_printed = True
                    # this augment has not been printed; print it
                    if not printed_header:
                        print_header()
                        printed_header = True
                    fd.write(">>>  augment %s:\n" % augment.arg)
                    print_children(ctx, augment.i_children, m, fd,
                                   '', path, 'augment', depth)

        rpcs = [ch for ch in module.i_children
                if ch.keyword == 'rpc']
        if path is not None:
            if len(path) > 0:
                rpcs = [rpc for rpc in rpcs if rpc.arg == path[0]]
                path = path[1:]
            else:
                rpcs = []
        if len(rpcs) > 0:
            if not printed_header:
                print_header()
                printed_header = True
            fd.write("\n>>>  rpcs:\n")
            print_children(ctx, rpcs, module, fd, '', path, 'rpc', depth)

        notifs = [ch for ch in module.i_children
                  if ch.keyword == 'notification']
        if path is not None:
            if len(path) > 0:
                notifs = [n for n in notifs if n.arg == path[0]]
                path = path[1:]
            else:
                notifs = []
        if len(notifs) > 0:
            if not printed_header:
                print_header()
                printed_header = True
            fd.write("\n>>>  notifications:\n")
            print_children(ctx, notifs, module, fd, '', path,
                           'notification', depth)

def print_children(ctx, i_children, module, fd, prefix, path, mode, depth):
    if depth == 0:
        return

    for ch in i_children:
        if ((ch.keyword == 'input' or ch.keyword == 'output') and
            len(ch.i_children) == 0):
            pass
        else:
            if ch.keyword == 'input':
                mode = 'input'
            elif ch.keyword == 'output':
                mode = 'output'
            print_node(ctx, ch, module, fd, prefix, path, mode, depth)

def print_node(ctx, s, module, fd, prefix, path, mode, depth):
    line = prefix
    hideline = False

    if s.i_module.i_modulename == module.i_modulename:
        name = s.arg
    else:
        name = s.i_module.i_prefix + ':' + s.arg
    if s.keyword in ['list', 'container', 'leaf', 
            'leaf-list', 'anydata', 'anyxml',
            'notification', 'rpc', ('tailf-common', 'action')]:
        line += "/" + name
    elif s.keyword  in ['choice', 'case', 'input', 'output']:
        hideline = True
    else:
        fd.write(">>> Unknown keyword %s\n"%(s.keyword,))
        line += "/" + name

    if(ctx.opts.xpath_name and ctx.opts.xpath_name != name):
        hideline = True

    if(ctx.opts.xpath_substring and ctx.opts.xpath_substring not in name):
        hideline = True 

    if(not hideline):
        fd.write(line + '\n')

    if hasattr(s, 'i_children'):
        if depth is not None:
            depth -= 1
        chs = s.i_children
        if path is not None and len(path) > 0:
            chs = [ch for ch in chs
                   if ch.arg == path[0]]
            path = path[1:]
        print_children(ctx, chs, module, fd, line, path, mode, depth)
