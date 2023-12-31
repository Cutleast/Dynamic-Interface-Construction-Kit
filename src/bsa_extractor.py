"""
Part of Dynamic Interface Construction Kit (DICK).
Contains modfied BSA class.

Licensed under Attribution-NonCommercial-NoDerivatives 4.0 International
"""


from pathlib import Path
from bethesda_structs.archive.bsa import BSAArchive as _BSAArchive


class BSAArchive(_BSAArchive):
    """
    Modified version of BSAArchive class.
    Has method to extract single files.
    """

    def contains_file(
            self,
            file: str | Path
    ):
        """
        Checks if <file> is in BSA.

        Parameters:
            file: str or Path, relative to BSA's root folder

        Returns:
            file_exists: bool
        """

        archive_files = list(self.iter_files())

        for archive_file in archive_files:
            if Path(archive_file.filepath) == Path(file):
                return True

        return False

    def extract_file(
            self,
            to_dir: str | Path,
            file: str | Path
    ):
        """
        Extracts <file> from BSA.

        Parameters:
            to_dir: str, directory to extract <file> to.
            file: str, relative path to BSA's root folder.
        """

        to_dir = Path(to_dir)

        if not to_dir.is_dir():
            raise NotADirectoryError(f"No directory {to_dir!r} exists")

        archive_files = list(self.iter_files())

        for archive_file in archive_files:
            if Path(archive_file.filepath) == Path(file):
                break

        to_path = to_dir / archive_file.filepath

        if not to_path.parent.is_dir():
            to_path.parent.mkdir(parents=True, exist_ok=True)

        with to_path.open("wb") as stream:
            stream.write(archive_file.data)
