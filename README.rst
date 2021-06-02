.. image:: https://img.shields.io/pypi/l/pywinwatcher
.. image:: https://i.imgur.com/JtZ54GZ.png
    :target: https://xakep.ru/2021/05/20/malware-analysis-python/

Operating system event monitoring package
=========================================

This package implements event monitoring with processes, file system, and registry.

Installation
""""""""""""

.. code-block:: bash

    $ pip install pywinwatcher

Usage
"""""

Process event monitoring
------------------------

.. code-block:: python

    from threading import Thread
    import keyboard
    import pythoncom
    import pywinwatcher

    class Monitor(Thread):

        def __init__(self, action):

            Thread.__init__(self)
            self._action = action

        def run(self):
            print('Start monitoring...')
            #Use pythoncom.CoInitialize when starting monitoring in a thread.
            pythoncom.CoInitialize()
            proc_mon = pywinwatcher.ProcessMonitor(self._action)
            while not keyboard.is_pressed('ctrl+q'):
                proc_mon.update()
                print(
                    proc_mon.timestamp,
                    proc_mon.event_type,
                    proc_mon.name,
                    proc_mon.process_id
                )
            pythoncom.CoUninitialize()

    monitor = Monitor('сreation')
    monitor.start()

File system event monitoring
----------------------------

Example with FileMonitorAPI class use:

.. code-block:: python

    from threading import Thread
    import keyboard
    import pywinwatcher

    class Monitor(Thread):

        def __init__(self, action):

            Thread.__init__(self)
            self._action = action

        def run(self):
            print('Start monitoring...')
            file_mon = pywinwatcher.FileMonitorAPI(Path=r'c:\\Windows')
            while not keyboard.is_pressed('ctrl+q'):
                file_mon.update()
                print(
                    file_mon.timestamp,
                    file_mon.event_type
                )
            pythoncom.CoUninitialize()

    monitor = Monitor()
    monitor.start()

Example with FileMonitorWMI class use:

.. code-block:: python

    from threading import Thread
    import keyboard
    import pythoncom
    import pywinwatcher

    class Monitor(Thread):

        def __init__(self):
            Thread.__init__(self)

        def run(self):
            print('Start monitoring...')
            #Use pythoncom.CoInitialize when starting monitoring in a thread.
            pythoncom.CoInitialize()
            file_mon = pywinwatcher.FileMonitorWMI(
                Drive=r'e:',
                Path=r'\\Windows\\',
                FileName=r'text',
                Extension=r'txt'
            )
            while not keyboard.is_pressed('ctrl+q'):
                file_mon.update()
                print(
                    file_mon.timestamp,
                    file_mon.event_type
                )
        pythoncom.CoUninitialize()

    monitor = Monitor()
    monitor.start()

Registry event monitoring
-------------------------

Example with RegistryMonitorAPI class use:

.. code-block:: python

    from threading import Thread
    import keyboard
    import pywinwatcher

    class Monitor(Thread):

        def __init__(self, action):

            Thread.__init__(self)
            self._action = action

        def run(self):
            print('Start monitoring...')
            reg_mon = pywinwatcher.RegistryMonitorAPI(
                'UnionChange',
                Hive='HKEY_LOCAL_MACHINE',
                KeyPath=r'SOFTWARE'
            )
            while not keyboard.is_pressed('ctrl+q'):
                reg_mon.update()
                print(
                    reg_mon.timestamp,
                    reg_mon.event_type
                )
            pythoncom.CoUninitialize()

    monitor = Monitor()
    monitor.start()

Example with RegistryMonitorWMI class use:

.. code-block:: python

    from threading import Thread
    import keyboard
    import pythoncom
    import pywinwatcher

    class Monitor(Thread):

        def __init__(self):
            Thread.__init__(self)

        def run(self):
            print('Start monitoring...')
            #Use pythoncom.CoInitialize when starting monitoring in a thread.
            pythoncom.CoInitialize()
            reg_mon = pywinwatcher.RegistryMonitorWMI(
                'KeyChange',
                Hive='HKEY_LOCAL_MACHINE',
                KeyPath=r'SOFTWARE'
            )
            while not keyboard.is_pressed('ctrl+q'):
                reg_mon.update()
                print(
                    reg_mon.timestamp,
                    reg_mon.event_type
                )
        pythoncom.CoUninitialize()

    monitor = Monitor()
    monitor.start()

License
"""""""

MIT Copyright (c) 2021 Evgeny Drobotun
