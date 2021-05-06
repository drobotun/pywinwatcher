"""Windows registry monitor module.

This module contains a description of classes that implement methods for
monitoring events in the Windows registry.

Example with RegistryMonitorAPI class use:

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
"""

import datetime
import pywintypes
import win32con
import win32api
import win32event
import wmi

class RegistryMonitor:
    """Base class of monitoring events in the Windows registry."""

    def __init__(self, notify_filter, **kwargs):
        valid_kwargs = ('Hive', 'RootPath', 'KeyPath', 'ValueName')
        for key in kwargs:
            if key not in valid_kwargs:
                raise RegistryMonitorError(
                    'Watcher installation error.'
                    'Invalid parameters of the registry access.'
                )
        self._notify_filter = notify_filter
        self._kwargs = kwargs
        self._event_properties = {
            'Hive': None,
            'RootPath': None,
            'KeyPath': None,
            'ValueName': None,
            'Timestamp': None,
            'EventType': None,
        }

    @property
    def hive(self):
        """Registry hive where the changes occurred."""
        return self._event_properties['Hive']

    @property
    def root_path(self):
        """Path to the registry key where the changes occurred."""
        return self._event_properties['RootPath']

    @property
    def key_path(self):
        """Registry key where the changes occurred."""
        return self._event_properties['KeyPath']

    @property
    def value_name(self):
        """Value in the registry key that was changed."""
        return self._event_properties['ValueName']

    @property
    def timestamp(self):
        """Registry event date and time (in UTC format)."""
        return self._event_properties['Timestamp']

    @property
    def event_type(self):
        """Type of registry event."""
        return self._event_properties['EventType']

class RegistryMonitorAPI(RegistryMonitor):
    """Сlass defines a register monitor object.

    This class is based on using the Windows registry API functions:
    RegOpenKeyEx and RegNotifyChangeKeyValue.
    """

    def __init__(self, notify_filter='UnionChange', **kwargs):
        """Initialize an instance of the class.

        Args:
          notify_filter (str): A value that indicates the changes that should be
            reported. This parameter can be one or more of the following values:
            - 'NameChange' - Notify the caller if a subkey is added or deleted.
            - 'LastSetChange' - Notify the caller of changes to a value of the
              key. This can include adding or deleting a value, or changing an
              existing value.
            - 'UnionChange' - Includes the value of 'NameChange' and
              'LastSetChange'. This value is set by default.
            Default value - AND of all specified values.
          **hive (str): A registry hive, any one of the following value:
            - 'HKEY_CLASSES_ROOT'.
            - 'HKEY_CURRENT_USER'.
            - 'HKEY_LOCAL_MACHINE'.
            - 'HKEY_USERS'.
            - 'HKEY_CURRENT_CONFIG'.
          **key_path (str): The name of a key. This value must be a subkey of
            the root key identified by the 'hive' parameter.

        Raises:
          RegistryMonitorError: When errors occur when opening a registry key or
            creating an event object or watcher installation error.
        """
        RegistryMonitor.__init__(self, notify_filter, **kwargs)
        valid_notify_filter = ('NameChange', 'LastSetChange', 'UnionChange')
        if self._notify_filter not in valid_notify_filter:
            raise RegistryMonitorError(
                'Watcher installation error.'
                'The notify_filter value cannot be: "{}".'.
                format(self._notify_filter)
            )
        self._event = win32event.CreateEvent(None, False, False, None)
        if not self._event:
            raise RegistryMonitorError(
                'Watcher installation error.'
                'Failed to create event. Error code: {}.'
                .format(self._event)
            )
        try:
            self._key = win32api.RegOpenKeyEx(
                self._get_hive_const(),
                self._kwargs['KeyPath'],
                0,
                win32con.KEY_NOTIFY
            )
        except pywintypes.error as err:
            raise RegistryMonitorError(
                'Watcher installation error.'
                'Failed to open key. Error code: {}.'
                .format(err.winerror)
            ) from err
        self._set_watcher()

    def update(self):
        """Update the properties of a registry when the event occurs.

        This function updates the dict with registry properties when a specific
        event occurs related to a registry change. Registry properties can be
        obtained from the corresponding class attribute.
        """
        while True:
            result = win32event.WaitForSingleObject(self._event, 0)
            if result == win32con.WAIT_OBJECT_0:
                timestamp = datetime.datetime.fromtimestamp(
                    datetime.datetime.utcnow().timestamp()
                )
                self._event_properties['Hive'] = self._kwargs['Hive']
                self._event_properties['KeyPath'] = self._kwargs['KeyPath']
                self._event_properties['Timestamp'] = timestamp
                self._event_properties['EventType'] = self._notify_filter
                self._set_watcher()
                break
            if result == win32con.WAIT_FAILED:
                self.close()
                raise RegistryMonitorError()

    def close(self):
        """Close the registry key and event handles."""
        win32api.RegCloseKey(self._key)
        win32api.CloseHandle(self._event)

    def _get_notify_filter_const(self):
        if self._notify_filter == 'NameChange':
            return win32api.REG_NOTIFY_CHANGE_NAME
        if self._notify_filter == 'LastSetChange':
            return win32api.REG_NOTIFY_CHANGE_LAST_SET
        if self._notify_filter == 'UnionChange':
            return (
                win32api.REG_NOTIFY_CHANGE_NAME |
                win32api.REG_NOTIFY_CHANGE_LAST_SET
            )
        return None

    def _get_hive_const(self):
        if self._kwargs['Hive'] == 'HKEY_CLASSES_ROOT':
            return win32con.HKEY_CLASSES_ROOT
        if self._kwargs['Hive'] == 'HKEY_CURRENT_USER':
            return win32con.HKEY_CURRENT_USER
        if self._kwargs['Hive'] == 'HKEY_LOCAL_MACHINE':
            return win32con.HKEY_LOCAL_MACHINE
        if self._kwargs['Hive'] == 'HKEY_USERS':
            return win32con.HKEY_USERS
        if self._kwargs['Hive'] == 'HKEY_CURRENT_CONFIG':
            return win32con.HKEY_CURRENT_CONFIG
        return None

    def _set_watcher(self):
        try:
            win32api.RegNotifyChangeKeyValue(
                self._key,
                True,
                self._get_notify_filter_const(),
                self._event,
                True
            )
        except pywintypes.error as err:
            raise RegistryMonitorError(
                'Watcher installation error.'
                'Invalid parameters. Error code: {}.'
                .format(err.winerror)
            ) from err

class RegistryMonitorWMI(RegistryMonitor):
    """Сlass defines a register monitor object.

    This class is based on using the WMI registry event classes:
    RegistryTreeChangeEvent,  RegistryKeyChangeEvent and
    RegistryValueChangeEvent.
    """

    def __init__(self, notify_filter='ValueChange', **kwargs):
        """Initialize an instance of the class.

        Args:
          notify_filter (str): A value that indicates the changes that should be
            reported. This parameter can be one or more of the following values:
            - 'TreeChange' - Notify the caller of changes to a root key and its
              subkeys.
            - 'KeyChange' - Notify the caller of changes to a specific key.
            - 'ValueChange' - Notify the caller of changes to a single value of
              a specific key.
            Default value - 'KeyChange'.
          **hive (str): A registry hive, any one of the following value:
            - 'HKEY_LOCAL_MACHINE'.
            - 'HKEY_USERS'.
            - 'HKEY_CURRENT_CONFIG'.
          **root_path (str): Path to the registry key that contains the subkeys.
          **key_path (str): Path to the registry key.
          **value_name (str): Name of the value in the registry key.

        Raises:
          RegistryMonitorError: When errors occur when opening a registry key or
            creating an event object or watcher installation error.
        """
        RegistryMonitor.__init__(self, notify_filter, **kwargs)
        valid_notify_filter = ('TreeChange', 'KeyChange', 'ValueChange')
        if self._notify_filter not in valid_notify_filter:
            raise RegistryMonitorError(
                'Watcher installation error.'
                'The notify_filter value cannot be: "{}".'.
                format(self._notify_filter)
            )
        wmi_obj = wmi.WMI(namespace='root/DEFAULT')
        if notify_filter == 'TreeChange':
            try:
                self._watcher = wmi_obj.RegistryTreeChangeEvent.watch_for(
                    Hive=self._kwargs['Hive'],
                    RootPath=self._kwargs['RootPath'],
                )
            except wmi.x_wmi as err:
                raise RegistryMonitorError(
                    'Watcher installation error. Error code: {}.'.
                    format(err.com_error.hresult or 'unknown')
                ) from err
        elif notify_filter == 'KeyChange':
            try:
                self._watcher = wmi_obj.RegistryKeyChangeEvent.watch_for(
                    Hive=self._kwargs['Hive'],
                    KeyPath=self._kwargs['KeyPath'],
                )
            except wmi.x_wmi as err:
                raise RegistryMonitorError(
                    'Watcher installation error. Error code: {}.'.
                    format(err.com_error.hresult or 'unknown')
                ) from err
        elif notify_filter == 'ValueChange':
            try:
                self._watcher = wmi_obj.RegistryValueChangeEvent.watch_for(
                    Hive=self._kwargs['Hive'],
                    KeyPath=self._kwargs['KeyPath'],
                    ValueName=self._kwargs['ValueName'],
                )
            except wmi.x_wmi as err:
                raise RegistryMonitorError(
                    'Watcher installation error. Error code: {}.'.
                    format(err.com_error.hresult or 'unknown')
                ) from err
        else:
            raise RegistryMonitorError('Watcher installation error.')

    def update(self):
        """Update the properties of a registry when the event occurs.

        This function updates the dict with registry properties when a specific
        event occurs related to a registry change. Registry properties can be
        obtained from the corresponding class attribute.
        """
        event = self._watcher()
        self._event_properties['Timestamp'] = wmi.from_1601(event.TIME_CREATED)
        self._event_properties['EventType'] = self._notify_filter
        self._event_properties['Hive'] = event.Hive
        if hasattr(event, 'RootPath'):
            self._event_properties['RootPath'] = event.RootPath
        if hasattr(event, 'KeyPath'):
            self._event_properties['KeyPath'] = event.KeyPath
        if hasattr(event, 'ValueName'):
            self._event_properties['ValueName'] = event.ValueName

class RegistryMonitorError(Exception):
    """Class of exceptions."""
    pass
