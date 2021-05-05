"""Operating system event monitoring package

This package implements event monitoring with processes, file system, and
registry.
"""

from sys import version_info
from sys import platform
from sys import exit as sys_exit

from .regmon import (
    RegistryMonitorAPI,
    RegistryMonitorWMI,
    RegistryMonitorError,
)

from .filemon import(
    FileMonitorAPI,
    FileMonitorWMI,
    FileMonitorError,
)

from .procmon import (
    ProcessMonitor,
)

if version_info.major < 3:
    print('Use python version 3.0 and higher')
    sys_exit()

if platform != "win32":
    print('Unsupported operation sysytem')
    sys_exit()
