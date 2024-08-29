import re;
import base64;

permissions = [    'android.permission.ACCESS_ALL_DOWNLOADS',
                    'android.permission.ACCESS_BLUETOOTH_SHARE',
                    'android.permission.ACCESS_CACHE_FILESYSTEM',
                    'android.permission.ACCESS_CHECKIN_PROPERTIES',
                    'android.permission.ACCESS_COARSE_LOCATION',
                    'android.permission.ACCESS_CONTENT_PROVIDERS_EXTERNALLY',
                    'android.permission.ACCESS_DOWNLOAD_MANAGER',
                    'android.permission.ACCESS_DOWNLOAD_MANAGER_ADVANCED',
                    'android.permission.ACCESS_DRM_CERTIFICATES',
                    'android.permission.ACCESS_EPHEMERAL_APPS',
                    'android.permission.ACCESS_FINE_LOCATION',
                    'android.permission.ACCESS_FM_RADIO',
                    'android.permission.ACCESS_INPUT_FLINGER',
                    'android.permission.ACCESS_KEYGUARD_SECURE_STORAGE',
                    'android.permission.ACCESS_LOCATION_EXTRA_COMMANDS',
                    'android.permission.ACCESS_MOCK_LOCATION',
                    'android.permission.ACCESS_MTP',
                    'android.permission.ACCESS_NETWORK_CONDITIONS',
                    'android.permission.ACCESS_NETWORK_STATE',
                    'android.permission.ACCESS_NOTIFICATIONS',
                    'android.permission.ACCESS_NOTIFICATION_POLICY',
                    'android.permission.ACCESS_PDB_STATE',
                    'android.permission.ACCESS_SURFACE_FLINGER',
                    'android.permission.ACCESS_VOICE_INTERACTION_SERVICE',
                    'android.permission.ACCESS_VR_MANAGER',
                    'android.permission.ACCESS_WIFI_STATE',
                    'android.permission.ACCESS_WIMAX_STATE',
                    'android.permission.ACCOUNT_MANAGER',
                    'android.permission.ADD_VOICEMAIL',
                    'android.permission.ALLOW_ANY_CODEC_FOR_PLAYBACK',
                    'android.permission.ASEC_ACCESS',
                    'android.permission.ASEC_CREATE',
                    'android.permission.ASEC_DESTROY',
                    'android.permission.ASEC_MOUNT_UNMOUNT',
                    'android.permission.ASEC_RENAME',
                    'android.permission.AUTHENTICATE_ACCOUNTS',
                    'android.permission.BACKUP',
                    'android.permission.BATTERY_STATS',
                    'android.permission.BIND_ACCESSIBILITY_SERVICE',
                    'android.permission.BIND_APPWIDGET',
                    'android.permission.BIND_CARRIER_MESSAGING_SERVICE',
                    'android.permission.BIND_CARRIER_SERVICES',
                    'android.permission.BIND_CHOOSER_TARGET_SERVICE',
                    'android.permission.BIND_CONDITION_PROVIDER_SERVICE',
                    'android.permission.BIND_CONNECTION_SERVICE',
                    'android.permission.BIND_DEVICE_ADMIN',
                    'android.permission.BIND_DIRECTORY_SEARCH',
                    'android.permission.BIND_DREAM_SERVICE',
                    'android.permission.BIND_INCALL_SERVICE',
                    'android.permission.BIND_INPUT_METHOD',
                    'android.permission.BIND_INTENT_FILTER_VERIFIER',
                    'android.permission.BIND_JOB_SERVICE',
                    'android.permission.BIND_KEYGUARD_APPWIDGET',
                    'android.permission.BIND_MIDI_DEVICE_SERVICE',
                    'android.permission.BIND_NFC_SERVICE',
                    'android.permission.BIND_NOTIFICATION_LISTENER_SERVICE',
                    'android.permission.BIND_NOTIFICATION_RANKER_SERVICE',
                    'android.permission.BIND_PACKAGE_VERIFIER',
                    'android.permission.BIND_PRINT_RECOMMENDATION_SERVICE',
                    'android.permission.BIND_PRINT_SERVICE',
                    'android.permission.BIND_PRINT_SPOOLER_SERVICE',
                    'android.permission.BIND_QUICK_SETTINGS_TILE',
                    'android.permission.BIND_REMOTEVIEWS',
                    'android.permission.BIND_REMOTE_DISPLAY',
                    'android.permission.BIND_ROUTE_PROVIDER',
                    'android.permission.BIND_RUNTIME_PERMISSION_PRESENTER_SERVICE',
                    'android.permission.BIND_SCREENING_SERVICE',
                    'android.permission.BIND_TELECOM_CONNECTION_SERVICE',
                    'android.permission.BIND_TEXT_SERVICE',
                    'android.permission.BIND_TRUST_AGENT',
                    'android.permission.BIND_TV_INPUT',
                    'android.permission.BIND_TV_REMOTE_SERVICE',
                    'android.permission.BIND_VOICE_INTERACTION',
                    'android.permission.BIND_VPN_SERVICE',
                    'android.permission.BIND_VR_LISTENER_SERVICE',
                    'android.permission.BIND_WALLPAPER',
                    'android.permission.BLUETOOTH',
                    'android.permission.BLUETOOTH_ADMIN',
                    'android.permission.BLUETOOTH_MAP',
                    'android.permission.BLUETOOTH_PRIVILEGED',
                    'android.permission.BLUETOOTH_STACK',
                    'android.permission.BRICK',
                    'android.permission.BROADCAST_CALLLOG_INFO',
                    'android.permission.BROADCAST_NETWORK_PRIVILEGED',
                    'android.permission.BROADCAST_PACKAGE_REMOVED',
                    'android.permission.BROADCAST_PHONE_ACCOUNT_REGISTRATION',
                    'android.permission.BROADCAST_SMS',
                    'android.permission.BROADCAST_STICKY',
                    'android.permission.BROADCAST_WAP_PUSH',
                    'android.permission.CACHE_CONTENT',
                    'android.permission.CALL_PHONE',
                    'android.permission.CALL_PRIVILEGED',
                    'android.permission.CAMERA',
                    'android.permission.CAMERA_DISABLE_TRANSMIT_LED',
                    'android.permission.CAMERA_SEND_SYSTEM_EVENTS',
                    'android.permission.CAPTURE_AUDIO_HOTWORD',
                    'android.permission.CAPTURE_AUDIO_OUTPUT',
                    'android.permission.CAPTURE_SECURE_VIDEO_OUTPUT',
                    'android.permission.CAPTURE_TV_INPUT',
                    'android.permission.CAPTURE_VIDEO_OUTPUT',
                    'android.permission.CARRIER_FILTER_SMS',
                    'android.permission.CHANGE_APP_IDLE_STATE',
                    'android.permission.CHANGE_BACKGROUND_DATA_SETTING',
                    'android.permission.CHANGE_COMPONENT_ENABLED_STATE',
                    'android.permission.CHANGE_CONFIGURATION',
                    'android.permission.CHANGE_DEVICE_IDLE_TEMP_WHITELIST',
                    'android.permission.CHANGE_NETWORK_STATE',
                    'android.permission.CHANGE_WIFI_MULTICAST_STATE',
                    'android.permission.CHANGE_WIFI_STATE',
                    'android.permission.CHANGE_WIMAX_STATE',
                    'android.permission.CLEAR_APP_CACHE',
                    'android.permission.CLEAR_APP_GRANTED_URI_PERMISSIONS',
                    'android.permission.CLEAR_APP_USER_DATA',
                    'android.permission.CONFIGURE_DISPLAY_COLOR_TRANSFORM',
                    'android.permission.CONFIGURE_WIFI_DISPLAY',
                    'android.permission.CONFIRM_FULL_BACKUP',
                    'android.permission.CONNECTIVITY_INTERNAL',
                    'android.permission.CONTROL_INCALL_EXPERIENCE',
                    'android.permission.CONTROL_KEYGUARD',
                    'android.permission.CONTROL_LOCATION_UPDATES',
                    'android.permission.CONTROL_VPN',
                    'android.permission.CONTROL_WIFI_DISPLAY',
                    'android.permission.COPY_PROTECTED_DATA',
                    'android.permission.CREATE_USERS',
                    'android.permission.CRYPT_KEEPER',
                    'android.permission.DELETE_CACHE_FILES',
                    'android.permission.DELETE_PACKAGES',
                    'android.permission.DEVICE_POWER',
                    'android.permission.DIAGNOSTIC',
                    'android.permission.DISABLE_KEYGUARD',
                    'android.permission.DISPATCH_NFC_MESSAGE',
                    'android.permission.DISPATCH_PROVISIONING_MESSAGE',
                    'android.permission.DOWNLOAD_CACHE_NON_PURGEABLE',
                    'android.permission.DUMP',
                    'android.permission.DVB_DEVICE',
                    'android.permission.EXPAND_STATUS_BAR',
                    'android.permission.FACTORY_TEST',
                    'android.permission.FILTER_EVENTS',
                    'android.permission.FLASHLIGHT',
                    'android.permission.FORCE_BACK',
                    'android.permission.FORCE_STOP_PACKAGES',
                    'android.permission.FRAME_STATS',
                    'android.permission.FREEZE_SCREEN',
                    'android.permission.GET_ACCOUNTS',
                    'android.permission.GET_ACCOUNTS_PRIVILEGED',
                    'android.permission.GET_APP_GRANTED_URI_PERMISSIONS',
                    'android.permission.GET_APP_OPS_STATS',
                    'android.permission.GET_DETAILED_TASKS',
                    'android.permission.GET_INTENT_SENDER_INTENT',
                    'android.permission.GET_PACKAGE_IMPORTANCE',
                    'android.permission.GET_PACKAGE_SIZE',
                    'android.permission.GET_PASSWORD',
                    'android.permission.GET_PROCESS_STATE_AND_OOM_SCORE',
                    'android.permission.GET_TASKS',
                    'android.permission.GET_TOP_ACTIVITY_INFO',
                    'android.permission.GLOBAL_SEARCH',
                    'android.permission.GLOBAL_SEARCH_CONTROL',
                    'android.permission.GRANT_RUNTIME_PERMISSIONS',
                    'android.permission.HARDWARE_TEST',
                    'android.permission.HDMI_CEC',
                    'android.permission.INJECT_EVENTS',
                    'android.permission.INSTALL_GRANT_RUNTIME_PERMISSIONS',
                    'android.permission.INSTALL_LOCATION_PROVIDER',
                    'android.permission.INSTALL_PACKAGES',
                    'android.permission.INTENT_FILTER_VERIFICATION_AGENT',
                    'android.permission.INTERACT_ACROSS_USERS',
                    'android.permission.INTERACT_ACROSS_USERS_FULL',
                    'android.permission.INTERNAL_SYSTEM_WINDOW',
                    'android.permission.INTERNET',
                    'android.permission.INVOKE_CARRIER_SETUP',
                    'android.permission.KILL_BACKGROUND_PROCESSES',
                    'android.permission.KILL_UID',
                    'android.permission.LAUNCH_TRUST_AGENT_SETTINGS',
                    'android.permission.LOCAL_MAC_ADDRESS',
                    'android.permission.LOCATION_HARDWARE',
                    'android.permission.LOOP_RADIO',
                    'android.permission.MANAGE_ACCOUNTS',
                    'android.permission.MANAGE_ACTIVITY_STACKS',
                    'android.permission.MANAGE_APP_OPS_RESTRICTIONS',
                    'android.permission.MANAGE_APP_TOKENS',
                    'android.permission.MANAGE_CA_CERTIFICATES',
                    'android.permission.MANAGE_DEVICE_ADMINS',
                    'android.permission.MANAGE_DOCUMENTS',
                    'android.permission.MANAGE_FINGERPRINT',
                    'android.permission.MANAGE_MEDIA_PROJECTION',
                    'android.permission.MANAGE_NETWORK_POLICY',
                    'android.permission.MANAGE_NOTIFICATIONS',
                    'android.permission.MANAGE_PROFILE_AND_DEVICE_OWNERS',
                    'android.permission.MANAGE_SOUND_TRIGGER',
                    'android.permission.MANAGE_USB',
                    'android.permission.MANAGE_USERS',
                    'android.permission.MANAGE_VOICE_KEYPHRASES',
                    'android.permission.MASTER_CLEAR',
                    'android.permission.MEDIA_CONTENT_CONTROL',
                    'android.permission.MODIFY_APPWIDGET_BIND_PERMISSIONS',
                    'android.permission.MODIFY_AUDIO_ROUTING',
                    'android.permission.MODIFY_AUDIO_SETTINGS',
                    'android.permission.MODIFY_CELL_BROADCASTS',
                    'android.permission.MODIFY_DAY_NIGHT_MODE',
                    'android.permission.MODIFY_NETWORK_ACCOUNTING',
                    'android.permission.MODIFY_PARENTAL_CONTROLS',
                    'android.permission.MODIFY_PHONE_STATE',
                    'android.permission.MOUNT_FORMAT_FILESYSTEMS',
                    'android.permission.MOUNT_UNMOUNT_FILESYSTEMS',
                    'android.permission.MOVE_PACKAGE',
                    'android.permission.NET_ADMIN',
                    'android.permission.NET_TUNNELING',
                    'android.permission.NFC',
                    'android.permission.NFC_HANDOVER_STATUS',
                    'android.permission.NOTIFY_PENDING_SYSTEM_UPDATE',
                    'android.permission.OBSERVE_GRANT_REVOKE_PERMISSIONS',
                    'android.permission.OEM_UNLOCK_STATE',
                    'android.permission.OVERRIDE_WIFI_CONFIG',
                    'android.permission.PACKAGE_USAGE_STATS',
                    'android.permission.PACKAGE_VERIFICATION_AGENT',
                    'android.permission.PACKET_KEEPALIVE_OFFLOAD',
                    'android.permission.PEERS_MAC_ADDRESS',
                    'android.permission.PERFORM_CDMA_PROVISIONING',
                    'android.permission.PERFORM_SIM_ACTIVATION',
                    'android.permission.PERSISTENT_ACTIVITY',
                    'android.permission.PROCESS_CALLLOG_INFO',
                    'android.permission.PROCESS_OUTGOING_CALLS',
                    'android.permission.PROCESS_PHONE_ACCOUNT_REGISTRATION',
                    'android.permission.PROVIDE_TRUST_AGENT',
                    'android.permission.QUERY_DO_NOT_ASK_CREDENTIALS_ON_BOOT',
                    'android.permission.READ_BLOCKED_NUMBERS',
                    'android.permission.READ_CALENDAR',
                    'android.permission.READ_CALL_LOG',
                    'android.permission.READ_CONTACTS',
                    'android.permission.READ_DREAM_STATE',
                    'android.permission.READ_EXTERNAL_STORAGE',
                    'android.permission.READ_FRAME_BUFFER',
                    'android.permission.READ_HISTORY_BOOKMARKS',
                    'android.permission.READ_INPUT_STATE',
                    'android.permission.READ_INSTALL_SESSIONS',
                    'android.permission.READ_LOGS',
                    'android.permission.READ_NETWORK_USAGE_HISTORY',
                    'android.permission.READ_OEM_UNLOCK_STATE',
                    'android.permission.READ_PHONE_STATE',
                    'android.permission.READ_PRECISE_PHONE_STATE',
                    'android.permission.READ_PRIVILEGED_PHONE_STATE',
                    'android.permission.READ_PROFILE',
                    'android.permission.READ_SEARCH_INDEXABLES',
                    'android.permission.READ_SMS',
                    'android.permission.READ_SOCIAL_STREAM',
                    'android.permission.READ_SYNC_SETTINGS',
                    'android.permission.READ_SYNC_STATS',
                    'android.permission.READ_USER_DICTIONARY',
                    'android.permission.READ_WIFI_CREDENTIAL',
                    'android.permission.REAL_GET_TASKS',
                    'android.permission.REBOOT',
                    'android.permission.RECEIVE_BLUETOOTH_MAP',
                    'android.permission.RECEIVE_BOOT_COMPLETED',
                    'android.permission.RECEIVE_DATA_ACTIVITY_CHANGE',
                    'android.permission.RECEIVE_EMERGENCY_BROADCAST',
                    'android.permission.RECEIVE_MEDIA_RESOURCE_USAGE',
                    'android.permission.RECEIVE_MMS',
                    'android.permission.RECEIVE_SMS',
                    'android.permission.RECEIVE_STK_COMMANDS',
                    'android.permission.RECEIVE_WAP_PUSH',
                    'android.permission.RECEIVE_WIFI_CREDENTIAL_CHANGE',
                    'android.permission.RECORD_AUDIO',
                    'android.permission.RECOVERY',
                    'android.permission.REGISTER_CALL_PROVIDER',
                    'android.permission.REGISTER_CONNECTION_MANAGER',
                    'android.permission.REGISTER_SIM_SUBSCRIPTION',
                    'android.permission.REGISTER_WINDOW_MANAGER_LISTENERS',
                    'android.permission.REMOTE_AUDIO_PLAYBACK',
                    'android.permission.REMOVE_DRM_CERTIFICATES',
                    'android.permission.REMOVE_TASKS',
                    'android.permission.REORDER_TASKS',
                    'android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS',
                    'android.permission.REQUEST_INSTALL_PACKAGES',
                    'android.permission.RESET_FINGERPRINT_LOCKOUT',
                    'android.permission.RESET_SHORTCUT_MANAGER_THROTTLING',
                    'android.permission.RESTART_PACKAGES',
                    'android.permission.RETRIEVE_WINDOW_CONTENT',
                    'android.permission.RETRIEVE_WINDOW_TOKEN',
                    'android.permission.REVOKE_RUNTIME_PERMISSIONS',
                    'android.permission.SCORE_NETWORKS',
                    'android.permission.SEND_CALL_LOG_CHANGE',
                    'android.permission.SEND_DOWNLOAD_COMPLETED_INTENTS',
                    'android.permission.SEND_RESPOND_VIA_MESSAGE',
                    'android.permission.SEND_SMS',
                    'android.permission.SEND_SMS_NO_CONFIRMATION',
                    'android.permission.SERIAL_PORT',
                    'android.permission.SET_ACTIVITY_WATCHER',
                    'android.permission.SET_ALARM',
                    'android.permission.SET_ALWAYS',
                    'android.permission.SET_ALWAYS_FINISH',
                    'android.permission.SET_ANIMATION_SCALE',
                    'android.permission.SET_DEBUG_APP',
                    'android.permission.SET_INPUT_CALIBRATION',
                    'android.permission.SET_KEYBOARD_LAYOUT',
                    'android.permission.SET_ORIENTATION',
                    'android.permission.SET_POINTER_SPEED',
                    'android.permission.SET_PREFERRED_APPLICATIONS',
                    'android.permission.SET_PROCESS_LIMIT',
                    'android.permission.SET_SCREEN_COMPATIBILITY',
                    'android.permission.SET_TIME',
                    'android.permission.SET_TIME_ZONE',
                    'android.permission.SET_WALLPAPER',
                    'android.permission.SET_WALLPAPER_COMPONENT',
                    'android.permission.SET_WALLPAPER_HINTS',
                    'android.permission.SHUTDOWN',
                    'android.permission.SIGNAL_PERSISTENT_PROCESSES',
                    'android.permission.START_ANY_ACTIVITY',
                    'android.permission.START_PRINT_SERVICE_CONFIG_ACTIVITY',
                    'android.permission.START_TASKS_FROM_RECENTS',
                    'android.permission.STATUS_BAR',
                    'android.permission.STATUS_BAR_SERVICE',
                    'android.permission.STOP_APP_SWITCHES',
                    'android.permission.STORAGE_INTERNAL',
                    'android.permission.SUBSCRIBED_FEEDS_READ',
                    'android.permission.SUBSCRIBED_FEEDS_WRITE',
                    'android.permission.SUBSTITUTE_NOTIFICATION_APP_NAME',
                    'android.permission.SYSTEM_ALERT_WINDOW',
                    'android.permission.TABLET_MODE',
                    'android.permission.TEMPORARY_ENABLE_ACCESSIBILITY',
                    'android.permission.TETHER_PRIVILEGED',
                    'android.permission.TRANSMIT_IR',
                    'android.permission.TRUST_LISTENER',
                    'android.permission.TV_INPUT_HARDWARE',
                    'android.permission.TV_VIRTUAL_REMOTE_CONTROLLER',
                    'android.permission.UPDATE_APP_OPS_STATS',
                    'android.permission.UPDATE_CONFIG',
                    'android.permission.UPDATE_DEVICE_STATS',
                    'android.permission.UPDATE_LOCK',
                    'android.permission.UPDATE_LOCK_TASK_PACKAGES',
                    'android.permission.USER_ACTIVITY',
                    'android.permission.USE_CREDENTIALS',
                    'android.permission.USE_SIP',
                    'android.permission.VIBRATE',
                    'android.permission.WAKE_LOCK',
                    'android.permission.WRITE_APN_SETTINGS',
                    'android.permission.WRITE_BLOCKED_NUMBERS',
                    'android.permission.WRITE_CALENDAR',
                    'android.permission.WRITE_CALL_LOG',
                    'android.permission.WRITE_CONTACTS',
                    'android.permission.WRITE_DREAM_STATE',
                    'android.permission.WRITE_EXTERNAL_STORAGE',
                    'android.permission.WRITE_GSERVICES',
                    'android.permission.WRITE_HISTORY_BOOKMARKS',
                    'android.permission.WRITE_MEDIA_STORAGE',
                    'android.permission.WRITE_PROFILE',
                    'android.permission.WRITE_SECURE_SETTINGS',
                    'android.permission.WRITE_SETTING',
                    'android.permission.WRITE_SETTINGS',
                    'android.permission.WRITE_SMS',
                    'android.permission.WRITE_SOCIAL_STREAM',
                    'android.permission.WRITE_SYNC_SETTINGS',
                    'android.permission.WRITE_USER_DICTIONARY' ]

class Intent(object):
    """
    Representation of an Android Intent object in Python.

    An Python representation of an Intent can be built, and then converted into
    a Java representation using the buildIn() method to add context.
    """

    actions = [     'android.intent.action.MAIN',
                    'android.intent.action.VIEW',
                    'android.intent.action.ATTACH_DATA',
                    'android.intent.action.EDIT',
                    'android.intent.action.PICK',
                    'android.intent.action.CHOOSER',
                    'android.intent.action.GET_CONTENT',
                    'android.intent.action.DIAL',
                    'android.intent.action.CALL',
                    'android.intent.action.SEND',
                    'android.intent.action.SENDTO',
                    'android.intent.action.ANSWER',
                    'android.intent.action.INSERT',
                    'android.intent.action.DELETE',
                    'android.intent.action.RUN',
                    'android.intent.action.SYNC',
                    'android.intent.action.PICK_ACTIVITY',
                    'android.intent.action.SEARCH',
                    'android.intent.action.WEB_SEARCH',
                    'android.intent.action.FACTORY_TEST',
                    'android.intent.action.TIME_TICK',
                    'android.intent.action.TIME_CHANGED',
                    'android.intent.action.TIMEZONE_CHANGED',
                    'android.intent.action.BOOT_COMPLETED',
                    'android.intent.action.PACKAGE_ADDED',
                    'android.intent.action.PACKAGE_CHANGED',
                    'android.intent.action.PACKAGE_REMOVED',
                    'android.intent.action.PACKAGE_RESTARTED',
                    'android.intent.action.PACKAGE_DATA_CLEARED',
                    'android.intent.action.UID_REMOVED',
                    'android.intent.action.BATTERY_CHANGED',
                    'android.intent.action.ACTION_POWER_CONNECTED',
                    'android.intent.action.ACTION_POWER_DISCONNECTED',
                    'android.intent.action.ACTION_SHUTDOWN' ] # Last 3 are the exception to the rule
    categories = [  'android.intent.category.DEFAULT',
                    'android.intent.category.BROWSABLE',
                    'android.intent.category.TAB',
                    'android.intent.category.ALTERNATIVE',
                    'android.intent.category.SELECTED_ALTERNATIVE',
                    'android.intent.category.LAUNCHER',
                    'android.intent.category.INFO',
                    'android.intent.category.HOME',
                    'android.intent.category.PREFERENCE',
                    'android.intent.category.TEST',
                    'android.intent.category.CAR_DOCK',
                    'android.intent.category.DESK_DOCK',
                    'android.intent.category.LE_DESK_DOCK',
                    'android.intent.category.HE_DESK_DOCK',
                    'android.intent.category.CAR_MODE',
                    'android.intent.category.APP_MARKET' ]
    extra_keys = [  'android.intent.extra.ALARM_COUNT',
                    'android.intent.extra.BCC',
                    'android.intent.extra.CC',
                    'android.intent.extra.CHANGED_COMPONENT_NAME',
                    'android.intent.extra.DATA_REMOVED',
                    'android.intent.extra.DOCK_STATE',
                    'android.intent.extra.DOCK_STATE_HE_DESK',
                    'android.intent.extra.DOCK_STATE_LE_DESK',
                    'android.intent.extra.DOCK_STATE_CAR',
                    'android.intent.extra.DOCK_STATE_DESK',
                    'android.intent.extra.DOCK_STATE_UNDOCKED',
                    'android.intent.extra.DONT_KILL_APP',
                    'android.intent.extra.EMAIL',
                    'android.intent.extra.INITIAL_INTENTS',
                    'android.intent.extra.INTENT',
                    'android.intent.extra.KEY_EVENT',
                    'android.intent.extra.ORIGINATING_URI',
                    'android.intent.extra.PHONE_NUMBER',
                    'android.intent.extra.REFERRER',
                    'android.intent.extra.REMOTE_INTENT_TOKEN',
                    'android.intent.extra.REPLACING',
                    'android.intent.extra.SHORTCUT_ICON',
                    'android.intent.extra.SHORTCUT_ICON_RESOURCE',
                    'android.intent.extra.SHORTCUT_INTENT',
                    'android.intent.extra.STREAM',
                    'android.intent.extra.SHORTCUT_NAME',
                    'android.intent.extra.SUBJECT',
                    'android.intent.extra.TEMPLATE',
                    'android.intent.extra.TEXT',
                    'android.intent.extra.TITLE',
                    'android.intent.extra.UID' ]
    extra_types = [ 'boolean',
                    'byte',
                    'char',
                    'double',
                    'float',
                    'integer',
                    'long',
                    'parcelable',
                    'short',
                    'string',
                    'bytearray' ]
    flags = {       'ACTIVITY_BROUGHT_TO_FRONT': 0x00400000,
                    'ACTIVITY_CLEAR_TASK': 0x00008000,
                    'ACTIVITY_CLEAR_TOP': 0x04000000,
                    'ACTIVITY_CLEAR_WHEN_TASK_RESET': 0x00080000,
                    'ACTIVITY_EXCLUDE_FROM_RECENTS': 0x00800000,
                    'ACTIVITY_FORWARD_RESULT': 0x02000000,
                    'ACTIVITY_LAUNCHED_FROM_HISTORY': 0x00100000,
                    'ACTIVITY_MULTIPLE_TASK': 0x08000000,
                    'ACTIVITY_NEW_TASK': 0x10000000,
                    'ACTIVITY_NO_ANIMATION': 0x00010000,
                    'ACTIVITY_NO_HISTORY': 0x40000000,
                    'ACTIVITY_NO_USER_ACTION': 0x00040000,
                    'ACTIVITY_PREVIOUS_IS_TOP': 0x01000000,
                    'ACTIVITY_REORDER_TO_FRONT': 0x00020000,
                    'ACTIVITY_RESET_TASK_IF_NEEDED': 0x00200000,
                    'ACTIVITY_SINGLE_TOP': 0x20000000,
                    'ACTIVITY_TASK_ON_HOME': 0x00004000,
                    'FLAG_DEBUG_LOG_RESOLUTION': 0x00000008,
                    'FROM_BACKGROUND': 0x00000004,
                    'GRANT_READ_URI_PERMISSION': 0x00000001,
                    'GRANT_WRITE_URI_PERMISSION': 0x00000002,
                    'RECEIVER_REGISTERED_ONLY': 0x40000000 }
    
    usage = """    dz> run app.activity.start
                --action android.intent.action.VIEW
                --data-uri http://www.google.com
                --flags ACTIVITY_NEW_TASK

Last Modified: 2021-09-20
Credit: MWR InfoSecurity (@mwrlabs)
License: MWR Code License

optional arguments:
  -h, --help
  --action ACTION       specify the action to include in the Intent
  --category CATEGORY   specify the category to include in the Intent
  --component COMPONENT COMPONENT
                        specify the component name to include in the Intent
  --data-uri DATA_URI   specify a Uri to attach as data in the Intent
  --extra type key value
                        add an field to the Intent's extras bundle
  --flags FLAGS [FLAGS ...]
                        specify one-or-more flags to include in the Intent
  --mimetype MIMETYPE   specify the MIME type to send in the Intent"""

    def __init__(self, action=None, category=None, component=None,
        data_uri=None, extras=None, flags=None, mimetype=None):
        self.action = action
        self.category = category
        self.component = component
        self.data_uri = data_uri
        self.extras = extras
        self.flags = flags
        self.mimetype = mimetype

    @classmethod
    def addArgumentsTo(cls, parser):
        """
        Prepares an ArgumentParser object to allow a user to pass Intent
        arguments through a command-line interface.
        """

        parser.add_argument("--action", help="specify the action to include in the Intent")
        parser.add_argument("--category", nargs="+", help="specify the category to include in the Intent")
        parser.add_argument("--component", help="specify the component name to include in the Intent",
                            nargs=2, metavar=('PACKAGE', 'COMPONENT'))
        parser.add_argument("--data-uri", help="specify a Uri to attach as data in the Intent")
        parser.add_argument("--extra", action="append", default=[], 
                            dest="extras", nargs=3, help="add an field to the Intent's extras bundle", metavar=('TYPE', 'KEY', 'VALUE'))
        parser.add_argument("--flags", nargs='+', default=[], help="specify one-or-more flags to include in the Intent")
        parser.add_argument("--mimetype", help="specify the MIME type to send in the Intent")

    @classmethod
    def fromParser(cls, arguments):
        """
        Builds an Intent, given arguments parsed by an ArgumentParser that was
        previously initialised with addArgumentsTo().
        """

        return cls( action=arguments.action,
                    category=arguments.category,
                    component=arguments.component,
                    data_uri=arguments.data_uri,
                    extras=arguments.extras,
                    flags=arguments.flags,
                    mimetype=arguments.mimetype)
        
    @classmethod
    def get_completion_suggestions(cls, action, text, **kwargs):
        """
        Provide completion suggestions for Android Intents.
        """
        
        if action.dest == "action":
            return cls.actions
        elif action.dest == "category":
            return cls.categories
        elif action.dest == "component":
            pass
        elif action.dest == "data_uri":
            pass
        elif action.dest == "extras":
            if kwargs['idx'] == 0:
                return cls.extra_types
            elif kwargs['idx'] == 1:
                return cls.extra_keys
        elif action.dest == "flags":
            return cls.flags.keys()
        elif action.dest == "mimetype":
            pass

    def buildIn(self, module):
        """
        Convert a Python Intent representation into a Java Intent that can be
        used with reflection, by adding context.
        """

        intent = module.new("android.content.Intent")

        self.__add_action_to(intent, module)
        self.__add_categories_to(intent, module)
        self.__add_component_to(intent, module)
        self.__add_data_uri_to(intent, module)
        self.__add_extras_to(intent, module)
        self.__add_flags_to(intent, module)
        self.__add_type_to(intent, module)

        return intent

    def isValid(self):
        """
        Determine whether an Intent is valid: it must have an action or a
        component.
        """

        return self.action != None or self.component != None
    
    def __add_action_to(self, intent, context):
        """
        Set the ACTION of intent, iff we have a value to set.
        """
        
        if self.action != None:
            intent.setAction(self.action)
    
    def __add_categories_to(self, intent, context):
        """
        Set the CATEGORY of intent, iff we have a value to set.
        """
        
        if self.category != None:
            for category in self.category:
                intent.addCategory(category)
    
    def __add_component_to(self, intent, context):
        """
        Set the COMPONENT of intent, iff we have a value to set.
        """
        
        if self.component != None:
            com = context.new("android.content.ComponentName", *self.component)
            # pass the built ComponentName to the intent
            intent.setComponent(com)
    
    def __add_data_uri_to(self, intent, context):
        """
        Set the DATA of intent as a Uri, iff we have a value to set.
        """
        
        if self.data_uri != None:
            uri = context.klass("android.net.Uri")
            intent.setData(uri.parse(self.data_uri))
            
    def add_extra_to(self, extra, bundle, context):
        """
        Adds one Extra to an Intent/Bundle.
        """
        if extra[0] == "boolean":
            bundle.putBoolean(extra[1], context.arg(extra[2].lower().startswith("t"), obj_type="boolean"))
        elif extra[0] == "byte":
            bundle.putByte(extra[1], context.arg(int(extra[2]), obj_type="byte"))
        elif extra[0] == "char":
            bundle.putChar(extra[1], context.arg(int(extra[2]), obj_type="char"))
        elif extra[0] == "double":
            bundle.putDouble(extra[1], context.arg(float(extra[2]), obj_type="double"))
        elif extra[0] == "float":
            bundle.putFloat(extra[1], context.arg(float(extra[2]), obj_type="float"))
        elif extra[0] == "integer":
            bundle.putInt(extra[1], context.arg(int(extra[2]), obj_type="int"))
        elif extra[0] == "long":
            bundle.putLong(extra[1], context.arg(int(extra[2]), obj_type="long"))
        elif extra[0] == "short":
            bundle.putShort(extra[1], context.arg(int(extra[2]), obj_type="short"))
        elif extra[0] == "bytearray":
            wrapper = context.new("java.io.ByteArrayOutputStream")
            if isinstance(extra[2], str):
                #Allow the user to supply b64 or hex by wrapping
                #stuff in base64() or hex()
                b64_extra = re.match(r"^base64\(([-a-z0-9+\/]+=*)\)$", extra[2], flags=re.IGNORECASE)
                hex_extra = re.match(r"^hex\(([a-z0-9]+)\)$", extra[2], flags=re.IGNORECASE)
                if b64_extra != None:
                    extra[2] = base64.b64decode(b64_extra.group(1))
                elif hex_extra != None:
                    extra[2] = bytes.fromhex(hex_extra.group(1))
                # otherwise it's just a utf8 string
                else:
                    extra[2] = extra[2].encode('utf-8')
            for i in extra[2]:
                wrapper.write(i)
            bundle.putByteArray(extra[1],wrapper.toByteArray())
        elif extra[0] == "string":
            bundle.putString(extra[1], extra[2])
        elif extra[0] == "bundle":
            yaybundleyay = context.new("android.os.Bundle")
            yayUriArryay = extra[2].split(";")
            yayIntyay = len(yayUriArryay)
            while yayIntyay != 0:
                yayKeyyay = yayUriArryay[yayIntyay - 1].split("=")[0]
                yayValueyay = yayUriArryay[yayIntyay - 1].split("=")[1]
                if yayKeyyay.startswith("S."):
                    yaybundleyay.putString(yayKeyyay[2:], context.arg(str(yayValueyay), obj_type="string"))
                elif yayKeyyay.startswith("B."):
                    yaybundleyay.putBoolean(yayKeyyay[2:], context.arg(yayValueyay.lower().startswith("t"), obj_type="boolean"))
                elif yayKeyyay.startswith("b."):
                    yaybundleyay.putByte(yayKeyyay[2:], context.arg(int(yayValueyay), obj_type="byte"))
                elif yayKeyyay.startswith("c."):
                    yaybundleyay.putChar(yayKeyyay[2:], context.arg(int(yayValueyay), obj_type="char"))
                elif yayKeyyay.startswith("d."):
                    yaybundleyay.putDouble(yayKeyyay[2:], context.arg(float(yayValueyay), obj_type="double"))
                elif yayKeyyay.startswith("i."):
                    yaybundleyay.putInt(yayKeyyay[2:], context.arg(int(yayValueyay), obj_type="int"))
                elif yayKeyyay.startswith("f."):
                    yaybundleyay.putFloat(yayKeyyay[2:], context.arg(float(yayValueyay), obj_type="float"))
                elif yayKeyyay.startswith("l."):
                    yaybundleyay.putLong(yayKeyyay[2:], context.arg(int(yayValueyay), obj_type="long"))
                elif yayKeyyay.startswith("s."):
                    yaybundleyay.putShort(yayKeyyay[2:], context.arg(int(yayValueyay), obj_type="short"))

                yayIntyay = yayIntyay - 1

            bundle.putBundle(extra[1], yaybundleyay)

        elif extra[0] == "serializable":
            yaySerializableArryay = extra[2].split(";")
            yaybundleyay = []
            for key in yaySerializableArryay:
                if key.startswith("S."):
                    yaybundleyay.append(str(key[2:]))
                elif key.startswith("i."):
                    yaybundleyay.append(int(key[2:]))
                else:
                    yaybundleyay.append(key[2:])

            if len(yaybundleyay) == 1:
                bundle.putSerializable(extra[1], yaybundleyay[0])
            else:
                bundle.putSerializable(extra[1], yaybundleyay)
                
        elif extra[0] == "parcelablearraylist": # currently only supports URIs
            yayListyay = context.new("java.util.ArrayList")
            yayUriClassyay = context.klass("android.net.Uri")
            yayListyay.add(yayUriClassyay.parse(extra[2]))
            bundle.putParcelableArrayList("android.intent.extra.STREAM", yayListyay)
            
        elif extra[0] == "parcelable":
            if extra[2].lower().startswith("intent://"): # intent:// intent
                yayIntentClassYay = context.klass("android.content.Intent")

                # Fix to provide support for the old drozer intent format.
                if '#Intent' not in extra[2]:
                    if '#' not in extra[2]:
                        extra[2] += '#Intent;end;'
                    else:
                        extra[2] = re.sub('#(.*?);?$', '#Intent;\\1;end;', extra[2])

                if 'component=' in extra[2]:
                    component = re.findall('component=([^;]*)', extra[2])[0]
                    if '/' not in component:
                        if 'package=' not in extra[2]:
                            raise Exception("Please use 'component=[PACKAGE_NAME]/[COMPONENT_NAME]'")
                        package = re.findall('package=([^;]*)', extra[2])[0]
                        if package not in component:
                            raise Exception("Please use 'component=[PACKAGE_NAME]/[COMPONENT_NAME]'")
                        extra[2] = extra[2].replace(f'component={package}', f'component={package}/')

                yayParcelableIntentyay = yayIntentClassYay.parseUri(extra[2], 4)  # 4 = URI_ALLOW_UNSAFE for launchFlags
                bundle.putParcelable(extra[1], yayParcelableIntentyay)
            else:
                yayUriClassyay = context.klass("android.net.Uri")
                yayExtrayay = yayUriClassyay.parse(extra[2])
                bundle.putParcelable(extra[1], yayExtrayay)

        else:
            bundle.putParcelable(extra[1], extra[2])
        

    def __add_extras_to(self, intent, context):
        """
        Set the Extras of intent, iff we have a value to set.
        If any Extras already exist, clear them.
        """
        
        if self.extras != None:
            extras = context.new("android.os.Bundle")

            for extra in self.extras:
                self.add_extra_to(extra, extras, context)

            intent.putExtras(extras)
            
    def __add_flags_to(self, intent, context):
        """
        Set the FLAGS of intent, if we have a value to set.
        """

        if self.flags != None:
            intent.setFlags(self.__build_flags(self.flags))
    
    def __add_type_to(self, intent, context):
        """
        Set the TYPE of intent, if we have a value to set.
        """
        
        if self.mimetype != None:
            intent.setType(self.mimetype)
            
    def __build_flags(self, flags):
        """
        Take arguments passed as flags, and combine them to form the integer
        flag field to pass in an Intent.

        We can accept flags either as a key from the flags dictionary above,
        or in a binary format.
        """

        flag = 0x00000000

        for flag_spec in flags:
            if flag_spec.startswith("0x"):
                flag = flag | int(flag_spec[2:], 16) # support hexadecimal flags
            else:
                flag = flag | self.__class__.flags[flag_spec]

        return flag
        
