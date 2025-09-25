import subprocess
import json
import re

# Function to get ifconfig data
def get_ifconfig_data():
    # Run the ifconfig command and capture the output
    try:
        output = subprocess.check_output("ifconfig", stderr=subprocess.STDOUT, shell=True).decode()
    except subprocess.CalledProcessError as e:
        print("Error running ifconfig:", e)
        return []

    # Split the output by interfaces (each interface is separated by two newlines)
    interfaces = output.split("\n\n")

    interface_data = []

    for interface in interfaces:
        # Extract interface name (the first line is usually the name, e.g., eth0 or lo)
        match = re.match(r"^(\S+)\s+", interface)
        if not match:
            continue
        iface_name = match.group(1)

        # Extract IPv4 and IPv6 addresses using regular expressions
        ipv4_match = re.search(r"inet (\S+)\s+netmask", interface)
        ipv6_match = re.search(r"inet6 (\S+)\s+scope", interface)

        ipv4_address = ipv4_match.group(1) if ipv4_match else None
        ipv6_address = ipv6_match.group(1) if ipv6_match else None

        # Extract MAC address (Ethernet address) if available
        mac_match = re.search(r"ether (\S+)", interface)
        mac_address = mac_match.group(1) if mac_match else None

        # Extract packet statistics (RX and TX bytes)
        rx_bytes_match = re.search(r"RX bytes:(\d+)", interface)
        tx_bytes_match = re.search(r"TX bytes:(\d+)", interface)

        rx_bytes = int(rx_bytes_match.group(1)) if rx_bytes_match else 0
        tx_bytes = int(tx_bytes_match.group(1)) if tx_bytes_match else 0

        # Extract MTU
        mtu_match = re.search(r"MTU:(\d+)", interface)
        mtu = int(mtu_match.group(1)) if mtu_match else None

        # Extract status (UP/DOWN)
        status_match = re.search(r"(\w+)\s+RUNNING", interface)
        status = "UP" if status_match else "DOWN"  # Mark as UP if RUNNING is found, otherwise DOWN

        # Prepare the data for this interface
        interface_info = {
            "interface": iface_name,
            "mac_address": mac_address,
            "ipv4": {
                "address": ipv4_address,
            },
            "ipv6": {
                "address": ipv6_address,
            },
            "status": status,
            "rx_bytes": rx_bytes,
            "tx_bytes": tx_bytes,
            "mtu": mtu
        }

        # Append the interface info to the list
        interface_data.append(interface_info)

    return interface_data


# Function to get iwconfig data
def get_iwconfig_data():
    # Run the iwconfig command and capture the output
    try:
        output = subprocess.check_output("iwconfig", stderr=subprocess.STDOUT, shell=True).decode()
    except subprocess.CalledProcessError as e:
        print("Error running iwconfig:", e)
        return []

    # Split the output by wireless interfaces (each interface is separated by newlines)
    interfaces = output.splitlines()

    wireless_data = []
    current_iface = None

    for line in interfaces:
        # Extract interface name (e.g., wlan0)
        match = re.match(r"^(\S+)\s+", line)
        if match:
            if current_iface:  # Save the last interface if we have one
                wireless_data.append(current_iface)
            current_iface = {"interface": match.group(1)}

        # Extract ESSID (network name)
        essid_match = re.search(r"ESSID:\"([^\"]+)\"", line)
        if essid_match:
            current_iface["essid"] = essid_match.group(1)

        # Extract mode (e.g., Managed, Ad-Hoc)
        mode_match = re.search(r"Mode:(\S+)", line)
        if mode_match:
            current_iface["mode"] = mode_match.group(1)

        # Extract frequency (e.g., 2.437 GHz)
        freq_match = re.search(r"Frequency:(\S+)", line)
        if freq_match:
            current_iface["frequency"] = freq_match.group(1)

        # Extract signal level (signal strength)
        signal_match = re.search(r"Signal level=(-?\d+)", line)
        if signal_match:
            current_iface["signal_level"] = int(signal_match.group(1))

        # Extract bit rate
        bitrate_match = re.search(r"Bit Rate=\S+ (\S+)", line)
        if bitrate_match:
            current_iface["bit_rate"] = bitrate_match.group(1)

        # Extract MAC address
        mac_match = re.search(r"Access Point: (\S+)", line)
        if mac_match:
            current_iface["mac_address"] = mac_match.group(1)

    # Append the last interface if available
    if current_iface:
        wireless_data.append(current_iface)

    return wireless_data
