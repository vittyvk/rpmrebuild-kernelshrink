#! /usr/bin/python

##############################################################################
#   kernelshrink.plug
#
#    Copyright (C) 2022 by Red Hat
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
###############################################################################

import sys
import os
import yaml
import re
import glob

stage = os.environ['LONG_OPTION']

# WIP: assuming there's only one kernel installed.
kver = os.listdir("/lib/modules")[0]

# safely find files matching regexp, remove the leading prefix
def filterfiles(filelist, prefix, regexp):
    ret = set()
    prefix_len = len(prefix)
    for fname in filelist:
        fname = fname[prefix_len:]
        if re.search(regexp, fname) is not None:
            ret.add(fname)
    return list(ret)

def modclosure(modulist):
    moddeps = {}
    allmods = set()
    fd = open("/lib/modules/" + kver + "/modules.dep", "r")
    # Parse modules.dep for all modules
    for line in fd.readlines():
        moddeps[line.split(':')[0]] = line.split(':')[1].strip().split(' ')
    # Add all modules expanding regexps
    existmods = glob.glob("/lib/modules/%s/**/*.ko.*" % kver, recursive=True)
    for mod in modulist:
        fnames = filterfiles(existmods, "/lib/modules/%s/" % kver, mod)
        if fnames == []:
            sys.stderr.write("No modules matching '%s'!" % mod)
            sys.exit(1)
        for fname in fnames:
            allmods.add(fname)
    # Add all dependencies (+ their dependencies)
    while True:
        allmods_new = allmods.copy()
        for mod in allmods:
            for dep in moddeps[mod]:
                if dep != '':
                    allmods_new.add(dep)
        if len(allmods_new) == len(allmods):
            break
        allmods = allmods_new

    return allmods

def modaliases(modnames):
    aliases = []
    # Parse modules.alias and leave what's needed
    fd = open("/lib/modules/" + kver + "/modules.alias", "r")
    for line in fd.readlines():
        if line.split(' ')[2].strip() in modnames:
            aliases.append(line.split(' ')[1])
    return aliases

try:
    confile = os.environ['KSCONF']
    with open(confile, 'r') as fd:
        conf = yaml.safe_load(fd.read())
except:
    sys.stderr.write("KSCONF env variable should specify YAML config file!")
    sys.exit(1)

allmods = modclosure(conf['modulist'])
allmodnames = [s.split("/")[-1].replace(".ko.xz","") for s in allmods]
allmodnames_ko = [s.split("/")[-1].replace(".xz","") for s in allmods]
allaliases = modaliases(allmodnames)
addfiles = set()
if 'addfiles' in conf:
    for fname in conf['addfiles']:
        filelist = glob.glob(fname[:fname.rfind("/")] + "/**", recursive = True)
        fnames = filterfiles(filelist, "", fname)
        for fname in fnames:
            addfiles.add(fname)

if stage == "change-spec-preamble":
    for line in sys.stdin:
        # Change package's name
        if (line.startswith("Name:")):
            print("Name: " + conf['name'])
        else:
            print(line)
if stage == "change-spec-provides":
    for line in sys.stdin:
        # WIP: drop "Provides:kernel()" for now
        if (line.replace(' ','').startswith('Provides:kernel(')):
            pass
        # filter "Provides:kmod()"
        elif (line.replace(' ','').startswith('Provides:kmod(')):
            modname = re.search('\(.*\)', line).group(0)[1:-1]
            if modname in allmodnames_ko:
                print(line)
        # filter "Provides:modalias()"
        elif (line.replace(' ','').startswith('Provides:modalias(')):
            modalias = re.search('\(.*\)', line).group(0)[1:-1]
            if modalias in allaliases:
                print(line)
        else:
            print(line)
if stage == "change-spec-requires":
    for line in sys.stdin:
        if line.find('linux-firmware'):
            pass
        else:
            print(line)
if stage == "change-spec-recommends":
    for line in sys.stdin:
        if line.find('linux-firmware'):
            pass
        else:
            print(line)
if stage == "change-spec-files":
    for line in sys.stdin:
        try:
            modname = re.search('"/lib/modules/%s/(.*)\"' % kver, line).group(1)
            if not modname.startswith("kernel/"):
                print(line)
                continue
            # include all non-empty '%dir's
            if line.strip().startswith("%dir"):
                for mod in allmods:
                    if mod.startswith(modname):
                        print(line)
                        break
            # skipping actual module files here, will add everything
            # from allmods as it is possible to include modules not
            # only from kernel-core package
        except:
            print(line)

    for fname in allmods:
        # WIP: some %dirs may be missing (modules not from kernel-core)
        print('%attr(0644, root, root) "/lib/modules/' + kver + '/' + fname + '"')

    for fname in addfiles:
        # WIP: add %dirs maybe?
        print('%attr(0644, root, root) "' + fname + '"')
else:
    for line in sys.stdin:
        print(line)
