from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from backend.config import settings
from backend.storage import ensure_storage
from backend.db import init_db
from backend.jobs import create_job

storage = ensure_storage(settings)
init_db(settings.db_path)

pdf_path = Path("/home/ifzzh/Project/PDF-Babel/test-pdf/Kua.pdf")
record = create_job(
    settings,
    storage["jobs"],
    pdf_path.name,
    pdf_path.read_bytes(),
)

print("job_id:", record.id)
print("folder:", record.folder_name)
print("file exists:", (storage["jobs"]/record.folder_name/pdf_path.name).exists())
