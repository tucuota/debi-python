import csv
import os
import time
from pathlib import Path

from dotenv import load_dotenv

import debi


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CSV = BASE_DIR / "change_payment_method.csv"
SLEEP_SECONDS = 0

load_dotenv(dotenv_path=BASE_DIR / ".env")


def main() -> None:
    token = os.getenv("DEBI_API_KEY")
    if not token:
        raise SystemExit("Missing DEBI_API_KEY in .env")

    csv_path = DEFAULT_CSV
    if not csv_path.exists():
        raise SystemExit(f"No existe el CSV: {csv_path}")

    sleep_seconds = SLEEP_SECONDS

    client = debi.debi(token)

    results_path = csv_path.with_name(f"{csv_path.stem}_results.csv")

    with csv_path.open(newline="") as handle, results_path.open("w", newline="") as out:
        reader = csv.DictReader(handle)
        writer = csv.DictWriter(
            out,
            fieldnames=["payment_id", "payment_method_id", "status", "error"]
        )
        writer.writeheader()

        for row in reader:
            payment_id = (row.get("payment_id") or "").strip()
            payment_method_id = (row.get("payment_method_id") or "").strip()

            if not payment_id or not payment_method_id:
                continue

            endpoint = f"/v1/payments/{payment_id}"

            status = "ok"
            error = ""

            try:
                client.put(endpoint, {
                    "payment_method_id": payment_method_id
                })
            except debi.debiRequestFailed as exc:
                status = "error"
                error = str(exc)

            writer.writerow({
                "payment_id": payment_id,
                "payment_method_id": payment_method_id,
                "status": status,
                "error": error,
            })

            if status == "ok":
                print(f"[ok] {payment_id} -> {payment_method_id}")
            else:
                print(f"[error] {payment_id} -> {error}")

            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

    print(f"Resultados escritos en: {results_path}")


if __name__ == "__main__":
    main()
