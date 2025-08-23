from celery import shared_task
from django.core.files.base import ContentFile
from django.conf import settings
from pathlib import Path
import pandas as pd
import io

from .models import UploadJob, GeneratedReport
from .pdf import build_pdf_enhanced

def _read_table(file_path: Path):
    suffix = file_path.suffix.lower()
    if suffix in [".xlsx", ".xls"]:
        return pd.read_excel(file_path, dtype=str, engine="openpyxl").fillna("")
    if suffix == ".csv":
        return pd.read_csv(file_path, dtype=str).fillna("")
    raise ValueError(f"Unsupported file type: {suffix}")


@shared_task(bind=True)
def process_upload_job(self, job_id: str):
    job = UploadJob.objects.get(pk=job_id)
    try:
        # 0 → 25: leitura/validação
        job.status = "processing"; job.progress = 5
        job.save(update_fields=["status", "progress"])
        job.add_log("info", "Starting processing")

        file_path = Path(settings.MEDIA_ROOT) / job.original_file.name
        df = _read_table(file_path)  # usa engine="openpyxl" p/ xlsx dentro de _read_table (veja abaixo)
        job.add_log("info", f"Rows loaded: {len(df)}")

        required = ["sample_id","name","value","date"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")

        job.progress = 25
        job.add_log("info", "Validation OK")
        job.save(update_fields=["progress", "log"])

        # 25 → 50: normalização (rápida)
        try:
            job.add_log("info", "Normalizing values…")
            if "value" in df.columns:
                df["value"] = df["value"].astype(str).str.replace(",", ".", regex=False)
        except Exception as e:
            job.add_log("warning", f"Value normalization warning: {e}")

        job.progress = 50
        job.add_log("info", "Normalization done")
        job.save(update_fields=["progress", "log"])

        # 50 → 75: geração do PDF
        job.add_log("info", "Building PDF… (bar chart)")
        pdf_buffer = io.BytesIO()
        build_pdf_enhanced(pdf_buffer, title="Excel → PDF Automation", df=df, top_n=8)  # top_n reduzido
        pdf_buffer.seek(0)

        job.progress = 75
        job.add_log("info", "PDF built, saving…")
        job.save(update_fields=["progress", "log"])


        # 75 → 100: salvar arquivo
        filename = f"report_{job.id}.pdf"
        rep = GeneratedReport(job=job, filename=filename)
        rep.file.save(filename, ContentFile(pdf_buffer.read()))
        pdf_buffer.close()

        job.report_count = 1
        job.progress = 100
        job.status = "done"
        job.add_log("success","Report generated")
        job.save(update_fields=["report_count","progress","status","log"])

    except Exception as e:
        job.status = "failed"
        job.add_log("error", f"{e}")
        job.save(update_fields=["status","log"])
        raise

