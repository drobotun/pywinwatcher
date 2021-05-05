"""File system monitor module.

This module contains a description of classes that implement methods for
monitoring events in the Windows file system.

Example with FileMonitorAPI class use:

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

"""
import datetime
import pywintypes
import win32api
import win32event
import win32con
import win32file
import winnt
import wmi

class FileMonitor:
    """Base class of monitoring events in the Windows file sysytem."""

    def __init__(self, notify_filter, **kwargs):
        valid_kwargs = ('Drive', 'Path', 'FileName', 'Extension')
        for key in kwargs:
            if key not in valid_kwargs:
                raise FileMonitorError(
                    'Watcher installation error.'
                    'Invalid parameters of the file access.'
                )
        self._notify_filter = notify_filter
        self._kwargs = kwargs
        self._event_properties = {
            'Drive': None,
            'Path': None,
            'FileName': None,
            'Extension': None,
            'Timestamp': None,
            'EventType': None,
        }

    @property
    def drive(self):
        return self._event_properties['Drive']

    @property
    def path(self):
        return self._event_properties['Path']

    @property
    def file_name(self):
        return self._event_properties['FileName']

    @property
    def extension(self):
        return self._event_properties['Extension']

    @property
    def timestamp(self):
        return self._event_properties['Timestamp']

    @property
    def event_type(self):
        return self._event_properties['EventType']

class FileMonitorAPI(FileMonitor):
    """Сlass defines a files monitor object."""

    _ACTIONS = {
        0x00000000: 'Unknown action',
        0x00000001: 'Added',
        0x00000002: 'Removed',
        0x00000003: 'Modified',
        0x00000004: 'Renamed from file or directory',
        0x00000005: 'Renamed to file or directory'
    }

    def __init__(self, notify_filter = 'UnionChange', **kwargs):
        """Initialize an instance of the class.

        Args:
          notify_filter (str): A value that indicates the changes that should be
            reported. This parameter can be one or more of the following values:
            - 'FileNameChange': Any file name change in the watched directory or
            subtree causes a change notification wait operation to return.
            Changes include renaming, creating, or deleting a file.
            - 'DirNameChange': Any directory-name change in the watched
            directory or subtree causes a change notification wait operation to
            return. Changes include creating or deleting a directory.
            - 'LastWriteChange': Any change to the last write-time of files in
            the watched directory or subtree causes a change notification wait
            operation to return. The operating system detects a change to the
            last write-time only when the file is written to the disk. For
            operating systems that use extensive caching, detection occurs only
            when the cache is sufficiently flushed.
            - 'UnionChange': Combining all events.

        Raises:
          FileMonitorError: When errors occur when opening a directory or
            creating an event object.
          TypeError: When the input parameter type is invalid.
        """
        FileMonitor.__init__(self, notify_filter, **kwargs)
        valid_notify_filter = (
            'FileNameChange',
            'DirNameChange',
            'LastWriteChange',
            'UnionChange'
        )
        if self._notify_filter not in valid_notify_filter:
            raise FileMonitorError(
                'Watcher installation error.'
                'The notify_filter value cannot be: "{}".'.
                format(self._notify_filter)
            )
        try:
            self._directory = win32file.CreateFile(
                self._kwargs['Path'],
                winnt.FILE_LIST_DIRECTORY,
                win32con.FILE_SHARE_READ |
                win32con.FILE_SHARE_WRITE,
                None,
                win32con.OPEN_EXISTING,
                win32con.FILE_FLAG_BACKUP_SEMANTICS |
                win32con.FILE_FLAG_OVERLAPPED,
                None
            )
        except pywintypes.error as err:
            raise FileMonitorError(
                'Failed to open directory. Error code: {}.'
                .format(err.winerror)
            ) from err
        self._overlapped = pywintypes.OVERLAPPED()
        self._overlapped.hEvent = win32event.CreateEvent(
            None,
            False,
            False,
            None
        )
        if not self._overlapped.hEvent:
            raise FileMonitorError(
                'Failed to create event. Error code: {}.'
                .format(self._overlapped.hEvent)
            )
        self._buffer  = win32file.AllocateReadBuffer(1024)
        self._num_bytes_returned = 0
        self._set_watcher()

    def update(self):
        """Update the properties of a file system when the event occurs.

        This function updates the dict with file system properties when a
        specific event occurs related to a file system change. File system
        properties can be obtained from the corresponding class attribute.
        """
        while True:
            result = win32event.WaitForSingleObject(self._overlapped.hEvent, 0)
            if result == win32con.WAIT_OBJECT_0:
                self._num_bytes_returned = win32file.GetOverlappedResult(
                    self._directory,
                    self._overlapped,
                    True
                )
                timestamp = datetime.datetime.fromtimestamp(
                    datetime.datetime.utcnow().timestamp()
                )
                self._event_properties['Path'] = self._get_path()
                self._event_properties['FileName'] = self._get_file_name()
                self._event_properties['Timestamp'] = timestamp
                self._event_properties['EventType'] = self._get_event_type()
                self._set_watcher()
                break
            if result == win32con.WAIT_FAILED:
                self.close()
                raise FileMonitorError()

    def close(self):
        """Close the open directory and event handles."""
        win32api.CloseHandle(self._kwargs['Path'])
        win32api.CloseHandle(self._overlapped.hEvent)

    def _get_notify_filter_const(self):
        if self._notify_filter == 'FileNameChange':
            return win32con.FILE_NOTIFY_CHANGE_FILE_NAME
        if self._notify_filter == 'DirNameChange':
            return win32con.FILE_NOTIFY_CHANGE_DIR_NAME
        if self._notify_filter == 'LastWriteChange':
            return win32con.FILE_NOTIFY_CHANGE_LAST_WRITE
        if self._notify_filter == 'UnionChange':
            return (
                win32con.FILE_NOTIFY_CHANGE_FILE_NAME |
                win32con.FILE_NOTIFY_CHANGE_DIR_NAME |
                win32con.FILE_NOTIFY_CHANGE_LAST_WRITE
            )
        return None

    def _get_event_type(self):
        result = ''
        if self._num_bytes_returned != 0:
            result = self._ACTIONS.get(win32file.FILE_NOTIFY_INFORMATION(
                self._buffer, self._num_bytes_returned)[0][0], 'Uncnown')
        return result

    def _get_path(self):
        result = ''
        if self._num_bytes_returned != 0:
            result = win32file.GetFinalPathNameByHandle(
                self._directory,
                win32con.FILE_NAME_NORMALIZED
            )
        return result

    def _get_file_name(self):
        result = ''
        if self._num_bytes_returned != 0:
            result = win32file.FILE_NOTIFY_INFORMATION(
                self._buffer, self._num_bytes_returned)[0][1]
        return result

    def _set_watcher(self):
        win32file.ReadDirectoryChangesW(
            self._directory,
            self._buffer,
            True,
            self._get_notify_filter_const(),
            self._overlapped,
            None
        )

class FileMonitorWMI(FileMonitor):

    def __init__(self, notify_obj='File', notify_filter='Operation', **kwargs):
        """Initialize an instance of the class.

        Args:
          notify_obj (str) : A parameter whose value defines the object whose
            events need to be monitored. This parameter can be one or more of
            the following values:
            - 'File' : Monitoring file events.
            - 'Directory' : Monitoring directory events.
          notify_filter (str): A value that indicates the changes that should be
            reported. This parameter can be one or more of the following values:
            - 'Operation': All possible operations with file or directory.
            - 'Creation': Creating a file or directory.
            - 'Deletion': Deleting a file or directory.
            - 'Modification': File or directory modification.

        Raises:
          FileMonitorError: When errors occur when opening a directory or
            creating an event object.
          TypeError: When the input parameter type is invalid.
        """
        FileMonitor.__init__(self, notify_filter, **kwargs)
        valid_notify_filter = (
            'Operation',
            'Creation',
            'Deletion',
            'Modification'
        )
        if self._notify_filter not in valid_notify_filter:
            raise FileMonitorError(
                'Watcher installation error.'
                'The notify_filter value cannot be: "{}".'.
                format(self._notify_filter)
            )
        valid_notify_obj = ('File', 'Directory')
        if notify_obj not in valid_notify_obj:
            raise FileMonitorError(
                'Watcher installation error.'
                'The notify_obj value cannot be: "{}".'.
                format(notify_obj)
            )
        wmi_obj = wmi.WMI(namespace='root/CIMv2')
        if notify_obj == 'File':
            try:
                self._watcher = wmi_obj.CIM_DataFile.watch_for(
                    self._notify_filter,
                    **kwargs
                )
            except wmi.x_wmi as err:
                raise FileMonitorError(
                    'Watcher installation error. Error code: {}.'.
                    format(err.com_error.hresult or 'unknown')
                ) from err
        elif notify_obj == 'Directory':
            try:
                self._watcher = wmi_obj.CIM_Directory.watch_for(
                    self._notify_filter,
                    **kwargs
                )
            except wmi.x_wmi as err:
                raise FileMonitorError(
                    'Watcher installation error. Error code: {}.'.
                    format(err.com_error.hresult or 'unknown')
                ) from err
        else:
            raise FileMonitorError('Watcher installation error.')

    def update(self):
        """Update the properties of a file system when the event occurs.

        This function updates the dict with file system properties when a
        specific event occurs related to a file system change. File system
        properties can be obtained from the corresponding class attribute.
        """
        event = self._watcher()
        self._event_properties['Timestamp'] = event.timestamp
        self._event_properties['EventType'] = event.event_type
        if hasattr(event, 'Drive'):
            self._event_properties['Drive'] = event.Drive
        if hasattr(event, 'Path'):
            self._event_properties['Path'] = event.Path
        if hasattr(event, 'FileName'):
            self._event_properties['FileName'] = event.FileName
        if hasattr(event, 'Extension'):
            self._event_properties['Extension'] = event.Extension

class FileMonitorError(Exception):
    """Class of exceptions."""
    pass
