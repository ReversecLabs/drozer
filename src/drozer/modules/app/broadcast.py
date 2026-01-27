from xml.etree import ElementTree

from drozer import android
from drozer.modules import common, Module
from drozer.modules.common import loader
import time

class Info(Module, common.Filters, common.IntentFilter, common.PackageManager):

    name = "Get information about broadcast receivers"
    description = "Get information about exported broadcast receivers."
    examples = """Get receivers exported by the platform:

    dz> run app.broadcast.info -a android
    Package: android
      com.android.server.BootReceiver
        Permission: null
      com.android.server.updates.CertPinInstallReceiver
        Permission: null
      com.android.server.updates.IntentFirewallInstallReceiver
        Permission: null
      com.android.server.updates.SmsShortCodesInstallReceiver
        Permission: null
      com.android.server.updates.CarrierProvisioningUrlsInstallReceiver
        Permission: null
      com.android.server.updates.TZInfoInstallReceiver
        Permission: null
      com.android.server.updates.SELinuxPolicyInstallReceiver
        Permission: null
      com.android.server.MasterClearReceiver
        Permission: android.permission.MASTER_CLEAR"""
    author = ["MWR InfoSecurity (@mwrlabs)", "Luander (luander.r@samsung.com)"]
    date = "2012-11-06"
    license = "BSD (3 clause)"
    path = ["app", "broadcast"]
    permissions = ["com.reversec.dz.permissions.GET_CONTEXT"]

    def add_arguments(self, parser):
        parser.add_argument("-a", "--package", default=None, help="specify the package to inspect")
        parser.add_argument("-f", "--filter", default=None, help="specify filter conditions")
        parser.add_argument("-p", "--permission", default=None, help="specify permission conditions")
        parser.add_argument("-i", "--show-intent-filters", action="store_true", default=False, help="specify whether to include intent filters")
        parser.add_argument("-u", "--unexported", action="store_true", default=False, help="include receivers that are not exported")
        parser.add_argument("-v", "--verbose", action="store_true", default=False, help="be verbose")

    def execute(self, arguments):
        if arguments.package == None:
            for package in self.packageManager().getPackages(common.PackageManager.GET_RECEIVERS | common.PackageManager.GET_PERMISSIONS):
                self.__get_receivers(arguments, package)
        else:
            package = self.packageManager().getPackageInfo(arguments.package, common.PackageManager.GET_RECEIVERS | common.PackageManager.GET_PERMISSIONS)

            self.__get_receivers(arguments, package)
            
    def get_completion_suggestions(self, action, text, **kwargs):
        if action.dest == "permission":
            return ["null"] + android.permissions

    def __get_receivers(self, arguments, package):
        receivers = self.match_filter(package.receivers, 'name', arguments.filter)
        receivers = self.match_filter(receivers, 'permission', arguments.permission)

        exported_receivers = self.match_filter(receivers, 'exported', True)
        hidden_receivers = self.match_filter(receivers, 'exported', False)

        if len(exported_receivers) > 0 or arguments.unexported and len(receivers) > 0:
            self.stdout.write("Package: %s\n" % package.packageName)

            if not arguments.unexported:
                for receiver in exported_receivers:
                    self.__print_receiver(package, receiver, "  ", arguments.show_intent_filters)
            else:
                self.stdout.write("  Exported Receivers:\n")
                for receiver in exported_receivers:
                    self.__print_receiver(package, receiver, "    ", arguments.show_intent_filters)
                self.stdout.write("  Hidden Receivers:\n")
                for receiver in hidden_receivers:
                    self.__print_receiver(package, receiver, "    ", arguments.show_intent_filters)
            self.stdout.write("\n")
        elif arguments.package or arguments.verbose:
            self.stdout.write("Package: %s\n" % package.packageName)
            self.stdout.write("  No matching receivers.\n\n")

    def __print_receiver(self, package, receiver, prefix, include_intent_filters=False):
        self.stdout.write("%s%s\n" % (prefix, receiver.name))
            
        if include_intent_filters:
            intent_filters = self.find_intent_filters(receiver, 'receiver')
            
            if len(intent_filters) > 0:
                for intent_filter in intent_filters:
                    self.stdout.write("%s  Intent Filter:\n" % (prefix))
                    if len(intent_filter.actions) > 0:
                        self.stdout.write("%s    Actions:\n" % (prefix))
                        for action in intent_filter.actions:
                            self.stdout.write("%s      - %s\n" % (prefix, action))
                    if len(intent_filter.categories) > 0:
                        self.stdout.write("%s    Categories:\n" % (prefix))
                        for category in intent_filter.categories:
                            self.stdout.write("%s      - %s\n" % (prefix, category))
                    if len(intent_filter.datas) > 0:
                        self.stdout.write("%s    Data:\n" % (prefix))
                        for data in intent_filter.datas:
                            self.stdout.write("%s      - %s\n" % (prefix, data))
        self.stdout.write("%s  Permission: %s\n" % (prefix, receiver.permission))

class Send(Module):

    name = "Send broadcast using an intent"
    description = "Sends an intent to broadcast receivers."
    examples = """Attempt to send the BOOT_COMPLETED broadcast message:

    dz> run app.broadcast.send
                --action android.intent.action.BOOT_COMPLETED
    java.lang.SecurityException: Permission Denial: not allowed to send broadcast android.intent.action.BOOT_COMPLETED from pid=955, uid=10044

For more information on how to formulate an Intent, type 'help intents'."""
    author = "MWR InfoSecurity (@mwrlabs)"
    date = "2012-11-06"
    license = "BSD (3 clause)"
    path = ["app", "broadcast"]
    permissions = ["com.reversec.dz.permissions.GET_CONTEXT"]

    def add_arguments(self, parser):
        android.Intent.addArgumentsTo(parser)

    def execute(self, arguments):
        intent = android.Intent.fromParser(arguments)

        if intent.isValid():
            self.getContext().sendBroadcast(intent.buildIn(self))
        else:
            self.stderr.write("invalid intent: one of action or component must be set")
    
    def get_completion_suggestions(self, action, text, **kwargs):
        if action.dest in ["action", "category", "component", "data_uri",
                           "extras", "flags", "mimetype"]:
            return android.Intent.get_completion_suggestions(action, text, **kwargs)

class Sniff(Module, loader.ClassLoader):

    name = "Register a broadcast receiver that can sniff particular intents"
    description = "Register a broadcast receiver that can sniff particular intents"
    examples = """
    dz> run app.broadcast.sniff --action android.intent.action.BATTERY_CHANGED
    [*] Broadcast receiver registered to sniff matching intents
    [*] Output is updated once a second. Press Control+C to exit.

    Action: android.intent.action.BATTERY_CHANGED
    Raw: Intent { act=android.intent.action.BATTERY_CHANGED flg=0x60000010 (has extras) }
    Extra: technology=Li-ion (java.lang.String)
    Extra: icon-small=17303411 (java.lang.Integer)
    Extra: health=2 (java.lang.Integer)
    Extra: online=4 (java.lang.Integer)
    Extra: status=2 (java.lang.Integer)
    Extra: plugged=2 (java.lang.Integer)
    Extra: present=true (java.lang.Boolean)
    Extra: level=80 (java.lang.Integer)
    Extra: scale=100 (java.lang.Integer)
    Extra: temperature=280 (java.lang.Integer)
    Extra: current_avg=460 (java.lang.Integer)
    Extra: voltage=4151 (java.lang.Integer)
    Extra: charge_type=1 (java.lang.Integer)
    Extra: invalid_charger=0 (java.lang.Integer)"""
    author = "Tyrone (@mwrlabs)"
    date = "2014-06-27"
    license = "BSD (3 clause)"
    path = ["app", "broadcast"]
    permissions = ["com.reversec.dz.permissions.GET_CONTEXT"]

    def add_arguments(self, parser):
        parser.add_argument("--action", help="specify the action to include in the Intent Filter")
        parser.add_argument("--category", nargs="+", help="specify the category to include in the Intent Filter")
        parser.add_argument("--data-authority", nargs=2, metavar=('HOST', 'PORT'), help="specify the data authority to match against in the Intent Filter")
        parser.add_argument("--data-path", nargs=2, metavar=('PATH', 'TYPE'), help="specify the data path to match against in the Intent Filter")
        parser.add_argument("--data-scheme", nargs="+", help="specify the data scheme to match against in the Intent Filter")
        parser.add_argument("--data-type", nargs="+", help="specify the data type to match against in the Intent Filter")

    def execute(self, arguments):

        cl = self.loadClass("common/RegisterReceiver.apk", "RegisterReceiver")
        broadcast = self.new(cl)

        if arguments.action is not None:
            intentFilter = self._createIntentFilter(arguments)
            broadcast.register(self.getContext(), intentFilter)
            self.stdout.write("[*] Broadcast receiver registered to sniff matching intents\n")
        else:
            self.stdout.write("[-] No broadcast receiver registered. However, this will still receive intents from previously registered receivers.\n")

        self.stdout.write("[*] Output is updated once a second. Press Control+C to exit.\n\n") 
        while (True):
            output = broadcast.getOutput()
            if (str(output) == ""):
                time.sleep(1)
            else:
                self.stdout.write(str(output))
            
    def _createIntentFilter(self, arguments):

        tmp = self.new("android.content.IntentFilter")

        if arguments.action is not None:
            tmp.addAction(arguments.action)    

        if arguments.category is not None:
            for cat in arguments.category:
                tmp.addCategory(cat)

        if arguments.data_scheme is not None:
            for ds in arguments.data_scheme:
                tmp.addDataScheme(ds)

        if arguments.data_type is not None:
            for dt in arguments.data_type:
                tmp.addDataType(dt)

        if arguments.data_authority is not None:
            for da in arguments.data_authority:
                tmp.addDataAuthority(da[0], da[1])

        if arguments.data_path is not None:
            for dp in arguments.data_path:
                tmp.addDataPath(dp[0], dp[1])

        return tmp
