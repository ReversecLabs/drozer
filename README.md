# drozer

drozer is a security testing framework for Android.

drozer allows you to search for security vulnerabilities in apps and devices by assuming the role of an app and interacting with the Android Runtime, other apps' IPC endpoints and the underlying OS.

drozer provides tools to help you use, share and understand public Android exploits.

drozer is open source software, maintained by WithSecure, and can be downloaded from: [https://labs.withsecure.com/tools/drozer/](https://labs.withsecure.com/tools/drozer/)

## NOTE

This is an BETA release of a rewritten drozer version; this version is updated to support python3.

## Docker Container

To help with making sure drozer can be run on all systems, a Docker container was created that has a working build of drozer.

* The Docker container and basic setup instructions can be found [here](https://hub.docker.com/r/withsecurelabs/drozer).
* Instructions on building your own Docker container can be found [here](https://github.com/WithSecureLabs/drozer/tree/develop/docker).

## Manual Building and Installation

### Software pre-requisites

1. [Python3.8](https://www.python.org/downloads/)
2. [Protobuf](https://pypi.python.org/pypi/protobuf) 4.25.2 or greater
3. [Pyopenssl](https://pypi.python.org/pypi/pyOpenSSL) 22.0.0 or greater
4. [Twisted](https://pypi.python.org/pypi/Twisted) 18.9.0 or greater
4. [Distro](https://pypi.org/project/distro/) 1.8.0 or greater
5. [Java Development Kit](https://adoptopenjdk.net/releases.html) 11 or greater

### Installing

You can use `pip` or `pipx` (preferably, if available) to install the latest release of drozer from PyPI:

```shell
pipx install drozer
```

Alternatively, you can download individual [releases](https://github.com/WithSecureLabs/drozer/releases/) from GitHub and run:

```shell
pipx install ./drozer-*.whl
```

If you haven't already, consider running:
```shell
pipx ensurepath
```

to ensure `pipx`-installed packages appear in your `PATH`

## Building

To build drozer from source you can run.

```shell
git clone https://github.com/WithSecureLabs/drozer.git
cd drozer
pip install .
```

To build the Android native components against a specific SDK you can set the `ANDROID_SDK` environment variable to the path. For example:

**Linux/macOS:**
```shell
export ANDROID_SDK=/home/drozerUser/Android/Sdk/platforms/android-34/android.jar
```

**Windows - PowerShell:**
```powershell
New-Item -Path Env:\ANDROID_SDK -Value 'C:\Users\drozerUser\AppData\Local\Android\sdk\platforms\android-34\android.jar'
```

**Windows - cmd:**
```cmd
set ANDROID_SDK = "C:\Users\drozerUser\AppData\Local\Android\sdk\platforms\android-34\android.jar"
```

 The location of the `d8` tool used can also be changed by setting `D8`.

## Usage

### Installing the Agent

drozer can be installed using Android Debug Bridge (adb).

Download the latest drozer Agent [here](https://github.com/WithSecureLabs/drozer-agent/releases/latest).

Or create a custom agent with
```
drozer agent set-apk --latest
drozer agent interactive
```
Then install with
```shell
adb install drozer-agent.apk
```

### Setup for session

You should now have the drozer Console installed on your PC, and the Agent running on your test device. Now, you need to connect the two and you’re ready to start exploring.

We will use the server embedded in the drozer Agent to do this. First, launch the Agent, select the "Embedded Server" option and tap "Enable" to start the server. You should see a notification that the server has started. 

Then, follow one of the options below.

#### Option 1: Connect to the phone via network

By default, the drozer Agent listens for incoming TCP connections on all interfaces on port 31415. In order to connect to the Agent, run the following command:

```
drozer console connect --server <phone's IP address>
```

If you are using the Docker container, the equivalent command would be:

```
docker run --net host -it withsecurelabs/drozer console connect --server <phone's IP address>
```

#### Option 2: Connect to the phone via USB

In some scenarios, connecting to the device over the network may not be viable. In these scenarios, we can leverage `adb`'s port-forwarding capabilities to establish a connection over USB.

First, you need to set up a suitable port forward so that your PC can connect to a TCP socket opened by the Agent inside the emulator, or on the device. By default, drozer uses port 31415

```shell
adb forward tcp:31415 tcp:31415
```

You can now connect to the drozer Agent by connecting to `localhost` (or simply not specifying the target IP)

```shell
drozer console connect
```

### Confirming a successful connection

You should be presented with a drozer command prompt:

```
Selecting ebe9fcc0c47b28da (Google sdk_gphone64_x86_64 12)

            ..                    ..:.
           ..o..                  .r..
            ..a..  . ....... .  ..nd
              ro..idsnemesisand..pr
              .otectorandroidsneme.
           .,sisandprotectorandroids+.
         ..nemesisandprotectorandroidsn:.
        .emesisandprotectorandroidsnemes..
      ..isandp,..,rotecyayandro,..,idsnem.
      .isisandp..rotectorandroid..snemisis.
      ,andprotectorandroidsnemisisandprotec.
     .torandroidsnemesisandprotectorandroid.
     .snemisisandprotectorandroidsnemesisan:
     .dprotectorandroidsnemesisandprotector.

drozer Console (v3.0.0)
dz>
```
The prompt confirms the Android ID of the device you have connected to, along with the manufacturer, model and Android software version.

You are now ready to start exploring the device.

### Command Reference

| Command        | Description           |
| ------------- |:-------------|
| run  | Executes a drozer module
| list | Show a list of all drozer modules that can be executed in the current session. This hides modules that you do not have suitable permissions to run. | 
| shell | Start an interactive Linux shell on the device, in the context of the Agent process. | 
| cd | Mounts a particular namespace as the root of session, to avoid having to repeatedly type the full name of a module. | 
| clean | Remove temporary files stored by drozer on the Android device. | 
| contributors | Displays a list of people who have contributed to the drozer framework and modules in use on your system. | 
| echo | Print text to the console. | 
| exit | Terminate the drozer session. | 
| help | Display help about a particular command or module. | 
| load | Load a file containing drozer commands, and execute them in sequence. | 
| module | Find and install additional drozer modules from the Internet. | 
| permissions | Display a list of the permissions granted to the drozer Agent. | 
| set | Store a value in a variable that will be passed as an environment variable to any Linux shells spawned by drozer. | 
| unset | Remove a named variable that drozer passes to any Linux shells that it spawns. | 

## License

drozer is released under a 3-clause BSD License. See LICENSE for full details.

## Contacting the Project

drozer is Open Source software, made great by contributions from the community.

For full source code, to report bugs, suggest features and contribute patches please see our Github project:

  <https://github.com/WithSecureLabs/drozer>

Bug reports, feature requests, comments and questions can be submitted [here](https://github.com/WithSecureLabs/drozer/issues).
