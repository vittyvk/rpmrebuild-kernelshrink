# Shrink kernel package with rpmrebuild

## About

This is a PoC plugin for [rpmrebuild] http://rpmrebuild.sourceforge.net/ which
allows to repackage `kernel` package for Fedora/CentOS stream/RHEL leaving only
the required content (modules, firmware).

## Usage

Using `mock`:

```
$ mock --init -r fedora-36-x86_64
$ mock -r fedora-36-x86_64 -i rpmrebuild -i python -i python-yaml -i kernel -i linux-firmware
$ mock -r fedora-36-x86_64 --copyin ./kernelshrink.* ./*.yaml  /usr/lib/rpmrebuild/plugins/
$ mock -r fedora-36-x86_64 --shell

<mock-chroot> sh-5.1# KSCONF=/usr/lib/rpmrebuild/plugins/aws-fedora.yaml rpmrebuild --include /usr/lib/rpmrebuild/plugins/kernelshrink.plug kernel-core
INFO: mock.py version 3.0 starting (python version = 3.10.4, NVR = mock-3.0-1.fc35)...
Start(bootstrap): init plugins
...
result: /builddir/build/RPMS/kernel-aws-5.17.12-300.fc36.x86_64.rpm
<mock-chroot> sh-5.1# exit

$ mock -r fedora-36-x86_64 --copyout /builddir/build/RPMS/kernel-aws-5.17.12-300.fc36.x86_64.rpm /tmp/

```

## Configuring

### How do I know which modules to include?

`getmods.sh` gives an example on how to list loaded modules in yaml format.

### Do I need to resolve module dependencies?

No, the script does that automatically.

### How do I know which firmware files I need?

Guess :-) Currently, there's no kernel interface to list all firmware files
which were loaded.

## Notes

Currently, there's no `rpmrebuild` package for CS9. F36 version can be
used instead.

## License

GNU GPLv2+
