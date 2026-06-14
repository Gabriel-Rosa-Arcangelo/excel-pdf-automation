from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .models import UploadJob
from .tasks import _read_table


class ReadTableTests(TestCase):
    def test_reads_csv_as_strings_and_fills_empty_values(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "samples.csv"
            path.write_text("sample_id,name,value,date\n001,Ada,,2026-01-01\n", encoding="utf-8")

            data = _read_table(path)

        self.assertEqual(data.loc[0, "sample_id"], "001")
        self.assertEqual(data.loc[0, "value"], "")

    def test_rejects_unsupported_file_type(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "samples.txt"
            path.write_text("not supported", encoding="utf-8")

            with self.assertRaisesMessage(ValueError, "Unsupported file type"):
                _read_table(path)


class UploadJobTests(TestCase):
    def test_add_log_appends_structured_entry(self):
        job = UploadJob.objects.create(
            original_file=SimpleUploadedFile("samples.csv", b"sample_id,name,value,date\n")
        )

        job.add_log("info", "File received", {"rows": 1})

        job.refresh_from_db()
        self.assertEqual(
            job.log,
            [{"level": "info", "msg": "File received", "extra": {"rows": 1}}],
        )
