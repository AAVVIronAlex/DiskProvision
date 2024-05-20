# -----------------------------------------------------------------------------
# 
# DiskProvision - A virtual disk management tool for multiple OS's with unique application support.
# 
# Copyright (c) 2024 RoyalGraphX - BSD 3-Clause License
# See LICENSE file for more detailed information.
# 
# -----------------------------------------------------------------------------

import os
import re
import sys
import json
import click
import string
import shutil
import platform
import subprocess

# Define various variables
DB_FOLDER = "images"
MNT_FOLDER = "mountpoints"
DEBUG = "FALSE"

def get_host_os():
    """
    Determine the host operating system.

    Returns:
        str: The name of the host operating system ('Linux', 'Windows', 'Darwin' for macOS, etc.).
    """
    return platform.system()

def host_os_pretty():
    """
    Get a pretty-printed version of the host OS with detailed information.

    Returns:
        str: A detailed string describing the host OS.
    """
    os_type = get_host_os()
    
    if os_type == "Linux":
        # Read the os-release file to get distribution information
        try:
            with open('/etc/os-release') as f:
                lines = f.readlines()
                os_info = {}
                for line in lines:
                    key, value = line.strip().split('=', 1)
                    os_info[key] = value.strip('"')
                pretty_name = os_info.get('PRETTY_NAME', 'Linux')
                return pretty_name
        except Exception:
            return "Linux"
    
    elif os_type == "Darwin":
        try:
            # Use sw_vers to get macOS version details
            sw_vers_output = subprocess.check_output(["sw_vers"], text=True).strip().split("\n")
            version_info = {line.split(":")[0].strip(): line.split(":")[1].strip() for line in sw_vers_output}
            return f"Darwin {version_info.get('ProductVersion', '')} ({version_info.get('BuildVersion', '')})"
        except Exception:
            return "Darwin"
    
    return os_type

def get_current_directory():
    """Gets the current working directory and returns it"""
    return os.getcwd()

def get_last_directory_name(path):
    """
    Get the last directory name from a given path.
    
    Parameters:
        path (str): The path from which to extract the last directory name.
    
    Returns:
        str: The last directory name in the path.
    """
    return os.path.basename(os.path.normpath(path))

def check_image_exists(image_name):
    """
    Check if an image with the given name/extension exists in the database folder.

    Args:
        image_name (str): The name of the image to check.

    Returns:
        bool: True if the image exists, False otherwise.
    """
    db_path = os.path.join(get_current_directory(), DB_FOLDER)
    image_path = os.path.join(db_path, f"{image_name}.img")
    qcow2_path = os.path.join(db_path, f"{image_name}.qcow2")
    return os.path.exists(image_path) or os.path.exists(qcow2_path)

def ensure_directory_exists(directory):
    """
    Ensure that the specified directory exists.
    If it doesn't exist, create it.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
        if DEBUG == "TRUE":
            print(f"Directory '{directory}' created.")
    else:
        if DEBUG == "TRUE":
            print(f"Directory '{directory}' already exists.")

def ensure_directory_exists_destructive(directory):
    """
    Check if a directory exists, and delete it if it does.
    If the directory does not exist, print that it does not need to be deleted.

    Args:
        directory (str): The path of the directory to check and delete if it exists.
    """
    if os.path.exists(directory):
        if os.path.isdir(directory):
            shutil.rmtree(directory)
            if DEBUG.upper() == "TRUE":
                print(f"Directory '{directory}' existed and has been deleted.")
        else:
            print(f"'{directory}' exists but is not a directory.")
    else:
        print(f"Directory '{directory}' does not exist and does not need to be deleted.")

def get_latest_modified_file(directory):
    """
    Get the absolute path of the latest modified file in the specified directory.

    Args:
        directory (str): The directory to scan for files.

    Returns:
        str: The absolute path of the latest modified file.
    """
    # Get the list of files in the directory
    files = os.listdir(directory)
    
    # Filter out directories
    files = [f for f in files if os.path.isfile(os.path.join(directory, f))]
    
    # If there are no files in the directory, return None
    if not files:
        return None
    
    # Get the modification time of each file
    file_mod_times = {f: os.path.getmtime(os.path.join(directory, f)) for f in files}
    
    # Find the file with the maximum modification time
    latest_file = max(file_mod_times, key=file_mod_times.get)
    
    # Return the absolute path of the latest modified file
    return os.path.abspath(os.path.join(directory, latest_file))

def load_available_images():
    """
    Load all available disk images from the DB_FOLDER.

    Returns:
        list: A list of available disk images.
    """
    db_path = os.path.join(get_current_directory(), DB_FOLDER)
    ensure_directory_exists(db_path)
    images = [f for f in os.listdir(db_path) if os.path.isfile(os.path.join(db_path, f))]
    return images

def manage_chosen_image(chosen_image):
    """
    Function to manage the chosen disk image.

    Args:
        chosen_image (str): The path of the chosen disk image.
    """
    if DEBUG.upper() == "TRUE":
        click.echo(f"Image file path: {chosen_image}")

    click.echo("Available Options:")
    click.echo("1. Mount Image")
    click.echo("2. Format Image")
    click.echo("3. Delete Image")
    click.echo("4. Duplicate Image")
    
    if get_host_os() == "Linux":
        click.echo("5. Image Information")
        click.echo("6. Back to Main Menu")
    else:
        click.echo("5. Back to Main Menu")

    choice = click.prompt("Enter your choice", type=int)

    if choice == 1:
        mount_image(chosen_image)
    elif choice == 2:
        format_image(chosen_image)
    elif choice == 3:
        delete_image(chosen_image)
    elif choice == 4:
        duplicate_image(chosen_image)
    elif choice == 5 and get_host_os() == "Linux":
        fetch_disk_info_linux(chosen_image)
    elif choice == 5:
        click.echo("Returning to Main Menu...")
    elif choice == 6 and get_host_os() == "Linux":
        click.echo("Returning to Main Menu...")
    else:
        click.echo("Invalid choice. Please enter a valid option.")

def mount_image(image_path):
    """Handles mounting images based on host OS"""
    host_os = get_host_os()
    
    if DEBUG.upper() == "TRUE":
        print(f"Detected Operating System: {host_os}")

    if host_os == "Linux":
        if DEBUG.upper() == "TRUE":
            print("Mounting image on Linux...")

            # Print the image path
            print(f"Image path passed to mount_image function: {image_path}")

        # Extract the image name and print it
        image_name = extract_image_name(image_path)
        if DEBUG.upper() == "TRUE":
            print(f"Extracted image name: {image_name}")

        # Check and load nbd module
        if DEBUG.upper() == "TRUE":
            print("Checking if nbd module is loaded...")
        check_and_load_nbd_module()

        # Determine the next available nbd device
        if DEBUG.upper() == "TRUE":
            print("Determining the next available nbd device...")
        nbd_device = get_next_available_nbd()
        if DEBUG.upper() == "TRUE":
            print(f"Next available nbd device: {nbd_device}")

        # Prompt the user for their choice using click
        create_mount_dir = click.confirm("Would you like to create a mount directory?", default=True)

        if create_mount_dir:
            if DEBUG.upper() == "TRUE":
                print("User chose to create a mount directory.")

            current_directory = get_current_directory()
            db_path = os.path.join(current_directory, DB_FOLDER)
            mnt_path = os.path.join(current_directory, MNT_FOLDER)
            if DEBUG.upper() == "TRUE":
                click.echo(f"Current directory: {current_directory}")
                click.echo(f"Database folder: {db_path}")
                click.echo(f"Mounts folder: {mnt_path}")
            ensure_directory_exists(db_path)
            ensure_directory_exists(mnt_path)

            img_mnt_path = os.path.join(mnt_path, image_name)
            if DEBUG.upper() == "TRUE":
                click.echo(f"Image Mount directory: {img_mnt_path}")

            # Check if the img_mnt_path already exists
            if os.path.exists(img_mnt_path):
                print(f"Mount directory for {image_name} already exists. Have you unmounted it?")
                return
            else:
                ensure_directory_exists(img_mnt_path)
                if DEBUG.upper() == "TRUE":
                    print(f"Created mount directory {img_mnt_path}")

            # Determine the image format for later command building
            image_format = detect_image_format(image_path)
            if DEBUG.upper() == "TRUE":
                print("Detected Image Format:", image_format)

            # Construct the nbd_connect command
            nbd_connect_command = f"sudo qemu-nbd --connect=/dev/{nbd_device} -f {image_format} {image_path}"
            if DEBUG.upper() == "TRUE":
                print(f"Executing NBD connect command: {nbd_connect_command}")

            # Execute the nbd_connect command, suppressing the output if DEBUG is FALSE
            if DEBUG.upper() == "TRUE":
                subprocess.run(nbd_connect_command, shell=True)
            else:
                subprocess.run(nbd_connect_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            if DEBUG.upper() == "TRUE":
                print(f"Connected {image_name} to /dev/{nbd_device}")

            # Probe the connected nbd device for partitions, if none exist, we cannot continue
            nbd_device_info = get_nbd_device_info(nbd_device)
            if nbd_device_info:
                if DEBUG.upper() == "TRUE":
                    print(f"Device: {nbd_device_info['device']}")
                    print(f"Size: {nbd_device_info['size']}")
                    print(f"Mount Point: {nbd_device_info['mount_point']}")
                    print(f"Number of Partitions: {nbd_device_info['total_partitions']}")
                    print(f"Partitions: {', '.join(nbd_device_info['partitions']) if nbd_device_info['partitions'] else 'None'}")

                # Check if the NBD device has 0 partitions
                if nbd_device_info['total_partitions'] == 0:
                    print("Cannot mount... The selected image has 0 partitions. Have you formatted it yet?")

                    # Remove created Mount Point directory for clean up
                    if DEBUG.upper() == "TRUE":
                        print("Removing Mount Directory for clean up...")
                    ensure_directory_exists_destructive(img_mnt_path)

                    # Disconnect image from NBD Device for clean up
                    if DEBUG.upper() == "TRUE":
                        print("Disconnecting the NBD device...")

                    # Build the disconnect_nbd_command for the NBD device
                    disconnect_nbd_command = f"sudo qemu-nbd --disconnect /dev/{nbd_device}"

                    # Execute the command
                    if DEBUG.upper() == "TRUE":
                        subprocess.run(disconnect_nbd_command, shell=True)
                    else:
                        subprocess.run(disconnect_nbd_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                    if DEBUG.upper() == "TRUE":
                        print("Successfully cleaned up. Returning to Main Menu...")

                    return
                else:
                    # Continue with further actions
                    if DEBUG.upper() == "TRUE":
                        print("The selected image has valid partitions. Continuing...")
            else:
                print("Failed to get NBD device information. Exiting...")
                return

            # Mount the nbd device to the image mount path directory with desired ownership
            mount_command = f"sudo mount -o uid=$(id -u),gid=$(id -g) /dev/{nbd_device} {img_mnt_path}"
            if DEBUG.upper() == "TRUE":
                print(f"Executing mount command: {mount_command}")
                subprocess.run(mount_command, shell=True)
            else:
                subprocess.run(mount_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            print(f"Successfully mounted {image_name} to {img_mnt_path}")

        else:
            if DEBUG.upper() == "TRUE":
                print("User chose to only connect image to nbd.")
            
            # Determine the image format for later command building
            image_format = detect_image_format(image_path)
            if DEBUG.upper() == "TRUE":
                print("Detected Image Format:", image_format)

            # Construct the nbd_connect command
            nbd_connect_command = f"sudo qemu-nbd --connect=/dev/{nbd_device} -f {image_format} {image_path}"
            if DEBUG.upper() == "TRUE":
                print(f"Executing NBD connect command: {nbd_connect_command}")

            # Execute the nbd_connect command, suppressing the output if DEBUG is FALSE
            if DEBUG.upper() == "TRUE":
                subprocess.run(nbd_connect_command, shell=True)
            else:
                subprocess.run(nbd_connect_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            print(f"Successfully Connected {image_name} to /dev/{nbd_device}")

    elif host_os == "Windows":
        print("Mounting image on Windows has not been implemented yet")
        # Placeholder comment for Windows mounting logic

    elif host_os == "Darwin":
        if DEBUG.upper() == "TRUE":
            print("Mounting image on macOS...")

        # Check if the image has a .img extension
        if image_path.lower().endswith(".img"):
            if DEBUG.upper() == "TRUE":
                print("Detected raw disk image (.img).")

            # Mount the disk image using hdiutil
            mount_command = ["hdiutil", "attach", image_path]
            subprocess.run(mount_command)
        else:
            print("Unsupported image format for macOS. Only .img files can be mounted.")
            return
    else:
        print("Unknown operating system. Unable to mount image.")
        # Placeholder comment for handling unknown operating systems

def format_image(image_path):
    """Handles formatting images based on host OS"""
    host_os = get_host_os()
    
    if DEBUG.upper() == "TRUE":
        print(f"Detected Operating System: {host_os}")

    if host_os == "Linux":
        print("Formatting image on Linux...")
        
        # Initialize a dictionary of supported mkfs commands
        supported_mkfs_commands = get_supported_mkfs_commands()

        if DEBUG.upper() == "TRUE":
            print("Supported mkfs commands:")
            for pretty_name, mkfs_command in supported_mkfs_commands.items():
                print(f"{pretty_name}: {mkfs_command}")

        # Prompt the user to choose a formatting command
        print("Choose a formatting command:")
        for i, pretty_name in enumerate(supported_mkfs_commands.keys(), start=1):
            print(f"{i}. {pretty_name}")

        choice = input("Enter the number of the formatting command: ")
        try:
            choice_index = int(choice)
            if choice_index < 1 or choice_index > len(supported_mkfs_commands):
                raise ValueError
            chosen_pretty_name = list(supported_mkfs_commands.keys())[choice_index - 1]
            chosen_mkfs_command = supported_mkfs_commands[chosen_pretty_name]

            # In this area, we will handle properly formatting a given selected image
            # by checking if a user chose a known mkfs command, if used we can easily
            # confirm the correct way to format using a specific command and image extension
            # The first supported mkfs command is FAT. Both 16 and 32 are supported OOB.

            # Check if the chosen command is mkfs.fat
            if chosen_mkfs_command == "/sbin/mkfs.fat":
                print(f"You chose: {chosen_mkfs_command}")

                # If mkfs.fat is chosen, ask for FAT16 or FAT32
                fat_choice = input("Choose FAT type:\n1. FAT16\n2. FAT32\nEnter the number: ")
                if fat_choice == "1":
                    print("Continuing for FAT16 choice...")

                    # Print variable holding chosen image path
                    print("Chosen Image Path:", image_path)

                    # Check if nbd module is loaded, if not, load it
                    check_and_load_nbd_module()

                    # Get the next available nbd device to use
                    next_nbd = get_next_available_nbd()
                    if next_nbd:
                        if DEBUG.upper() == "TRUE":
                            print(f"The next available NBD device is: {next_nbd}")

                        # Retrieve a name to use for partition name
                        image_name = extract_image_name_for_fat(image_path)
                        if DEBUG.upper() == "TRUE":
                            print("FAT16 Partition Name Generated:", image_name)

                        # Detect the image format to use in the connect_command
                        image_format = detect_image_format(image_path)
                        if DEBUG.upper() == "TRUE":
                            print("Image format detected as:", image_format)
                        
                        # Build the connect_command to connect the image file to the next available nbd device
                        connect_command = f"sudo qemu-nbd --connect=/dev/{next_nbd} -f {image_format} {image_path}"
                        if DEBUG.upper() == "TRUE":
                            print("Built Connect Command:", connect_command)

                        # Execute the command
                        if DEBUG.upper() == "TRUE":
                            subprocess.run(connect_command, shell=True)
                        else:
                            subprocess.run(connect_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                        print("Successfully connected image to:", next_nbd)

                        # Build the format_command to format the mounted image with FAT32 filesystem and the specified name
                        format_command = f"sudo mkfs.fat -F 16 -n \"{image_name}\" -I /dev/{next_nbd}"

                        # Execute the command
                        if DEBUG.upper() == "TRUE":
                            subprocess.run(format_command, shell=True)
                        else:
                            subprocess.run(format_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                        # Build the unmount_command for the image on the NBD device
                        unmount_command = f"sudo qemu-nbd --disconnect /dev/{next_nbd}"

                        # Execute the command
                        if DEBUG.upper() == "TRUE":
                            subprocess.run(unmount_command, shell=True)
                        else:
                            subprocess.run(unmount_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                        print("Successfully formatted as FAT16!")

                elif fat_choice == "2":
                    print("Continuing for FAT32 choice...")
                    
                    # Print variable holding chosen image path
                    print("Chosen Image Path:", image_path)

                    # Check if nbd module is loaded, if not, load it
                    check_and_load_nbd_module()

                    # Get the next available nbd device to use
                    next_nbd = get_next_available_nbd()
                    if next_nbd:
                        if DEBUG.upper() == "TRUE":
                            print(f"The next available NBD device is: {next_nbd}")

                        # Retrieve a name to use for partition name
                        image_name = extract_image_name_for_fat(image_path)
                        if DEBUG.upper() == "TRUE":
                            print("FAT32 Partition Name Generated:", image_name)

                        # Detect the image format to use in the connect_command
                        image_format = detect_image_format(image_path)
                        if DEBUG.upper() == "TRUE":
                            print("Image format detected as:", image_format)
                        
                        # Build the connect_command to connect the image file to the next available nbd device
                        connect_command = f"sudo qemu-nbd --connect=/dev/{next_nbd} -f {image_format} {image_path}"
                        if DEBUG.upper() == "TRUE":
                            print("Built Connect Command:", connect_command)

                        # Execute the command
                        if DEBUG.upper() == "TRUE":
                            subprocess.run(connect_command, shell=True)
                        else:
                            subprocess.run(connect_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                        print("Successfully connected image to:", next_nbd)

                        # Build the format_command to format the mounted image with FAT32 filesystem and the specified name
                        format_command = f"sudo mkfs.fat -F 32 -n \"{image_name}\" -I /dev/{next_nbd}"

                        # Execute the command
                        if DEBUG.upper() == "TRUE":
                            subprocess.run(format_command, shell=True)
                        else:
                            subprocess.run(format_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                        # Build the unmount_command for the image on the NBD device
                        unmount_command = f"sudo qemu-nbd --disconnect /dev/{next_nbd}"

                        # Execute the command
                        if DEBUG.upper() == "TRUE":
                            subprocess.run(unmount_command, shell=True)
                        else:
                            subprocess.run(unmount_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                        print("Successfully formatted as FAT32!")

                    else:
                        print("No available NBD devices found.")

                else:
                    print("Invalid input. Please enter either 1 or 2.")

            else:
                # Placeholder code to print the chosen command, and say it's not supported
                print(f"You chose: {chosen_mkfs_command}")
                print(f"Unfortunately, {chosen_pretty_name} is not supported yet.")
                return

        except ValueError:
            print("Invalid input. Please enter a valid number.")

    elif host_os == "Windows":
        print("Formatting image on Windows has not been implemented yet")
        # Placeholder comment for Windows mounting logic
    elif host_os == "Darwin":
        if DEBUG.upper() == "TRUE":
            print("Formatting image on macOS...")

        # Check if the image has a .img extension
        if not image_path.lower().endswith(".img"):
            print("Unsupported image format for macOS. Only .img files can be formatted.")
            return

        # Prompt the user to choose a filesystem
        supported_filesystems = ["FAT32", "APFS", "JHFS+"]
        filesystem_choice = click.prompt("Choose a filesystem to format the image", type=click.Choice(supported_filesystems))

        # Determine the maximum length for the partition name based on the chosen filesystem
        max_partition_length = {
            "FAT32": 8,   # FAT32 allows up to 8 characters for the partition name
            "APFS": 255,   # APFS allows up to 255 characters for the partition name
            "JHFS+": 27    # JHFS+ allows up to 27 characters for the partition name
        }

        # Prompt the user to enter the partition name
        max_length = max_partition_length.get(filesystem_choice)
        partition_name = click.prompt(f"Enter a name for the partition (max {max_length} characters)")

        # Mount the image with noverify using hdiutil to initialize the image
        noverify_mountcommand = ["hdiutil", "attach", "-noverify", "-nomount", image_path]
        mount_output = subprocess.check_output(noverify_mountcommand, text=True)
        root_image_path = mount_output.strip()  # Capture the mounted path and remove any whitespace
        
        if DEBUG.upper() == "TRUE":
            # Output the root image path
            print(f"The image was mounted at: {root_image_path}")

        # Build the command to format the disk image
        format_command = ["diskutil", "eraseDisk", filesystem_choice, partition_name, root_image_path]

        if DEBUG.upper() == "TRUE":
            print(f"Running command: {' '.join(format_command)}")
        
        # Execute the command
        format_output = subprocess.check_output(format_command, text=True)
        
        # Extract the rdisk image path from the output
        rdisk_image_path = None
        for line in format_output.splitlines():
            if "Formatting" in line:
                rdisk_image_path = line.split()[0]  # Extract the first word from the line
                break

        if rdisk_image_path:
            if DEBUG.upper() == "TRUE":
                print(f"The rdisk image path is: {rdisk_image_path}")
        else:
            print("Failed to extract the rdisk image path.")

        # Unmount the image
        unmount_command = ["hdiutil", "detach", root_image_path]
        subprocess.run(unmount_command)

        if DEBUG.upper() == "TRUE":
            print("Image successfully unmounted.")

        print("Image successfully formatted.")

    else:
        print("Unknown operating system. Unable to format image.")
        # Placeholder comment for handling unknown operating systems

def delete_image(image_path):
    """Deletes the image file."""
    # Ask the user to confirm deletion
    confirmation = click.confirm(f"Are you sure you want to delete '{os.path.basename(image_path)}' permanently?")
    if confirmation:
        try:
            # Attempt to delete the file
            os.remove(image_path)
            click.echo(f"Image '{os.path.basename(image_path)}' deleted successfully.")
        except FileNotFoundError:
            click.echo("File not found.")
    else:
        click.echo("Deletion canceled.")

def duplicate_image(image_path):
    """Duplicates the image file."""
    current_directory = get_current_directory()
    db_path = os.path.join(current_directory, DB_FOLDER)

    # Ask the user for the name of the duplicate image file
    new_image_name = click.prompt("Enter the name of the duplicate image")

    # Get the original file extension
    original_extension = os.path.splitext(image_path)[1]

    # Append the original extension to the new image name if it doesn't already have it
    if not new_image_name.lower().endswith(original_extension.lower()):
        new_image_name += original_extension

    # Check if the new image file already exists
    new_image_path = os.path.join(db_path, new_image_name)
    if os.path.exists(new_image_path):
        click.echo("A file with the same name already exists.")
        return

    # Construct the command to duplicate the image file
    command = f"cp {image_path} {new_image_path}"

    # Execute the command
    subprocess.run(command, shell=True)

    click.echo(f"Image '{os.path.basename(image_path)}' duplicated successfully as '{new_image_name}'.")

def check_and_load_nbd_module():
    """
    Check if the nbd module is loaded.
    If not, attempt to load it using modprobe.
    """
    try:
        # Run lsmod command to check if nbd module is loaded
        lsmod_output = subprocess.check_output(["lsmod"], text=True)
        if "nbd" in lsmod_output:
            if DEBUG.upper() == "TRUE":
                print("NBD module is already loaded.")
        else:
            # Attempt to load the nbd module using modprobe
            subprocess.run(["sudo", "modprobe", "nbd", "max_part=8"])
            # Recheck if nbd module is loaded after attempting to load it
            lsmod_output = subprocess.check_output(["lsmod"], text=True)
            if "nbd" in lsmod_output:
                if DEBUG.upper() == "TRUE":
                    print("nbd module loaded successfully.")
            else:
                print("Failed to load nbd module.")
                sys.exit(1)  # Exit with error code 1
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        sys.exit(1)  # Exit with error code 1

def get_next_available_nbd():
    """
    Get the next available NBD device.

    Returns:
        str: The name of the next available NBD device (e.g., 'nbd1').
    """
    try:
        # Run the lsblk command and capture the output
        lsblk_output = subprocess.check_output(["lsblk", "-o", "NAME,SIZE,TYPE,MOUNTPOINT"], text=True)
        
        # Filter the output for lines containing 'nbd'
        nbd_lines = [line for line in lsblk_output.split("\n") if "nbd" in line]

        # Iterate through the filtered lines to find the next available NBD device
        for line in nbd_lines:
            columns = line.split()
            device_name = columns[0]
            device_size = columns[1]
            if device_size == "0B":
                return device_name
        
        return None  # Return None if no available NBD device is found
    
    except subprocess.CalledProcessError as e:
        print(f"Error executing lsblk command: {e}")
        return None

def extract_image_name(image_path):
    """
    Extracts the image name from the given image path without converting it to uppercase.

    Args:
        image_path (str): The path of the image.

    Returns:
        str: The extracted image name.
    """
    # Split the image path into filename and extension
    filename, extension = os.path.splitext(os.path.basename(image_path))
    
    # Return the filename without converting to uppercase
    return filename

def extract_upper_image_name(image_path):
    """
    Extracts the image name from the given image path and converts it to uppercase.

    Args:
        image_path (str): The path of the image.

    Returns:
        str: The extracted image name.
    """
    # Split the image path into filename and extension
    filename, extension = os.path.splitext(os.path.basename(image_path))
    
    # Convert filename to uppercase
    image_name = filename.upper()
    
    return image_name

def extract_image_name_for_fat(image_path):
    """
    Extracts the image name from the given image path, converts it to uppercase, 
    and restricts it to 8 characters max. Fit for FAT16/32 partition names.

    Args:
        image_path (str): The path of the image.

    Returns:
        str: The extracted image name.
    """
    # Split the image path into filename and extension
    filename, extension = os.path.splitext(os.path.basename(image_path))
    
    # Convert filename to uppercase and restrict to 8 characters max
    image_name = filename.upper()[:8]
    
    return image_name

def detect_image_format(image_path):
    """Detects the format of a disk image based on its file extension.

    Args:
        image_path (str): The path to the disk image.

    Returns:
        str: The detected format of the disk image ('raw', 'qcow2', or 'unknown').
    """
    # Convert the file extension to lowercase and check the format
    extension = image_path.lower().split('.')[-1]
    if extension in ['img', 'raw']:
        return "raw"
    elif extension == 'qcow2':
        return "qcow2"
    else:
        return "unknown"

def get_nbd_devices():
    """
    Enumerate all available nbd devices on the system using lsblk.
    Return a dictionary of nbd devices.
    """
    try:
        # Execute the lsblk command to list block devices
        lsblk_output = subprocess.check_output(['lsblk', '-o', 'NAME'], text=True)
        
        # Split the output into lines
        lines = lsblk_output.strip().split('\n')
        
        # Filter lines to include only nbd devices
        nbd_devices = [line for line in lines if line.startswith('nbd')]
        
        # Create a dictionary of nbd devices
        nbd_devices_dict = {f"nbd{i}": nbd for i, nbd in enumerate(nbd_devices)}
        
        return nbd_devices_dict
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        return {}

def get_connected_nbd_devices():
    """
    Enumerate all connected nbd devices with a size greater than 0B using lsblk.
    Return a dictionary of these nbd devices.
    """
    try:
        # Execute the lsblk command to list block devices with their sizes
        lsblk_output = subprocess.check_output(['lsblk', '-o', 'NAME,SIZE'], text=True)
        
        # Split the output into lines and skip the header
        lines = lsblk_output.strip().split('\n')[1:]
        
        # Filter lines to include only nbd devices with size greater than 0B
        connected_nbd_devices = [line.split()[0] for line in lines if line.startswith('nbd') and not line.split()[1] == '0B']
        
        # Create a dictionary of connected nbd devices
        connected_nbd_devices_dict = {device: device for device in connected_nbd_devices}
        
        return connected_nbd_devices_dict
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        return {}

def get_nbd_device_info(nbd_device):
    """
    Get detailed information about an nbd device.
    
    Parameters:
        nbd_device (str): The name of the nbd device (e.g., 'nbd2').
    
    Returns:
        dict: A dictionary containing device information including size, mount point, partitions, and total number of partitions.
    """
    try:
        # Execute the lsblk command to get detailed information about the nbd device
        lsblk_output = subprocess.check_output(['lsblk', '-o', 'NAME,SIZE,TYPE,MOUNTPOINT', f'/dev/{nbd_device}', '--json'], text=True)
        
        # Convert the JSON output to a dictionary
        lsblk_info = json.loads(lsblk_output)
        
        # Extract device information
        device_info = {
            'device': nbd_device,
            'size': lsblk_info['blockdevices'][0]['size'],
            'mount_point': lsblk_info['blockdevices'][0]['mountpoint'],
            'partitions': [],
            'total_partitions': 0
        }
        
        # Extract partition information
        if 'children' in lsblk_info['blockdevices'][0]:
            partitions = lsblk_info['blockdevices'][0]['children']
            for partition in partitions:
                device_info['partitions'].append(partition['name'])
        
        # Calculate total number of partitions
        device_info['total_partitions'] = len(device_info['partitions'])
        
        return device_info
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        return {}

def get_supported_mkfs_commands():
    """
    Get supported mkfs commands on the system.

    Returns:
        dict: A dictionary containing supported mkfs commands with pretty names.
    """
    supported_mkfs = {}
    try:
        # List files in the /sbin directory
        files_in_sbin = os.listdir("/sbin")

        # Filter out mkfs commands from the list of files
        mkfs_commands = [filename for filename in files_in_sbin if filename.startswith("mkfs.")]

        # Extract pretty names from mkfs commands
        for mkfs_command in mkfs_commands:
            pretty_name = mkfs_command.replace("mkfs.", "").capitalize()
            supported_mkfs[pretty_name] = f"/sbin/{mkfs_command}"

        return supported_mkfs
    except OSError as e:
        print(f"Error listing files in /sbin directory: {e}")
        return supported_mkfs

def fetch_disk_info_linux(chosen_image):
    """
    Fetches disk information via NBD by going through a routine to display information.
    Has Post Clean Up code that disconnects the chosen image after done viewing.
    
    Args:
        chosen_image (str): The path of the chosen disk image.
    """

    image_name = extract_image_name(chosen_image)
    if DEBUG.upper() == "TRUE":
        click.echo(f"Fetching disk information for {image_name} via NBD...")

    # Check if nbd module is loaded, if not, load it
    check_and_load_nbd_module()

    # Get the next available nbd device to use
    next_nbd = get_next_available_nbd()
    if next_nbd:
        if DEBUG.upper() == "TRUE":
            print(f"The next available NBD device is: {next_nbd}")

        # Build the connect_command to connect the image file to the next available nbd device
        connect_command = f"sudo qemu-nbd --connect=/dev/{next_nbd} -f raw {chosen_image}"

        # Execute the command
        if DEBUG.upper() == "TRUE":
            subprocess.run(connect_command, shell=True)
        else:
            subprocess.run(connect_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Probe and print general information of the disk image
        print(f"Name of disk image:", image_name)
        print(f"Absolute path of Image", chosen_image)

        image_format = detect_image_format(chosen_image)
        print(f"Image format based on extension:", image_format)

        # Probe for information about the disk image on the NBD device
        nbd_device_info = get_nbd_device_info(next_nbd)
        if nbd_device_info:
            print(f"Image connected on Device: {nbd_device_info['device']}")
            print(f"Size on Disk: {nbd_device_info['size']}")
            print(f"Mount Point: {nbd_device_info['mount_point']}")
            print(f"Number of Partitions: {nbd_device_info['total_partitions']}")
            print(f"Partitions: {', '.join(nbd_device_info['partitions']) if nbd_device_info['partitions'] else 'None'}")
        else:
            print("Failed to get NBD device information. Exiting...")
            return

        # Build the disconnect_command for the image on the NBD device
        disconnect_command = f"sudo qemu-nbd --disconnect /dev/{next_nbd}"

        # Execute the command
        if DEBUG.upper() == "TRUE":
            subprocess.run(disconnect_command, shell=True)
        else:
            subprocess.run(disconnect_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    else:
        print("No available NBD device found. Try after unmounting some images first.")

@click.command()
def main():
    """Main entry point for DiskProvision."""
    while True:
        click.clear()
        click.echo("Welcome to DiskProvision!")
        click.echo("Copyright (c) 2024 RoyalGraphX")
        click.echo(f"Python x86_64 Pre-Release 0.5.6 for {host_os_pretty()}\n")
        click.echo("What would you like to do?")
        click.echo("1. Create a new blank disk image")
        click.echo("2. Manage existing disk images")
        if get_host_os() == "Linux":
            click.echo("3. Create an OpenCore disk image")
        if get_host_os() == "Darwin":
            click.echo("3. Unmount a disk image")
            click.echo("4. Exit")
        else:
            click.echo("4. Unmount a disk image")
            click.echo("5. Exit")

        choice = click.prompt("Enter your choice", type=int)

        if choice == 1:
            create_disk_image()
        elif choice == 2:
            manage_disk_images()
        elif choice == 3 and get_host_os() == "Linux":
            create_oc_image()
        elif choice == 3 and get_host_os() == "Darwin":
            unmount_disk_image()
        elif choice == 4 and get_host_os() == "Darwin":
            exit_program()
        elif choice == 4 and get_host_os() != "Darwin":
            unmount_disk_image()
        elif choice == 5:
            exit_program()
        else:
            click.echo("Invalid choice. Please enter a valid option.")

        # Pause to show the result before clearing the screen again
        click.pause()

def create_disk_image():
    if DEBUG.upper() == "FALSE":
        click.clear()
    
    current_directory = get_current_directory()
    db_path = os.path.join(current_directory, DB_FOLDER)
    ensure_directory_exists(db_path)
    if DEBUG.upper() == "TRUE":
            click.echo(f"Current directory: {current_directory}")
            click.echo(f"Database folder: {db_path}")

    # Ask for the name of the image
    image_name = click.prompt("Enter the name of the image to create")

    # Determine the image format
    image_extension = ""
    if "." in image_name:
        # If the user input contains a dot, assume they provided an extension
        image_extension = image_name.split(".")[-1]
        if image_extension in ["img", "qcow2"]:
            image_format = "raw" if image_extension == "img" else "qcow2"
            image_name = image_name.rsplit(".", 1)[0]  # Remove the extension from the image name
        else:
            click.echo("Invalid extension provided. Please choose the image format.")
            return
    else:
        image_format = click.prompt("Choose the image format", type=click.Choice(["raw", "qcow2"]))
        # Append the appropriate extension based on the format
        image_extension = "img" if image_format == "raw" else "qcow2"

    # Ask for the size of the image in GB
    image_size = click.prompt("Enter the size of the image in GB", type=float)

    # Check if an image with the same name already exists
    image_path = os.path.join(db_path, f"{image_name}.{image_extension}")
    if os.path.exists(image_path):
        overwrite = click.confirm(f"An image with the name '{image_name}' already exists. Do you want to overwrite it?")
        if not overwrite:
            click.echo("Operation canceled.")
            return

    # Construct the command to create the disk image
    command = f"qemu-img create -f {image_format} {image_path} {image_size}G"
    
    # Execute the command, suppressing the output if DEBUG is FALSE
    if DEBUG.upper() == "TRUE":
        subprocess.run(command, shell=True)
    else:
        subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    click.echo(f"Disk image '{image_name}.{image_extension}' created successfully.")

def create_disk_image_octype():
    if DEBUG.upper() == "FALSE":
        click.clear()
    
    current_directory = get_current_directory()
    db_path = os.path.join(current_directory, DB_FOLDER)
    ensure_directory_exists(db_path)

    if DEBUG.upper() == "TRUE":
            click.echo(f"Current directory: {current_directory}")
            click.echo(f"Database folder: {db_path}")

    max_name_length = 8  # Maximum length for FAT32 partition name
    while True:
        # Ask for the name of the image
        image_name = click.prompt(f"Enter the name of the image (max {max_name_length} characters)", type=str)

        # Remove .img extension if it's included
        image_name = image_name.replace(".img", "")

        # Check if the name length exceeds the maximum allowed for FAT32
        if len(image_name) > max_name_length:
            click.echo(f"Image name must be {max_name_length} characters or less. Please try again.")
            continue
        
        # Check if the name contains only letters
        if not all(char in string.ascii_letters for char in image_name):
            click.echo("Image name can only contain letters. Please try again.")
            continue

        # Check if the name is already in use
        image_path = os.path.join(db_path, f"{image_name}.img")
        if os.path.exists(image_path):
            overwrite = click.confirm(f"An image with the name '{image_name}' already exists. Do you want to overwrite it?")
            if not overwrite:
                click.echo("Operation canceled.")
                return
            else:
                break
        else:
            break

    # Ask for the size of the image in GB
    image_size = click.prompt("Enter the size of the image in GB", type=float)

    # Construct the path of the image
    image_path = os.path.join(db_path, f"{image_name}.img")

    # Construct the command to create the disk image
    command = f"qemu-img create -f raw {image_path} {image_size}G"

    # Execute the command, suppressing the output if DEBUG is FALSE
    if DEBUG.upper() == "TRUE":
        subprocess.run(command, shell=True)
    else:
        subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    click.echo(f"OpenCore type Disk image '{image_name}.img' created successfully.")

def manage_disk_images():
    click.clear()
    
    if DEBUG.upper() == "TRUE":
        click.echo("Loading available disk images...")
    
    images = load_available_images()
    if not images:
        click.echo("No disk images found.")
        return

    click.echo("Available disk images:")
    for i, image in enumerate(images, start=1):
        click.echo(f"{i}. {image}")

    image_choice = click.prompt("Enter the number of the image to manage (or 'c' to cancel)", default='c')
    if image_choice.lower() == 'c':
        click.echo("Operation canceled.")
        return

    try:
        image_choice = int(image_choice)
        if 1 <= image_choice <= len(images):
            chosen_image_name = images[image_choice - 1]
            click.echo(f"You selected '{chosen_image_name}'.")
            # Construct the path of the chosen image
            chosen_image_path = os.path.join(get_current_directory(), DB_FOLDER, chosen_image_name)
            # Proceed to manage the chosen image
            manage_chosen_image(chosen_image_path)
        else:
            click.echo("Invalid choice. Please enter a valid number.")
    except ValueError:
        click.echo("Invalid input. Please enter a number or 'c' to cancel.")

def create_oc_image():
    click.clear()

    if DEBUG.upper() == "TRUE":
        click.echo("Creating an OpenCore disk image...")

    # Check if nbd module is loaded, if not, load it
    check_and_load_nbd_module()

    # Get the next available nbd device to use
    next_nbd = get_next_available_nbd()
    if next_nbd:
        if DEBUG.upper() == "TRUE":
            print(f"The next available NBD device is: {next_nbd}")

        # We can use create_disk_image_octype to handle the creation of a special image
        create_disk_image_octype()

        # Define variables for rest of process
        current_directory = get_current_directory()
        db_path = os.path.join(current_directory, DB_FOLDER)
        ensure_directory_exists(db_path)
        relative_images_path = os.path.join(db_path)

        if DEBUG.upper() == "TRUE":
            click.echo(f"Current directory: {current_directory}")
            click.echo(f"Database folder: {relative_images_path}")
        
        image_path = get_latest_modified_file(relative_images_path)
        if DEBUG.upper() == "TRUE":
            print("Latest modified file:", image_path)

        # Build the connect_command to connect the image file to the next available nbd device
        connect_command = f"sudo qemu-nbd --connect=/dev/{next_nbd} -f raw {image_path}"

        # Execute the command
        if DEBUG.upper() == "TRUE":
            subprocess.run(connect_command, shell=True)
        else:
            subprocess.run(connect_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        image_name = extract_upper_image_name(image_path)
        if DEBUG.upper() == "TRUE":
            print("FAT32 Partition Name Generated:", image_name)

        # Build the format_command to format the mounted image with FAT32 filesystem and the specified name
        format_command = f"sudo mkfs.fat -F 32 -n \"{image_name}\" -I /dev/{next_nbd}"

        # Execute the command
        if DEBUG.upper() == "TRUE":
            subprocess.run(format_command, shell=True)
        else:
            subprocess.run(format_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Build the disconnect_command for the image on the NBD device
        disconnect_command = f"sudo qemu-nbd --disconnect /dev/{next_nbd}"

        # Execute the command
        if DEBUG.upper() == "TRUE":
            subprocess.run(disconnect_command, shell=True)
        else:
            subprocess.run(disconnect_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    else:
        print("No available NBD devices found.")

def unmount_disk_image():
    click.clear()
    host_os = get_host_os()
    
    if DEBUG.upper() == "TRUE":
            print(f"Detected Operating System: {host_os}")

    if host_os == "Linux":
        if DEBUG.upper() == "TRUE":
            print("Unmounting image on Linux...")

        # Check and load nbd module
        if DEBUG.upper() == "TRUE":
            print("Checking if nbd module is loaded...")
        check_and_load_nbd_module()

        # Parsing lsblk output to construct a menu, begin by first finding all available NBD devices
        print("Listing Connected NBD devices...")
        nbd_devices = get_nbd_devices()
        if nbd_devices:
            if DEBUG.upper() == "TRUE":
                print("Available NBD Devices:", ', '.join(nbd_devices.keys()))
        else:
            print("No NBD devices found. How'd you get to this point?")

        # Continue by filtering down to only connected devices (NBDs with size larger than 0B)
        connected_nbd_devices = get_connected_nbd_devices()
        if connected_nbd_devices:
            print("Connected NBD Devices:")
            for i, (device, _) in enumerate(connected_nbd_devices.items(), start=1):
                nbd_device_info = get_nbd_device_info(device)
                mount_point = nbd_device_info.get('mount_point')
                disk_size = nbd_device_info.get('size')
                if mount_point:
                    pretty_disk_name = extract_image_name(mount_point)
                    print(f"{i}. {device} [{disk_size}] - Mounted as: {pretty_disk_name}")
                else:
                    print(f"{i}. {device} [{disk_size}] - Not Mounted")
            
            # Present menu for choosing an nbd device
            selected_index = input("Enter the number of the NBD device you want to unmount (or type 'c' to cancel): ")
            if selected_index.lower() == 'c':
                print("Operation canceled.")
            else:
                try:
                    selected_index = int(selected_index)
                    if selected_index < 1 or selected_index > len(connected_nbd_devices):
                        raise ValueError
                    selected_device = list(connected_nbd_devices.keys())[selected_index - 1]
                    print(f"You selected {selected_device}.")
                    
                    # Probe for information about the selected device
                    nbd_device_info = get_nbd_device_info(selected_device)
                    if nbd_device_info:
                        if DEBUG.upper() == "TRUE":
                            print(f"Device: {nbd_device_info['device']}")
                            print(f"Size: {nbd_device_info['size']}")
                            print(f"Mount Point: {nbd_device_info['mount_point']}")
                            print(f"Number of Partitions: {nbd_device_info['total_partitions']}")
                            print(f"Partitions: {', '.join(nbd_device_info['partitions']) if nbd_device_info['partitions'] else 'None'}")
                        
                        # Check if the NBD device is not mounted
                        if not nbd_device_info['mount_point']:
                            disconnect_choice = click.confirm("The selected NBD device is not mounted to a directory. Do you want to disconnect it?", default=True)
                            if disconnect_choice:
                                if DEBUG.upper() == "TRUE":
                                    print("Disconnecting the NBD device...")

                                # Build the disconnect_nbd_command for the NBD device
                                disconnect_nbd_command = f"sudo qemu-nbd --disconnect /dev/{nbd_device_info['device']}"

                                # Execute the command
                                if DEBUG.upper() == "TRUE":
                                    subprocess.run(disconnect_nbd_command, shell=True)
                                else:
                                    subprocess.run(disconnect_nbd_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                                print("Successfully disconnected chosen NBD Device.")
                                return
                            else:
                                print("Operation canceled.")
                    else:
                        print("Failed to get NBD device information.")

                    # Placeholder for further actions with the selected NBD device if it is mounted
                    
                    # Begin by getting the mount point folder name
                    full_mnt_path = nbd_device_info['mount_point']
                    mnt_folder = get_last_directory_name(nbd_device_info['mount_point'])
                    if DEBUG.upper() == "TRUE":
                        print(f"The NBD device is mounted to the directory: {mnt_folder}")

                    # Build the unmount_command for the image on the NBD device
                    unmount_command = f"sudo umount {full_mnt_path}"

                    # Execute the unmount command
                    if DEBUG.upper() == "TRUE":
                        subprocess.run(unmount_command, shell=True)
                    else:
                        subprocess.run(unmount_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                    # We can now remove the directory as it's no longer in use
                    ensure_directory_exists_destructive(full_mnt_path)

                    if DEBUG.upper() == "TRUE":
                        print("Disconnecting the NBD device...")

                    # Build the disconnect_nbd_command for the NBD device
                    disconnect_nbd_command = f"sudo qemu-nbd --disconnect /dev/{nbd_device_info['device']}"

                    # Execute disconnection command
                    if DEBUG.upper() == "TRUE":
                        subprocess.run(disconnect_nbd_command, shell=True)
                    else:
                        subprocess.run(disconnect_nbd_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                    print("Successfully Unmounted and Disconnected the chosen NBD Device.")

                except ValueError:
                    print("Invalid input. Please enter a valid number.")
        else:
            print("No connected NBD devices found. Have you mounted any images yet?")

    elif host_os == "Windows":
        print("Mounting image on Windows has not been implemented yet")
        # Placeholder comment for Windows unmounting logic, stating its not done yet.
    elif host_os == "Darwin":
        if DEBUG.upper() == "TRUE":
            print("Unmounting image on macOS...")

        # Step 1: Execute ls -l command in /dev/ directory
        ls_output = subprocess.run(['ls', '-l', '/dev/'], capture_output=True, text=True)
        
        # Step 2: Filter output to only include files that start with "disk"
        disk_lines = [line for line in ls_output.stdout.split('\n') if line.startswith('brw') or line.startswith('w-')]
        
        # Step 3: Further filter output to only include disks owned by the user
        user_disks = [line.split()[-1] for line in disk_lines if line.split()[2] == 'royalgraphx']
        
        if DEBUG.upper() == "TRUE":
            print("User disks:")
            print(user_disks)

        # If the user does not own any disks, we simply exit out to main menu with a print
        if not user_disks:
            print("You do not have any owned disks. Have you mounted any images yet?")
            return
        
        # Step 4: Create a list of diskroots (disks without partitions)
        user_diskroots = [disk for disk in user_disks if not any(char.isalpha() for char in disk.split('disk')[1])]

        if DEBUG.upper() == "TRUE":
            print("User disk roots:")
            print(user_diskroots)
            
        # Step 5: Get partition information for each disk root
        for disk_root in user_diskroots:
            disk_info_output = subprocess.run(['diskutil', 'list', f'/dev/{disk_root}'], capture_output=True, text=True)
            print(f"Partition information for {disk_root}:")
            print(disk_info_output.stdout)

        # Step 6: Present user with choices and allow them to select a disk
        print("Listing available disks to unmount...")
        for i, disk_root in enumerate(user_diskroots, start=1):
            print(f"{i}. {disk_root}")

        selected_index = input("Enter the number of the disk you want to unmount (or type 'c' to cancel): ")
        if selected_index.lower() == 'c':
            print("Operation canceled.")
            return
        try:
            selected_index = int(selected_index)
            if selected_index < 1 or selected_index > len(user_diskroots):
                raise ValueError
            selected_disk = user_diskroots[selected_index - 1]
            print(f"You selected {selected_disk} to unmount.")
            
            # Step 7: Unmount the selected disk
            unmount_command = ['diskutil', 'unmountDisk', f'/dev/{selected_disk}']
            unmount_output = subprocess.run(unmount_command, capture_output=True, text=True)
            if unmount_output.returncode == 0:
                print(f"{selected_disk} has been successfully unmounted.")
                # Step 8: Eject the disk
                eject_command = ['diskutil', 'eject', f'/dev/{selected_disk}']
                eject_output = subprocess.run(eject_command, capture_output=True, text=True)
                if eject_output.returncode == 0:
                    print(f"{selected_disk} has been successfully ejected.")
                else:
                    print(f"Error occurred while ejecting {selected_disk}.")
            else:
                print(f"Error occurred while unmounting {selected_disk}.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

    else:
        print("Unknown operating system. Unable to unmount images.")
        # Placeholder comment for handling unknown operating systems

def exit_program():
    click.echo("Exiting DiskProvision. Goodbye!")
    raise SystemExit

if __name__ == "__main__":
    main()