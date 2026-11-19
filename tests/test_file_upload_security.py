import unittest

from app.api.routes.files import _file_type, _sanitize_filename
from app.services.file_service import _safe_local_extension


class UploadFilenameTests(unittest.TestCase):
    def test_filename_path_components_are_removed(self):
        self.assertEqual(_sanitize_filename(r"..\..\notes.pdf"), "notes.pdf")

    def test_filename_control_characters_are_removed(self):
        self.assertEqual(_sanitize_filename("notes\n.pdf"), "notes.pdf")

    def test_only_supported_extensions_are_classified(self):
        self.assertEqual(_file_type("notes.pdf"), "pdf")
        self.assertEqual(_file_type("notes.exe"), "unknown")

    def test_drive_filename_cannot_escape_the_storage_directory(self):
        self.assertEqual(_safe_local_extension(r"..\..\notes.pdf"), ".pdf")
        self.assertEqual(_safe_local_extension("unexpected.exe"), ".bin")


if __name__ == "__main__":
    unittest.main()
