<p align="center">
<img src="https://i.imgur.com/76J8IOv.png" width="500px" />
<br>
<a href="https://www.nexusmods.com/skyrimspecialedition/mods/97864"><img src="https://i.imgur.com/STsBXT6.png" height="60px"/> </a>
<a href="https://ko-fi.com/cutleast"><img src="https://i.imgur.com/KcPrhK5.png" height="60px"/> </a>
<br>

# Please Note!!!

**I take no responsibility for any problems that may occur or any assets that get redistributed without permission!**

# Description

This is an automated patch creator for Dynamic Interface Patcher ([NexusMods](https://www.nexusmods.com/skyrimspecialedition/mods/96891) | [GitHub](https://github.com/Cutleast/Dynamic-Interface-Patcher)).
The tool requires a finished SWF patch to work. Those are created in FFDec manually.

# Features

- Fully automated patch creation
- Automatic extraction of BSA
- Automatic extraction of different shapes

# Usage

1. Create your patched SWF files in FFDec as you would publish them.
2. Start DICK.exe.
3. Put in the path to the folder with your patched SWF files (same folder structure as the original mod without BSA).
4. Put in the path to the original mod.
5. Click on *Create Patch!*
6. The output gets generated in a `Output` folder where DICK.exe is located.
7. If the original mod had a BSA, create a folder with the full filename of the BSA in the `Patch` folder and move everything that's normally in the BSA in it.

For example:

`Direct output`:

```
Output (root folder)
├── Patch
|   └── interface
|       ├── racemenu
|       |   └── buttonart.json
|       └── racesex_menu.json
└── Shapes
    ├── shape_1.svg
    └── shape_2.svg
```

`Finished output` (with created BSA folder):

```
Output (root folder)
├── Patch
|   └── RaceMenu.bsa
|       └── interface
|           ├── racemenu
|           |   └── buttonart.json
|           └── racesex_menu.json
└── Shapes
    ├── shape_1.svg
    └── shape_2.svg
```

8. Now you can publish the content of the `Output` folder in a subfolder named like your patch (for eg. `Nordic UI - RaceMenu - DIP Patch`) so that the folder structure in Skyrim's data folder would look like this:

```
data (in Skyrim's installation directory)
└── Nordic UI - RaceMenu - DIP Patch (the Output folder)
    ├── Patch
    |   └── RaceMenu.bsa
    |       └── interface
    |           ├── racemenu
    |           |   └── buttonart.json
    |           └── racesex_menu.json
    └── Shapes
        ├── shape_1.svg
        └── shape_2.svg
```

9. The usage of a simple FOMOD is strongly recommended to avoid mod managers warning that the mod does not look correct for the data folder.

Other examples are the official patches found below.

# Official Patches

To avoid duplicate patches, see [here](https://github.com/Cutleast/Dynamic-Interface-Patcher/blob/main/OfficialPatches.md) for a list of released and planned patches.

# How it works

Creates patch data by comparing patched mod with original mod:

1. Copy patched mod and original mod to a temp folder.
2. Extract original mod files from BSAs if required and possible.
3. Convert patched and original SWFs to XMLs.
4. Compare patched and original XMLs.
5. Export different shapes via ffdec commandline.

The following three steps are required since FFDec makes more changes
to a file when replacing shapes. Therefore, the shapes are replaced in the original files to avoid obsolete differences.

6. Replace shapes of the original file.
7. Convert modified original SWFs to XMLs, again.
8. Compare original and patched file.

And then to finish the patch:

9. Create output folder with JSON files for each modified SWF.
10. Copy finished patch data to `<current directory>/Output`.

# Contributing

### 1. Feedback (Suggestions/Issues)

If you encountered an issue/error or you have a suggestion, create an issue under the "Issues" tab above.

### 2. Code contributions

1. Install Python 3.11 (Make sure that you add it to PATH!)
2. Clone repository
3. Open terminal in repository folder
4. Type in following command to install all requirements (Using a virtual environment is strongly recommended!):
   `pip install -r requirements.txt`

### 3. Execute from source

1. Open terminal in src folder
2. Execute main file
   `python main.py`

### 4. Compile and build executable

1. Follow the steps on this page [Nuitka.net](https://nuitka.net/doc/user-manual.html#usage) to install a C Compiler
2. Run `build.bat` with activated virtual environment from the root folder of this repo.
3. The executable and all dependencies are built in the main.dist-Folder.

# Credits

- Qt by The [Qt Company Ltd](https://qt.io)
- [bethesda-structs](https://github.com/stephen-bunn/bethesda-structs) by [Stephen Bunn](https://github.com/stephen-bunn)
- [FFDec](https://github.com/jindrapetrik/jpexs-decompiler) by [Jindra Petřík](https://github.com/jindrapetrik)
