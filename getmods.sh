#! /bin/sh

echo "modulist:"
lsmod  | cut -f 1 -d ' ' | tail -n +2 | while read mod; do mod=`modinfo -F filename $mod | cut -f 5- -d '/'`; echo "  - $mod" ; done
