#!/usr/bin/python
import os
import re
import configparser
import ast
import xml.etree.ElementTree as ET

import LocalCopy
import RemoteCopy

global_config = {}


def print_progress(processed_items, total_items, last_percentage_printed=-2):
    percentage_complete = int((processed_items / total_items) * 100)

    if percentage_complete >= last_percentage_printed + 2:
        print(f"{percentage_complete}% ({processed_items}/{total_items} items processed..)")
        last_percentage_printed = percentage_complete

    return last_percentage_printed


# Get good list and return as python list
def parse_xml(xml_file):
    print("Parsing Mame XML..")
    screenless = configparser.ConfigParser(allow_no_value=True)
    screenless.read(global_config["screenless_ini"])
    screenless_items = dict(screenless.items('ROOT_FOLDER'))
    tree = ET.parse(xml_file)
    root = tree.getroot()
    mame_list = {}
    status_good, emulation_good, chd_req = 0, 0, 0
    machines = root.findall('machine')
    machine_count = len(machines)
    processed_roms = 0
    last_percentage_printed = -2
    for machine in machines:
        processed_roms += 1
        last_percentage_printed = print_progress(processed_roms, len(machines), last_percentage_printed)
        name = machine.get('name')
        if name in global_config["blacklist_roms"]:
            continue
        driver = machine.find('driver')
        description = machine.find('description').text
        manufacturer = machine.find('manufacturer')
        if (name not in screenless_items.keys() and driver is not None and not any(
                (re.findall(r'\(proto|prototype\)|\(beta\)', description, re.IGNORECASE))) and
                (manufacturer is None or
                 not any(re.findall(r'beta.*bootleg|bootleg.*beta', manufacturer.text, re.IGNORECASE)))):
            status = driver.get('status')
            emulation = driver.get('emulation')
            if status == "good" or emulation == "good":
                mame_rom = {
                    # 'name': name,
                    'description': description,
                    'chd_req': False,
                    'status_good': False,
                    'emulation_good': False}

                disk = machine.find('disk')
                if disk is not None:
                    if disk.get("status") != "nodump":
                        mame_rom['chd_req'] = True
                        if machine.get('cloneof'):
                            mame_rom['chd_name'] = machine.get('cloneof')
                        else:
                            mame_rom['chd_name'] = name
                    chd_req += 1
                if status == "good":
                    mame_rom['status_good'] = True
                    status_good += 1
                if emulation == "good":
                    mame_rom['emulation_good'] = True
                    emulation_good += 1
                if "mame_rom" in locals():
                    # print(mame_rom)
                    mame_list[name] = mame_rom
    # print(status_good, emulation_good, chd_req, len(mame_list))
    print("Parse completed..")
    return mame_list


def categorize_list(mame_list):
    print("It's time to categorize that huge list!.")
    cat_list = []
    categories = configparser.ConfigParser(allow_no_value=True)
    categories.read(global_config["category_ini"])
    genres = configparser.ConfigParser(allow_no_value=True)
    genres.read(global_config["genre_ini"])

    # Blacklisted cleanup
    for genre in global_config["blacklist_genres"]:
        for (rom_name, _) in genres.items(genre):
            if rom_name in mame_list.keys():
                mame_list.pop(rom_name)

    for category in categories.sections():
        if category == "FOLDER_SETTINGS" or category == "ROOT_FOLDER":
            continue

        for (rom_name, _) in categories.items(category):
            if rom_name in mame_list.keys():
                clean_category = category.lstrip("Arcade:").strip()
                mame_list[rom_name]["category"] = clean_category
                cat_list.append(rom_name)

    for unlisted in set(cat_list) ^ set(mame_list.keys()):
        mame_list[unlisted]["category"] = "Unlisted"
    # print(mame_list, len(mame_list))
    print("Done.")
    return mame_list


# Finding folder to copy, also mature filter too!.
def generate_folder_name(cat_name):
    is_mature = False
    if "* Mature *" in cat_name:
        is_mature = True
        cat_name_list = [global_config["mature_rom_folder"]] + [x.strip().rstrip(".") for x in
                                                                cat_name.replace("* Mature *", "").split("/")]
    else:
        cat_name_list = [x.strip().rstrip(".") for x in cat_name.split("/")]
    path_name = "/".join(cat_name_list)

    return path_name, is_mature


def copy_to_folder(mame_list):
    missing_roms, missing_chd = [], []

    # Check Missing roms
    for (name, info) in mame_list.items():
        # print(name, info)
        if not os.path.isfile(os.path.join(global_config["rom_dir"], name + ".zip")):
            missing_roms.append(name)
        if (info["chd_req"] and
                not os.path.isdir(os.path.join(global_config["chd_dir"], info["chd_name"])) and
                info["chd_name"] not in missing_chd):
            missing_chd.append(info["chd_name"])

    if len(missing_roms) > 0 or len(missing_chd) > 0:
        print("Some files are missing!")
        if len(missing_roms) > 0:
            missing_roms.sort()
            print("Missing ROMs: ")
            print(', '.join(missing_roms))

        if len(missing_chd) > 0:
            print("Missing CHDs: ")
            missing_chd.sort()
            print(', '.join(missing_chd))

    user_input = input('Would you like to continue copying roms? (Y/N): ')
    if user_input.lower() in ['yes', 'y']:
        # Copy time!
        if global_config["copy_path"].startswith("smb://"):
            filecopy = RemoteCopy.RemoteCopy(global_config["copy_path"])
        else:
            filecopy = LocalCopy.LocalCopy(global_config["copy_path"])

        processed_roms = 0
        last_percentage_printed = -2
        for (name, info) in mame_list.items():
            processed_roms += 1
            last_percentage_printed = print_progress(processed_roms, len(mame_list), last_percentage_printed)

            folder_to_copy, is_mature = generate_folder_name(info["category"])
            if not global_config["allow_mature"] and is_mature:
                print(name, "MATURE FILTERED!")
                continue

            # Copy Files
            if info["chd_req"]:
                filecopy.copy(os.path.join(global_config["chd_dir"], info["chd_name"]),
                              os.path.join(folder_to_copy, info["chd_name"]))
            filecopy.copy(os.path.join(global_config["rom_dir"], name + ".zip"), folder_to_copy)


def start_check():
    settings = configparser.ConfigParser(converters={'list': lambda x: [i.strip() for i in x.split(',')]})
    settings.read("settings.ini")
    for (key, val) in settings.items("config"):
        global_config[key] = val
    global_config["blacklist_genres"] = ast.literal_eval(global_config["blacklist_genres"])
    global_config["blacklist_roms"] = ast.literal_eval(global_config["blacklist_roms"])
    # print(global_config["chd_dir"])


def main():
    start_check()
    mame_list = parse_xml(global_config["mame_xml"])
    categorized_mame_list = categorize_list(mame_list)
    copy_to_folder(categorized_mame_list)


if __name__ == '__main__':
    main()

# possible genres to blacklist:
# 'TTL * Ball & Paddle',
# 'TTL * Driving',
# 'TTL * Maze',
# 'TTL * Quiz',
# 'TTL * Shooter',
# 'TTL * Sports',
# 'Watch'
