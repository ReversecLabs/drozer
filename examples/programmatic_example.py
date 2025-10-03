#!/usr/bin/env python3
"""
Example script demonstrating the drozer Programmatic API.

This script shows how to use drozer programmatically to:
1. Connect to a drozer server
2. Start a session with a device
3. Run modules and capture output
4. Process results programmatically

Usage:
    python programmatic_example.py [device_id]

If device_id is not provided, it will try to use the first available device.
"""

import sys
import argparse
from drozer.api import ProgrammaticSession
from drozer.connector import ServerConnector
from pysolar.api.protobuf_pb2 import Message


def list_devices(server):
    """List all available devices connected to the drozer server."""
    response = server.listDevices()
    if response.type == Message.SYSTEM_RESPONSE:
        devices = []
        for device in response.system_response.devices:
            devices.append({
                'id': device.id,
                'manufacturer': device.manufacturer,
                'model': device.model,
                'software': device.software
            })
        return devices
    return []


def run_package_analysis(device_id, package_filter=None):
    """
    Connect to device and analyze installed packages.

    Args:
        device_id: Device identifier
        package_filter: Optional filter string for package names

    Returns:
        Dictionary with analysis results
    """
    # 1. Connect to drozer server
    print("Connecting to drozer server...")
    server = ServerConnector()
    try:
        server.connect(host="localhost", port=31415)
    except Exception as e:
        print(f"Failed to connect to server: {e}")
        print("Make sure drozer server is running: drozer server start")
        return None

    # 2. Start session with device
    print(f"Starting session with device: {device_id}")
    response = server.startSession(device_id, password=None)

    if response.type != Message.SYSTEM_RESPONSE or \
       response.system_response.status != Message.SystemResponse.SUCCESS:
        print(f"Failed to start session: {response.system_response.error_message}")
        server.close()
        return None

    session_id = response.system_response.session_id
    print(f"Session started: {session_id}")

    # 3. Create programmatic session
    session = ProgrammaticSession(server, session_id)

    results = {
        'device_id': device_id,
        'packages': [],
        'attack_surfaces': []
    }

    try:
        # 4. List available modules (example)
        print("\nDiscovering package-related modules...")
        pkg_modules = session.list_modules("package")
        print(f"Found {len(pkg_modules)} package modules")

        # 5. List installed packages
        print("\nListing installed packages...")
        args = ["-f", package_filter] if package_filter else []
        pkg_result = session.run_module("app.package.list", args)

        if not pkg_result.success:
            print(f"Error listing packages: {pkg_result.errors}")
            return results

        # Parse package list
        packages = [line.strip() for line in pkg_result.output.split('\n')
                   if line.strip() and '(' in line]
        results['packages'] = packages

        print(f"Found {len(packages)} packages")
        if packages:
            print("First 5 packages:")
            for pkg in packages[:5]:
                print(f"  - {pkg}")

        # 6. Analyze attack surface for first few packages
        print("\nAnalyzing attack surfaces...")
        for i, pkg_line in enumerate(packages[:3], 1):  # Analyze first 3
            # Extract package name (before the parenthesis)
            pkg_name = pkg_line.split(' (')[0] if '(' in pkg_line else pkg_line

            print(f"[{i}/3] Analyzing: {pkg_name}")
            surface_result = session.run_module("app.package.attacksurface", pkg_name)

            if surface_result.success:
                results['attack_surfaces'].append({
                    'package': pkg_name,
                    'surface': surface_result.output
                })
                print(f"  {surface_result.output.strip()}")
            else:
                print(f"  Error: {surface_result.errors}")

        print("\n✓ Analysis complete!")
        return results

    finally:
        # 7. Always cleanup
        print("\nCleaning up...")
        session.close()
        server.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Programmatic drozer example',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('device_id', nargs='?', help='Device ID to connect to')
    parser.add_argument('-f', '--filter', help='Filter packages by name')
    parser.add_argument('-l', '--list-devices', action='store_true',
                       help='List available devices')

    args = parser.parse_args()

    # List devices if requested
    if args.list_devices:
        print("Listing available devices...")
        server = ServerConnector()
        try:
            server.connect(host="localhost", port=31415)
            devices = list_devices(server)
            server.close()

            if devices:
                print(f"\nFound {len(devices)} device(s):")
                for device in devices:
                    print(f"  ID: {device['id']}")
                    print(f"    Manufacturer: {device.get('manufacturer', 'N/A')}")
                    print(f"    Model: {device.get('model', 'N/A')}")
                    print(f"    Software: {device.get('software', 'N/A')}")
                    print()
            else:
                print("No devices found")
        except Exception as e:
            print(f"Error: {e}")
        return

    # Get device ID
    device_id = args.device_id
    if not device_id:
        print("No device ID provided. Use --list-devices to see available devices.")
        print("\nTrying to use first available device...")

        server = ServerConnector()
        try:
            server.connect(host="localhost", port=31415)
            devices = list_devices(server)
            server.close()

            if devices:
                device_id = devices[0]['id']
                print(f"Using device: {device_id}")
            else:
                print("Error: No devices found")
                sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    # Run analysis
    results = run_package_analysis(device_id, args.filter)

    if results:
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Device: {results['device_id']}")
        print(f"Packages found: {len(results['packages'])}")
        print(f"Attack surfaces analyzed: {len(results['attack_surfaces'])}")


if __name__ == '__main__':
    main()
