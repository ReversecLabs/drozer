from drozer.modules import common, Module

class MinimalSu(Module, common.SuperUser, common.Shell):

    name = "Prepare 'minimal-su' binary installation on the device."
    description = """Prepares 'minimal-su' binary installation files on the device in order to provide access to a root shell on demand.

This binary provides drozer the ability to maintain access to a root shell on the device after obtaining a temporary root shell via the use of an exploit. Just type `su` from a shell to get a root shell.

WARNING: This minimal version of the su binary is completely unprotected, meaning that any application on the device can obtain a root shell without any user prompting.
"""
    examples = """
    dz> run tools.setup.minimalsu
    [*] Uploaded minimal-su
    [*] Uploaded install-minimal-su.sh
    [*] chmod 770 /data/data/com.reversec.dz/install-minimal-su.sh
    [*] Ready! Execute /data/data/com.reversec.dz/install-minimal-su.sh from root context to install su
    
    ...insert root exploit here...
    u0_a95@android:/data/data/com.reversec.dz # /data/data/com.reversec.dz/install-minimal-su.sh
    Done. You can now use `su` from a shell.
    u0_a95@android:/data/data/com.reversec.dz # exit
    u0_a95@android:/data/data/com.reversec.dz $ su
    u0_a95@android:/data/data/com.reversec.dz #
    """
    author = "Tyrone (@mwrlabs)"
    date = "2013-12-12"
    license = "BSD (3 clause)"
    path = ["tools", "setup"]

    def execute(self, arguments):
        
        # Check for existence of any su binaries
        if self.isAnySuInstalled():
            self.stdout.write("[!] A version of su is already installed\n")

        # ARCH check
        if "ARM" not in str(self.klass('java.lang.System').getProperty("os.arch")).upper():
            response = input("[-] Unsupported CPU architecture - ARM only. Continue anyway (y/n)? ")
            if "Y" not in response.upper():
                return

        # Android 4.3 >= check
        if self.klass("android.os.Build$VERSION").SDK_INT >= 18:
            self.stdout.write("[-] This module is not supported on Android 4.3 and above yet. This is due to security changes in Android that mount the /system partition as nosuid for processes spawned by zygote.\n")
            return
        
        # Upload su binary
        if self.uploadMinimalSu():
            self.stdout.write("[+] Uploaded minimal-su\n")
        else:
            self.stdout.write("[-] Upload failed (minimal-su) - aborting\n")
            return
        
        # Upload install-minimal-su.sh    
        if self.uploadMinimalSuInstallScript():
            self.stdout.write("[+] Uploaded install-minimal-su.sh\n")
            self.stdout.write("[+] chmod 770 %s/install-minimal-su.sh\n" % self.workingDir())
        else:
            self.stdout.write("[-] Upload failed (install-minimal-su.sh) - aborting\n")
            return
        
        # Ready to be used from root context
        self.stdout.write("[+] Ready! Execute %s/install-minimal-su.sh from root context to install minimal-su\n" % self.workingDir())

