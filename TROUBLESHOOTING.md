# drozer Troubleshooting Guide

This document provides solutions to common issues encountered when using drozer.

## Table of Contents

- [Android 10+ Background Execution Limitations](#android-10-background-execution-limitations)
- [Connection Issues](#connection-issues)
- [Agent Installation Problems](#agent-installation-problems)

## Android 10+ Background Execution Limitations

### Problem Description

When testing applications on Android 10 (API level 29) or later, you may experience issues where drozer commands execute successfully but produce no visible results. Common symptoms include:

- Commands like `run app.activity.start` complete without errors but don't launch the target activity
- Activity starts work when the drozer Agent app is in the foreground
- Activity starts fail silently when the drozer Agent app is in the background
- ADB commands for the same operations work regardless of Agent state

### Root Cause

Starting with Android 10, Google introduced [background activity start restrictions](https://developer.android.com/guide/components/activities/background-starts) to improve user experience and security. These restrictions prevent background apps from starting activities unless they meet specific exemption criteria.

The current drozer Agent is designed as a "vanilla" Android application without special privileges. This design choice allows it to:
- Simulate real-world attack scenarios
- Evaluate devices from the perspective of a standard app
- Remain installable through normal channels

However, this also means the Agent is subject to Android's background execution restrictions when not in the foreground.

### Workarounds

#### Option 1: Keep Agent in Foreground (Recommended)

The simplest workaround is to keep the drozer Agent app visible on the device screen during testing:

1. Launch the drozer Agent app on your test device
2. Enable the embedded server or configure connection
3. **Keep the Agent visible** - don't switch to other apps or the home screen
4. Execute your drozer commands from the console

This ensures the Agent remains in the foreground and can execute all commands without restriction.

#### Option 2: Use ADB for Activity Starts

For operations that specifically require starting activities while testing other aspects with drozer:

```shell
# Use drozer for reconnaissance
dz> run app.activity.info -a com.example.targetapp

# Use adb to start activities
$ adb shell am start -n com.example.targetapp/.SomeActivity
```

This hybrid approach leverages drozer's powerful analysis capabilities while using ADB for operations affected by background restrictions.

#### Option 3: Periodic Agent Focus

For longer testing sessions where keeping the Agent constantly visible is impractical:

1. Switch to the drozer Agent app before executing commands that start activities
2. Execute the command
3. Observe the results
4. Switch back to drozer Agent before the next sensitive command

While not ideal for automated workflows, this works well for manual exploratory testing.

### Future Solutions

The drozer project is working on long-term solutions to this limitation:

1. **Foreground Service Implementation**: Modifying the Agent to run as a foreground service, which would grant it exemption from background start restrictions. This requires:
   - Adding a persistent notification
   - Potentially requesting `SYSTEM_ALERT_WINDOW` permission
   - See [drozer-agent PR #19](https://github.com/ReversecLabs/drozer-agent/pull/19) for work in progress

2. **Multiple Agent Variants**: Providing different Agent builds for different testing scenarios:
   - **Vanilla Agent**: Current behavior, minimal permissions (for app store-like testing)
   - **Privileged Agent**: Foreground service, additional permissions (for comprehensive testing)
   - **Custom Agent Builder**: Build agents with specific permission sets for specialized testing

Track progress on these solutions:
- [drozer-agent Issue #15](https://github.com/ReversecLabs/drozer-agent/issues/15)
- [drozer-agent PR #19](https://github.com/ReversecLabs/drozer-agent/pull/19)
- [drozer PR #465](https://github.com/FSecureLABS/drozer/pull/465)
- [drozer Issue #478](https://github.com/FSecureLABS/drozer/issues/478)

### Contributing

If you're interested in helping implement these solutions, contributions are welcome! The foreground service implementation is partially complete and needs:
- Code cleanup and testing
- Documentation updates
- Integration with the agent builder

See the [Contributing Guide](https://github.com/ReversecLabs/drozer/blob/develop/CONTRIBUTING.md) for more information.

## Connection Issues

### Agent Server Won't Start

If the embedded server in the drozer Agent fails to start:

1. Check that port 31415 is not already in use:
   ```shell
   adb shell netstat -an | grep 31415
   ```

2. Try restarting the Agent app

3. Check Android logs for errors:
   ```shell
   adb logcat | grep -i drozer
   ```

### Cannot Connect to Agent

If `drozer console connect` fails:

1. **Network Connection**: Verify the device IP address and network connectivity
   ```shell
   ping <device-ip>
   ```

2. **USB Connection**: Ensure ADB port forwarding is active
   ```shell
   adb forward tcp:31415 tcp:31415
   ```

3. **Firewall**: Check that firewall rules allow connections on port 31415

4. **Agent Status**: Verify the Agent's embedded server is enabled and shows "Server Enabled" status

## Agent Installation Problems

### Installation Fails

If `adb install drozer-agent.apk` fails:

1. **Enable USB Debugging**: Ensure USB debugging is enabled in Developer Options

2. **Device Authorization**: Accept the USB debugging prompt on the device

3. **Storage Space**: Verify sufficient storage space is available

4. **ADB Connection**: Confirm the device appears in `adb devices`

5. **Existing Installation**: If updating, try uninstalling first:
   ```shell
   adb uninstall com.WithSecure.dz
   ```

### Agent Crashes on Launch

If the Agent app crashes immediately:

1. Check Android version compatibility (minimum Android 5.0)

2. Review crash logs:
   ```shell
   adb logcat *:E | grep -A 20 'AndroidRuntime'
   ```

3. Try clearing app data:
   ```shell
   adb shell pm clear com.WithSecure.dz
   ```

4. Verify the APK is not corrupted by re-downloading

## Additional Resources

- [drozer User Guide](https://labs.reversec.com/tools/drozer/)
- [drozer GitHub Repository](https://github.com/ReversecLabs/drozer)
- [drozer-agent GitHub Repository](https://github.com/ReversecLabs/drozer-agent)
- [Android Background Execution Limits](https://developer.android.com/guide/components/activities/background-starts)

## Getting Help

If you encounter issues not covered in this guide:

1. Search existing [GitHub Issues](https://github.com/ReversecLabs/drozer/issues)
2. Check the [Discussions](https://github.com/ReversecLabs/drozer/discussions) section
3. Open a new issue with:
   - drozer version (`drozer --version`)
   - Android version and device model
   - Complete error messages
   - Steps to reproduce the issue
