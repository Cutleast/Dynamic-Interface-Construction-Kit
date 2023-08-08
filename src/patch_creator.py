"""
Part of Dynamic Interface Construction Kit (DICK).
Contains Patcher class.

Licensed under Attribution-NonCommercial-NoDerivatives 4.0 International
"""


import logging
import os
import shutil
import tempfile as tmp
import xml.etree.ElementTree as ET
from pathlib import Path

import jstyleson as json
import bsa_extractor as bsa

import errors
import ffdec
import utils
from main import MainApp


PATCHER_CONFIG: dict[str, list[str] | str] = json.loads((Path(".").resolve() / "assets" / "config.json").read_text())
FILE_BLACKLIST: list[str] = PATCHER_CONFIG.get("file_blacklist", [])
EXPORT_FORMAT: str = PATCHER_CONFIG.get("export_format", "svg")
CREATION_WHITELIST: list[str] = PATCHER_CONFIG.get("creation_whitelist", [])
LIST_TAGS: list[str] = PATCHER_CONFIG.get("list_tags", [])
FILTER_WHITELIST: list[str] = PATCHER_CONFIG.get("filter_whitelist", [])
TYPE_BLACKLIST: list[str] = PATCHER_CONFIG.get("type_blacklist", [])
TAG_BLACKLIST: list[str] = PATCHER_CONFIG.get("tag_blacklist", [])
ATTR_BLACKLIST: list[str] = PATCHER_CONFIG.get("attr_blacklist", [])
SHAPE_TYPES: list[str] = PATCHER_CONFIG.get("shape_types", [])


class PatchCreator:
    """
    Class for Patch Creator.
    """

    original_mod_path: Path = None
    patched_mod_path: Path = None
    ffdec_interface: ffdec.FFDec = None
    tmpdir: Path = None
    patch_data: dict[Path, dict] = None

    def __init__(self, app: MainApp, patched_mod_path: Path, original_mod_path: Path):
        self.app = app
        self.patched_mod_path = patched_mod_path
        self.original_mod_path = original_mod_path

        self.log = logging.getLogger(self.__repr__())
        self.log.addHandler(self.app.log_str)
        self.log.setLevel(self.app.log.level)

        self.load_patch()

    def __repr__(self):
        return "PatchCreator"

    def load_patch(self):
        self.patch_data = {}

        self.log.info("Loading patched mod...")

        for swf_file in self.patched_mod_path.glob("**\\*.swf"):
            if swf_file.name in FILE_BLACKLIST:
                continue
            swf_file = swf_file.relative_to(self.patched_mod_path)
            self.patch_data[swf_file] = {}
            self.log.debug(f"Found '{swf_file}'.")

        self.log.info(f"Loaded patched mod with {len(self.patch_data)} SWF file(s).")

    def copy_files(self):
        """
        Copies all required files to the temp folder.
        """

        self.log.info("Copying patched files...")

        for file in self.patch_data.keys():
            src_path = self.patched_mod_path / file
            dst_path = self.tmpdir / "Patch" / file

            os.makedirs(dst_path.parent, exist_ok=True)
            shutil.copyfile(src_path, dst_path)
        
        self.log.info("Copying original mod files...")

        for file in self.patch_data.keys():
            src_path = self.original_mod_path / file
            dst_path = self.tmpdir / "Original" / file

            if not src_path.exists():
                for bsa_file in self.original_mod_path.glob("*.bsa"):
                    bsa_archive = bsa.BSAArchive.parse_file(str(bsa_file))
                    if bsa_archive.contains_file(file):
                        dst_path = self.tmpdir / "Original"
                        os.makedirs(dst_path, exist_ok=True)
                        bsa_archive.extract_file(to_dir=dst_path, file=file)
                        self.log.debug(f"Extracted '{file}' from '{bsa_file}'.")
                        break
                else:
                    raise errors.SWFFileNotFoundError(f"File '{file}' not found in Original mod!")
            else:
                os.makedirs(dst_path.parent, exist_ok=True)
                shutil.copyfile(src_path, dst_path)
        
        self.log.info("Patched and original files ready to create patch.")

    def convert_patched_swfs2xmls(self):
        for swf_file in self.patch_data.keys():
            self.log.info(f"Converting patched '{swf_file}'...")

            patched_swf = self.tmpdir / "Patch" / swf_file

            # Initialize ffdec interface if required
            if self.ffdec_interface is None:
                self.ffdec_interface = ffdec.FFDec(patched_swf, self.app)

            # Convert patched file
            self.ffdec_interface.swf_path = patched_swf
            self.ffdec_interface.swf2xml()

    def convert_original_swfs2xmls(self):
        for swf_file in self.patch_data.keys():
            self.log.info(f"Converting original '{swf_file}'...")

            original_swf = self.tmpdir / "Original" / swf_file

            # Initialize ffdec interface if required
            if self.ffdec_interface is None:
                self.ffdec_interface = ffdec.FFDec(original_swf, self.app)

            # Convert original file
            self.ffdec_interface.swf_path = original_swf
            self.ffdec_interface.swf2xml()

    def compare_xmls(self):
        """
        Compares XML files and stores differences as values in self.patch_data.
        """

        for swf_file in self.patch_data.keys():
            xml_file = swf_file.with_suffix(".xml")
            self.log.info(f"Processing '{xml_file}'...")

            original_xml_path = self.tmpdir / "Original" / xml_file
            patched_xml_path = self.tmpdir / "Patch" / xml_file

            original_xml = ET.parse(str(original_xml_path)).getroot()
            patched_xml = ET.parse(str(patched_xml_path)).getroot()

            # Prepare xmls
            original_xml = self.split_frames(original_xml)
            patched_xml = self.split_frames(patched_xml)

            patch_data = self.compare_elements(original_xml, patched_xml, ".", "swf")

            if patch_data:
                self.patch_data[swf_file]["swf"] = patch_data

    @staticmethod
    def compare_elements(
        original_root: ET.Element,
        patched_element: ET.Element,
        cur_xpath: str,
        root: str
    ):
        result = {}

        if (patched_element.get("type", "item") not in TYPE_BLACKLIST
            and patched_element.tag not in TAG_BLACKLIST):
            if patched_element.tag != root:
                cur_xpath += "/" + patched_element.tag

                # Find original element
                # because element order can differ
                for key, value in patched_element.items():
                    if key in FILTER_WHITELIST:
                        cur_xpath += f"[@{key}='{value}']"
            original_element = original_root.find(cur_xpath)

            # If element is found, compare attributes
            if original_element is not None:
                # Compare attributes of the current elements
                for attribute, value in patched_element.items():
                    if original_value := original_element.get(attribute):
                        if (value == original_value) and (attribute in FILTER_WHITELIST):
                            result[f"#{attribute}"] = value
                        elif (value != original_value) and (attribute not in ATTR_BLACKLIST):
                            result[f"~{attribute}"] = value
                    elif attribute in FILTER_WHITELIST:
                        result[f"#{attribute}"] = value

            # If element is not found but in whitelist, create it
            elif patched_element.tag in CREATION_WHITELIST:
                print(f"Creating element '{patched_element.tag}' at '{cur_xpath}'...")

                new_attrib = {}
                for attribute, value in patched_element.items():
                    if attribute not in ATTR_BLACKLIST:
                        new_attrib[f"~{attribute}"] = value
                
                result = new_attrib

        # Compare child elements
        for patched_child in patched_element.findall("./"):
            child_result = PatchCreator.compare_elements(
                original_root,
                patched_child,
                cur_xpath,
                root
            )
            tag = patched_child.tag

            if isinstance(result, dict):
                if "/" in cur_xpath:
                    _, parent = cur_xpath.rsplit("/", 1)
                    parent, *_ = parent.split("[")
                else:
                    parent = root

                if (tag in result.keys()) or (parent in LIST_TAGS):
                    result = list(result.values())
                elif child_result:
                    result[tag] = child_result

            if (isinstance(result, list)
                and child_result
                and child_result not in result):
                result.append(child_result)

        # Remove unchanged elements
        if isinstance(result, dict):
            if all([
                key.startswith("#")
                for key in result.keys()
            ]):
                result.clear()

        return result

    def extract_shapes(self):
        """
        Extracts different shapes to shapes folder.
        """

        self.log.info("Exporting patched shapes...")
        shapes_folder = self.tmpdir / "Output" / "Shapes"

        for swf_file, patch_data in self.patch_data.items():
            xml_file = swf_file.with_suffix(".xml")

            original_xml_path = self.tmpdir / "Original" / xml_file
            patched_xml_path = self.tmpdir / "Patch" / xml_file
            patched_swf_path = self.tmpdir / "Patch" / swf_file

            original_xml = ET.parse(str(original_xml_path))
            patched_xml = ET.parse(str(patched_xml_path))

            different_shapes = self.get_different_shapes(original_xml, patched_xml)

            if different_shapes:
                self.log.info(f"Processing '{swf_file}'...")
                patch_data["shapes"] = []
                outpath = shapes_folder / swf_file.stem
                os.makedirs(outpath, exist_ok=True)

                self.ffdec_interface.swf_path = patched_swf_path
                self.ffdec_interface.export_shapes(different_shapes, outpath, EXPORT_FORMAT)

                for shape in outpath.glob("./*"):
                    shape_id = shape.stem
                    patch_data["shapes"].append({
                        "id": shape_id,
                        "fileName": str(shape.relative_to(shapes_folder))
                    })
                patch_data["shapes"].sort(
                    key=lambda shape: int(shape["id"])
                )

    def patch_shapes(self):
        """
        Replaces shapes in original files to
        exclude shape-related differences when creating
        the actual patch.
        """

        self.log.info("Replacing shapes in original files...")

        for swf_file, patch_data in self.patch_data.items():
            shapes: dict[Path, list[int]] = {}

            for shape_data in patch_data.get("shapes", []):
                shape_path: Path = (self.tmpdir / "Output" / "Shapes" / shape_data["fileName"]).resolve()

                if not shape_path.is_file():
                    self.log.error(
                        f"Failed to patch shape with id '{shape_data['id']}': \
File '{shape_path}' does not exist!"
                    )
                    continue

                shape_ids: list[int] = [
                    int(shape_id)
                    for shape_id in shape_data["id"].split(",")
                ]

                if shape_path in shapes:
                    shapes[shape_path] += shape_ids
                else:
                    shapes[shape_path] = shape_ids

            if shapes:
                self.log.info(f"Processing '{swf_file}'...")
                original_swf = self.tmpdir / "Original" / swf_file
                self.ffdec_interface.swf_path = original_swf
                self.ffdec_interface.replace_shapes(shapes)

    @staticmethod
    def get_different_shapes(original_xml: ET.ElementTree, patched_xml: ET.ElementTree):
        different_shapes: list[str] = []

        original_shapes: list[ET.Element] = []
        for shape_type in SHAPE_TYPES:
            original_shapes += original_xml.findall(f"*/item[@type='{shape_type}'][@shapeId]")

        for original_shape in original_shapes:
            shape_id = original_shape.attrib["shapeId"]
            shape_type = original_shape.attrib["type"]

            patched_xpath = f"*/item[@type='{shape_type}'][@shapeId='{shape_id}']"
            patched_shape = patched_xml.find(patched_xpath)
            if PatchCreator.check_if_different(original_shape, patched_shape):
                different_shapes.append(shape_id)

        return different_shapes

    @staticmethod
    def check_if_different(elem1: ET.Element, elem2: ET.Element):
        # Check if element attributes are different
        if elem1.attrib != elem2.attrib:
            return True

        # Compare children recursively
        for child1, child2 in zip(elem1, elem2):
            if PatchCreator.check_if_different(child1, child2):
                return True

        return False

    @staticmethod
    def split_frames(xml_element: ET.Element):
        """
        Split frames in xml_element recursively
        and return xml_element with frames.
        """

        new_frame = ET.Element("frame")
        current_frame = 1
        new_frame.set("frameId", str(current_frame))
        new_frame_subtags = ET.Element("subTags")
        new_frame.append(new_frame_subtags)

        frame_delimiters = xml_element.findall("./item[@type='ShowFrameTag']")

        # Iterate over all child elements
        for child in xml_element.findall("./"):
            # Split child recursively
            child = PatchCreator.split_frames(child)

            # If child is not a frame delimiter
            if len(frame_delimiters) > 1:
                # Remove child from xml_element
                xml_element.remove(child)

                # If child is not a frame delimiter
                if child.get("type") != "ShowFrameTag":
                    # Append child to current frame
                    new_frame_subtags.append(child)

                # If child is a frame delimiter
                elif child in frame_delimiters:
                    xml_element.append(new_frame)
                    # Create new frame
                    new_frame = ET.Element("frame")
                    current_frame += 1
                    new_frame.set("frameId", str(current_frame))
                    new_frame_subtags = ET.Element("subTags")
                    new_frame.append(new_frame_subtags)

        return xml_element

    @staticmethod
    def unsplit_frames(xml_element: ET.Element):
        """
        This functions is a reverse of split_frames.
        """

        for child in xml_element.findall("./"):
            frames = child.findall("./frame")

            for frame in frames:
                child.remove(frame)

                for frame_child in frame.findall("./subTags/"):
                    child.append(frame_child)
                
                frame_tag = ET.Element("item")
                frame_tag.set("type", "ShowFrameTag")
                child.append(frame_tag)

            PatchCreator.unsplit_frames(child)

        return xml_element

    def create_output(self):
        """
        Creates output folder with JSON files from self.patch_data.
        """

        output_folder = self.tmpdir / "Output" / "Patch"

        for swf_file, patch_data in self.patch_data.items():
            shapes_patch = patch_data.get("shapes")
            swf_patch = patch_data.get("swf")

            if (not shapes_patch) and (not swf_patch):
                continue

            # Reverse order
            patch_data = {}
            if shapes_patch:
                patch_data["shapes"] = shapes_patch
            if swf_patch:
                patch_data["swf"] = swf_patch

            json_file = swf_file.with_suffix(".json")

            self.log.info(f"Writing '{json_file}'...")

            json_file = output_folder / json_file
            os.makedirs(json_file.parent, exist_ok=True)

            with open(json_file, "w") as file:
                file.write(json.dumps(patch_data, indent=4))

    def finish_patch(self):
        """
        Copies output folder to current directory.
        """

        src_folder = self.tmpdir / "Output"
        dst_folder = Path(".").resolve() / "Output"

        self.log.info(f"Copying output to '{dst_folder}'...")

        if dst_folder.is_dir():
            shutil.rmtree(dst_folder)
            self.log.info("Deleted existing output folder.")
        
        shutil.copytree(src_folder, dst_folder)

    def create_patch(self):
        """
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
        """

        self.log.info("Creating patch data...")

        # 0. Create temp folder
        with tmp.TemporaryDirectory(prefix="DICK_") as tmpdir:
            self.tmpdir = Path(tmpdir).resolve()

            self.log.debug(f"Created temporary folder at '{self.tmpdir}'.")

            # 1. Copy patched mod and original mod files
            # 2 and extract BSAs if possible and necessary
            self.copy_files()

            # 3. Convert patched and original SWFs to XMLs.
            self.convert_original_swfs2xmls()
            self.convert_patched_swfs2xmls()

            # 5. Export different shapes via ffdec commandline
            self.extract_shapes()

            # 6. Replace shapes in original files.
            self.patch_shapes()

            # 7. Convert original SWFs to XMLs again.
            self.convert_original_swfs2xmls()

            # 4. Compare patched and original XMLs.
            self.compare_xmls()

            # 9. Create output folder with JSON files for each modified SWF.
            self.create_output()

            # 10. Copy finished output folder
            self.finish_patch()

        self.app.done_signal.emit()
