# VPN Rotation Script for Dragon Village Link Views

This script allows you to rotate through multiple VPN servers (using `.ovpn` files) to automate view clicks on Dragon Village links. The script logs used VPN servers and the number of views generated for each link, allowing you to skip previously used VPN configurations for a specific link.

## Features

- **Rotate VPN servers**: Connect to a list of VPNs using `.ovpn` files and click a Dragon Village link to generate views.
- **Track views**: Keep track of how many views each Dragon Village link has received from the program.
- **Skip used VPNs**: Ensure VPN configurations are not reused for the same link.
- **Skip failed servers**: Automatically skip VPN servers that fail to connect.
- **Clear logs**: Options to clear the VPN usage log and the skip list.

## Requirements

- Python 3.9+
- Hummingbird (AirVPN's OpenVPN3 client)
- OpenVPN configuration files (`.ovpn`)
- Requests library (`pip install requests`)

## How to Use

### Running the Script

First, activate your virtual environment by running:

```bash
source venv/bin/activate
```
To run the script:

```bash
python view_count.py
```

### Input Parameters

- **Dragon Village Link**: The script will prompt you to input the Dragon Village view link.
- **Number of Views**: The script will prompt you to input the number of views you want to generate.

If the link has been used before, the script will tell you how many views it has already received and ask how many additional views you want.

To exit at any time, press Ctrl + C.

### Commands

#### Clear VPN Usage Log

Use this command to clear the VPN usage log. This is useful if old links are no longer needed because dragons grow up after a few days:

```bash
python vpn_rotation.py --clearvpnlog
```

#### Clear Skip List

Use this command to clear the skip list, which contains VPN servers that previously failed to connect:

```bash
python vpn_rotation.py --clearskiplist
```

#### Show Skip List

Use this command to show all VPN servers that are in the skip list (i.e., servers that failed to connect in the past):

```bash
python vpn_rotation.py --showskiplist
```

## Logging

- **VPN Usage Log**: The script logs which `.ovpn` files have been used for each Dragon Village link and the number of views generated. This data is stored in `vpn_usage_log.json`.
- **Skip List**: If a VPN connection fails, the VPN server is added to the skip list, stored in `skip_list.json`.

## Example

Here is an example of running the script:

```bash
python view_count.py
Enter the Dragon Village link: https://dragon.dvc.land/view/eu?id=12345
Enter the number of views you want: 10
```

The script will rotate through the `.ovpn` files in the `configs/` directory, connect to each one, and generate views for the Dragon Village link.

## Future Improvements

- Log the connection time for each VPN server and the total runtime of the script.
- Further optimization of the connection logic.
- Command to verify existing AirVPN servers and matching OVPN files and rename them if necessary.