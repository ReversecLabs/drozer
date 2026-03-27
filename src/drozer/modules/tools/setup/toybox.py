from drozer.modules import common, Module

class ToyBox(Module, common.ToyBox, common.Shell):

	name = "Install Toybox."
	description = """Installs Toybox on the Agent.

Toybox provides a number of *nix utilities that are missing from Android. Some modules require Toybox to be installed.

Typically, you require root access to the device to install Toybox. drozer can install it from its restrictive context. You can then use 'toybox' in the when executing shell commands from drozer to use it."""
	examples = ""
	author = ["Tyrone (@mwrlabs)", "Thomas Cross (https://github.com/ThomasCross)"]
	date = "2025-06-24"
	license = "BSD (3 clause)"
	path = ["tools", "setup"]

	def execute(self, arguments):
		if (self.isToyBoxInstalled() == True):
			self.stdout.write("ToyBox is already installed.\n")

		else:
			arch = str(self.klass("android.os.SystemProperties").get("ro.product.cpu.abi"))
			if arch.startswith("armeabi"): 
				if self.installToyBox(arch="armeabi"):
					self.stdout.write("ToyBox installed " + self.toyboxPath() + "\n")
				else:
					self.stdout.write("ToyBox installation failed.\n")
		
			elif arch.startswith("arm64"):
				if self.installToyBox(arch="arm64"):
					self.stdout.write("ToyBox installed " + self.toyboxPath() + "\n")
				else:
					self.stdout.write("ToyBox installation failed.\n")

			elif arch.startswith("x86"):
				if self.installToyBox(arch="x86"):
					self.stdout.write("ToyBox installed " + self.toyboxPath() + "\n")
				else:
					self.stdout.write("ToyBox installation failed.\n")
			elif arch.startswith("x86_64"):
				if self.installToyBox(arch="x86_64"):
					self.stdout.write("ToyBox installed " + self.toyboxPath() + "\n")
				else:
					self.stdout.write("ToyBox installation failed.\n")
			else: 
				self.stdout.write("Unsupported CPU architecture. Supported architectures are arm, arm64, x86 and x86_64.\n")
