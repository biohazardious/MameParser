# Ultimate Mame Rom Clean, Categorize And Upload Script

Yet another Python Script to clean non-working roms, protos, betas etc. and categorize by genres. It also copies files
to destination folder.

This script is mostly written to use with EmulationStation operating systems like Batocera, RecalBox, RetroPie etc. but
you can use it if you need to categorize that bulk of MAME roms.

## What does this script do

- Parse mameXXXX.xml, read rom data, filter non-working roms, prototypes, betas screenless devices, mechanical devices etc etc..
- Read Genres and categorize roms in folders
- Different folder for CHD and ROM folders
- Lists missing ROM and CHD files, so you can download only necessary files instead of everything (mostly useful for
  CHDs)
- Option for blacklist roms
- Option for blacklist unwanted genres
- Optional adult rom filter :)
- Separate adult roms to another folder
- Copy ROMs and CHDs to local location
- Upload ROMs and CHDs to a remote location via samba sharing
- Update roms if source file different from destination
- Don't copy/upload source file if same with destination

## What does this script don't

- Download any rom file
- Download any mame information file
- Scrape file datas, videos, images etc.
- Compare only filenames and filesize only, no MD5 or etc. cos of speed reasons.

## TODO (Planning)

- FTP and SFTP support
- Test in Windows
- Maybe a UI... Maybe...

## How to use

- Set your path's in settings.ini
- Put necessary MAME files on MameFiles or your specific destination
- It's important to use same MAME version for all of your MAME specific files
-
    - Ex: if you are using 0.251 romset
-
    - use mame0251.xml (can found in Mame official webpage)
-
    - use categories.ini, catlist.ini, genre.ini, screenless.ini from mame extras 0.251
-
    - use **non-merged** mame 0.251
-
    - use 0.251 mame CHD files

When everything set and you are ready to go, just exec MameCleaner.py

Tested in linux and Batocera Operating system but should works for other distros like RecalBox, RetroPie etc.

**Note:** Using non-merged MAME roms hugely suggested. 