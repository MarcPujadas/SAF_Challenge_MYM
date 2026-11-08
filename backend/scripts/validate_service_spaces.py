import json

from app.database.database import init_db
from app.services.catalog_service import get_service_space_quality_report


def main() -> int:
    init_db()
    report = get_service_space_quality_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
