# Drozer Programmatic API

This document describes how to use drozer programmatically from Python scripts to run modules and capture their output.

## Overview

The Programmatic API allows you to:
- Run drozer modules from Python scripts
- Capture module output programmatically
- Handle errors and exceptions gracefully
- Integrate drozer into automated security testing workflows

## Quick Start

### Basic Usage

```python
from drozer.api import ProgrammaticSession
from drozer.connector import ServerConnector
from pysolar.api.protobuf_pb2 import Message

# 1. Connect to drozer server
server = ServerConnector()
server.connect(host="localhost", port=31415)

# 2. Start a session with a device
response = server.startSession("device_id", password=None)

if response.type == Message.SYSTEM_RESPONSE and \
   response.system_response.status == Message.SystemResponse.SUCCESS:
    session_id = response.system_response.session_id

    # 3. Create programmatic session
    session = ProgrammaticSession(server, session_id)

    try:
        # 4. Run a module
        result = session.run_module("app.package.list", ["-f", "browser"])

        # 5. Check results
        if result.success:
            print("Output:")
            print(result.output)
        else:
            print("Error:")
            print(result.errors)
    finally:
        # 6. Cleanup
        session.close()
        server.close()
else:
    print("Failed to start session:", response.system_response.error_message)
```

## API Reference

### ProgrammaticSession

The main class for running drozer modules programmatically.

#### Constructor

```python
ProgrammaticSession(server, session_id, arguments=None)
```

**Parameters:**
- `server`: ServerConnector instance
- `session_id`: Session ID from `server.startSession()`
- `arguments` (optional): Custom arguments object (uses sensible defaults if not provided)

#### Methods

##### run_module()

Run a drozer module and capture its output.

```python
result = session.run_module(module_name, args=None)
```

**Parameters:**
- `module_name` (str): Full module name (e.g., "app.package.list")
- `args` (str or list, optional): Module arguments
  - String: `"-f browser"`
  - List: `["-f", "browser"]`
  - None/Empty: `[]`

**Returns:** `ModuleResult` object

**Example:**
```python
# List packages containing "browser"
result = session.run_module("app.package.list", ["-f", "browser"])

# Get package info
result = session.run_module("app.package.info", "-a com.android.browser")

# No arguments
result = session.run_module("app.package.list")
```

##### list_modules()

List available drozer modules.

```python
modules = session.list_modules(filter=None)
```

**Parameters:**
- `filter` (str, optional): Filter string to search in module names

**Returns:** List of module names

**Example:**
```python
# List all modules
all_modules = session.list_modules()

# List only package-related modules
pkg_modules = session.list_modules("package")

for module in pkg_modules:
    print(module)
```

##### has_context()

Check if the session has application context.

```python
has_ctx = session.has_context()
```

**Returns:** `bool` - True if session has context

##### permissions()

Get available permissions in the session.

```python
perms = session.permissions()
```

**Returns:** List of permission strings

##### close()

Close the session and cleanup resources. Always call this when done.

```python
session.close()
```

### ModuleResult

Represents the result of a module execution.

#### Attributes

- `output` (str): Captured stdout from the module
- `errors` (str): Captured stderr from the module
- `return_value` (Any): Value returned by module's `execute()` method
- `exception` (Exception or None): Exception raised during execution, if any
- `success` (bool): True if execution completed without exceptions

#### Example

```python
result = session.run_module("app.package.list", ["-f", "browser"])

if result.success:
    print("Module executed successfully")
    print(f"Output length: {len(result.output)}")
    print(f"Return value: {result.return_value}")
else:
    print("Module failed")
    print(f"Exception: {result.exception}")
    print(f"Errors: {result.errors}")
```

## Complete Examples

### Example 1: List All Installed Packages

```python
from drozer.api import ProgrammaticSession
from drozer.connector import ServerConnector
from pysolar.api.protobuf_pb2 import Message

def list_packages(device_id):
    """List all installed packages on a device."""
    server = ServerConnector()
    server.connect(host="localhost", port=31415)

    response = server.startSession(device_id, password=None)
    if response.system_response.status != Message.SystemResponse.SUCCESS:
        print(f"Failed to start session: {response.system_response.error_message}")
        return None

    session_id = response.system_response.session_id
    session = ProgrammaticSession(server, session_id)

    try:
        result = session.run_module("app.package.list")

        if result.success:
            packages = [line.strip() for line in result.output.split('\n') if line.strip()]
            return packages
        else:
            print(f"Error: {result.errors}")
            return None
    finally:
        session.close()
        server.close()

# Usage
packages = list_packages("your_device_id")
if packages:
    print(f"Found {len(packages)} packages:")
    for pkg in packages[:10]:  # Show first 10
        print(f"  - {pkg}")
```

### Example 2: Analyze Package Attack Surface

```python
from drozer.api import ProgrammaticSession
from drozer.connector import ServerConnector
from pysolar.api.protobuf_pb2 import Message

def analyze_attack_surface(device_id, package_name):
    """Analyze the attack surface of a package."""
    server = ServerConnector()
    server.connect(host="localhost", port=31415)

    response = server.startSession(device_id, password=None)
    if response.system_response.status != Message.SystemResponse.SUCCESS:
        print(f"Failed to start session: {response.system_response.error_message}")
        return None

    session_id = response.system_response.session_id
    session = ProgrammaticSession(server, session_id)

    try:
        result = session.run_module("app.package.attacksurface", package_name)

        if result.success:
            return {
                'package': package_name,
                'attack_surface': result.output,
                'raw_output': result.output
            }
        else:
            return {
                'package': package_name,
                'error': result.errors
            }
    finally:
        session.close()
        server.close()

# Usage
analysis = analyze_attack_surface("your_device_id", "com.android.browser")
if 'error' not in analysis:
    print(f"Attack Surface for {analysis['package']}:")
    print(analysis['attack_surface'])
else:
    print(f"Error: {analysis['error']}")
```

### Example 3: Automated Security Scan

```python
from drozer.api import ProgrammaticSession
from drozer.connector import ServerConnector
from pysolar.api.protobuf_pb2 import Message
import json

def automated_security_scan(device_id, output_file="scan_results.json"):
    """
    Run automated security scan on all installed packages.
    """
    server = ServerConnector()
    server.connect(host="localhost", port=31415)

    response = server.startSession(device_id, password=None)
    if response.system_response.status != Message.SystemResponse.SUCCESS:
        print(f"Failed to start session: {response.system_response.error_message}")
        return

    session_id = response.system_response.session_id
    session = ProgrammaticSession(server, session_id)

    results = {
        'device_id': device_id,
        'scans': []
    }

    try:
        # Get list of packages
        pkg_result = session.run_module("app.package.list")
        if not pkg_result.success:
            print(f"Failed to list packages: {pkg_result.errors}")
            return

        packages = [line.strip() for line in pkg_result.output.split('\n') if line.strip()]
        print(f"Scanning {len(packages)} packages...")

        # Scan each package
        for i, package in enumerate(packages, 1):
            print(f"[{i}/{len(packages)}] Scanning {package}...")

            # Get attack surface
            surface_result = session.run_module("app.package.attacksurface", package)

            scan_data = {
                'package': package,
                'attack_surface': surface_result.output if surface_result.success else None,
                'error': surface_result.errors if not surface_result.success else None
            }

            results['scans'].append(scan_data)

        # Save results
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\nScan complete! Results saved to {output_file}")

    finally:
        session.close()
        server.close()

# Usage
automated_security_scan("your_device_id")
```

## Error Handling

Always check the `success` property of `ModuleResult`:

```python
result = session.run_module("app.package.list", ["-f", "nonexistent"])

if result.success:
    # Process successful result
    print(result.output)
else:
    # Handle error
    print(f"Module failed with exception: {result.exception}")
    print(f"Error output: {result.errors}")
```

Common errors:
- **KeyError**: Module not found
- **Other exceptions**: Module execution errors

## Best Practices

1. **Always use try/finally blocks** to ensure cleanup:
   ```python
   try:
       result = session.run_module(...)
       # Process result
   finally:
       session.close()
       server.close()
   ```

2. **Check result.success** before using output:
   ```python
   if result.success:
       process_output(result.output)
   else:
       log_error(result.errors)
   ```

3. **Use list_modules()** to discover available modules:
   ```python
   modules = session.list_modules("scanner")
   for module in modules:
       result = session.run_module(module)
   ```

4. **Handle connection failures** gracefully:
   ```python
   response = server.startSession(device_id, password)
   if response.system_response.status != Message.SystemResponse.SUCCESS:
       print(f"Connection failed: {response.system_response.error_message}")
       return
   ```

## Migration from Interactive Console

If you're used to the interactive console, here's how commands map to the API:

| Interactive Console | Programmatic API |
|---------------------|------------------|
| `run app.package.list -f browser` | `session.run_module("app.package.list", "-f browser")` |
| `run app.package.info -a com.test` | `session.run_module("app.package.info", ["-a", "com.test"])` |
| `list` | `session.list_modules()` |
| `exit` | `session.close()` |

## Troubleshooting

**Issue:** `ImportError: cannot import name 'ProgrammaticSession'`
- **Solution:** Ensure you have the latest version of drozer installed

**Issue:** `TypeError: encoding without a string argument`
- **Solution:** Ensure `session_id` is a string, not bytes

**Issue:** Module output is empty
- **Solution:** Check `result.errors` for error messages; the module may have failed

**Issue:** Connection refused
- **Solution:** Ensure drozer server is running: `drozer server start`

## See Also

- [drozer User Guide](./drozer-guide.md)
- [Module Development](./module-development.md)
- [API Source Code](../src/drozer/api/__init__.py)
