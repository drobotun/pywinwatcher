"""Process monitor module.

This module contains a description of classes that implement methods for
processes monitoring.

Exampile:

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
"""
import wmi

from pywinwatcher.util import date_time_format

class ProcessMonitor():
    """Сlass defines a processes monitor object."""

    def __init__(self, notify_filter='Operation'):
        """Initialize an instance of the class.

        Args:
          action (str): Type monitored operation. It can take the following
            values:
            - 'Operation': All possible operations with processes.
            - 'Creation': Creating a process.
            - 'Deletion': Deleting a process.
            - 'Modification': Process modification.
          pause (int): Delay between event views.
          in_thread (boolean): If you need to run in a thread, then True,
            otherwise False.

        Raises:
          ProcMonitorError: When errors occur when watcher installation error.
        """
        valid_notify_filter = (
            'Operation',
            'Creation',
            'Deletion',
            'Modification'
        )
        if notify_filter not in valid_notify_filter:
            raise ProcMonitorError(
                'Watcher installation error.'
                'The notify_filter value cannot be: "{}".'.
                format(notify_filter)
            )
        self._process_property = {
            'EventType': None,
            'Caption': None,
            'CommandLine': None,
            'CreationDate': None,
            'Description': None,
            'ExecutablePath': None,
            'HandleCount': None,
            'Name': None,
            'ParentProcessId': None,
            'ProcessID': None,
            'ThreadCount': None,
            'TimeStamp': None,
        }
        self._process_watcher = wmi.WMI().Win32_Process.watch_for(
            notify_filter
        )

    def update(self):
        """Update the properties of a process when the event occurs.

        This function updates the dict with process properties when a particular
        event occurs with the process. Process properties can be obtained from
        the corresponding class attribute.
        """
        process = self._process_watcher()
        self._process_property['EventType'] = process.event_type
        self._process_property['Caption'] = process.Caption
        self._process_property['CommandLine'] = process.CommandLine
        self._process_property['CreationDate'] = process.CreationDate
        self._process_property['Description'] = process.Description
        self._process_property['ExecutablePath'] = process.ExecutablePath
        self._process_property['HandleCount'] = process.HandleCount
        self._process_property['Name'] = process.Name
        self._process_property['ParentProcessId'] = process.ParentProcessId
        self._process_property['ProcessID'] = process.ProcessID
        self._process_property['ThreadCount'] = process.ThreadCount
        self._process_property['TimeStamp'] = process.timestamp

    @property
    def timestamp(self):
        """Timestamp of the event occurrence."""
        return self._process_property['TimeStamp']

    @property
    def event_type(self):
        """Type of event that occurred."""
        return self._process_property['EventType']

    @property
    def caption(self):
        """Short description of an object—a one-line string."""
        return self._process_property['Caption']

    @property
    def command_line(self):
        """Command line used to start a specific process, if applicable."""
        return self._process_property['CommandLine']

    @property
    def creation_date(self):
        """Date and time the process begins executing."""
        return date_time_format(self._process_property['CreationDate'])

    @property
    def description(self):
        """Description of an object."""
        return self._process_property['Description']

    @property
    def executable_path(self):
        """Path to the executable file of the process."""
        return self._process_property['ExecutablePath']

    @property
    def handle_count(self):
        """Total number of open handles owned by the process."""
        return self._process_property['HandleCount']

    @property
    def name(self):
        """Name of the executable file responsible for the process."""
        return self._process_property['Name']

    @property
    def parent_process_id(self):
        """Unique identifier of the process that creates a process."""
        return self._process_property['ParentProcessId']

    @property
    def process_id(self):
        """Numeric identifier used to distinguish one process from another."""
        return self._process_property['ProcessID']

    @property
    def thread_count(self):
        """Number of active threads in a process."""
        return self._process_property['ThreadCount']

class ProcMonitorError(Exception):
    """Class of exceptions."""
    pass
