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
    print("Iniciando cambio de metodo de pago...")
    token = os.getenv("DEBI_API_KEY")
    if not token:
        raise SystemExit("Missing DEBI_API_KEY in .env")

    csv_path = DEFAULT_CSV
    if not csv_path.exists():
        raise SystemExit(f"No existe el CSV: {csv_path}")

    sleep_seconds = SLEEP_SECONDS

    client = debi.debi(token)

    print(f"Usando CSV: {csv_path}")
    with csv_path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        if "change_payment_method" not in fieldnames:
            fieldnames.append("change_payment_method")
        rows = list(reader)
    print(f"Filas encontradas: {len(rows)}")

    with csv_path.open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()

        for index, row in enumerate(rows, start=1):
            payment_id = (row.get("payment_id") or "").strip()
            payment_method_id = (row.get("payment_method_id") or "").strip()
            log_status = ""
            retry_status = "skip"

            existing_status = (row.get("change_payment_method") or "").strip()
            if existing_status:
                log_status = "skip:ya_procesado"
                writer.writerow(row)
                print(
                    f"[row {index}/{len(rows)}] payment_id={payment_id} "
                    f"payment_method_id={payment_method_id} status={log_status} retry={retry_status}"
                )
                continue

            if not payment_id or not payment_method_id:
                row["change_payment_method"] = "missing_data"
                writer.writerow(row)
                log_status = "skip:missing_data"
                print(
                    f"[row {index}/{len(rows)}] payment_id={payment_id} "
                    f"payment_method_id={payment_method_id} status={log_status} retry={retry_status}"
                )
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
                row["change_payment_method"] = error
                writer.writerow(row)
                print(f"[row {index}/{len(rows)}] payment_id={payment_id} ERROR (change_method): {exc}")
                continue

            row["change_payment_method"] = status
            writer.writerow(row)

            log_status = status
            binary_mode_status = "skip"
            retry_status = "skip"
            payment_status = "unknown"

            # Set binary_mode on the payment before retrying
            try:
                client.put(endpoint, {"binary_mode": 1})
                binary_mode_status = "ok"
            except debi.debiRequestFailed as exc:
                binary_mode_status = f"error:{exc}"
                print(f"[row {index}/{len(rows)}] payment_id={payment_id} ERROR (binary_mode): {exc}")
                continue

            retry_endpoint = f"/v1/payments/{payment_id}/actions/retry"
            try:
                client.post(retry_endpoint, {})
                retry_status = "ok"
            except debi.debiRequestFailed as exc:
                retry_status = f"error:{exc}"
                print(f"[row {index}/{len(rows)}] payment_id={payment_id} ERROR (retry): {exc}")
                if payment_id:
                    try:
                        payment = client.get(f"/v1/payments/{payment_id}")
                        if isinstance(payment, dict):
                            data = payment.get("data") or {}
                            if isinstance(data, dict):
                                payment_status = data.get("status") or "unknown"
                    except debi.debiRequestFailed:
                        pass
                print(
                    f"[row {index}/{len(rows)}] payment_id={payment_id} "
                    f"payment_method_id={payment_method_id} change={log_status} "
                    f"binary_mode={binary_mode_status} retry={retry_status} payment_status={payment_status}"
                )
                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)
                continue

            if payment_id:
                try:
                    payment = client.get(f"/v1/payments/{payment_id}")
                    if isinstance(payment, dict):
                        data = payment.get("data") or {}
                        if isinstance(data, dict):
                            payment_status = data.get("status") or "unknown"
                except debi.debiRequestFailed as exc:
                    payment_status = f"error:{exc}"
                    print(f"[row {index}/{len(rows)}] payment_id={payment_id} ERROR (get payment): {exc}")

            print(
                f"[row {index}/{len(rows)}] payment_id={payment_id} "
                f"payment_method_id={payment_method_id} change={log_status} "
                f"binary_mode={binary_mode_status} retry={retry_status} payment_status={payment_status}"
            )

            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

    print(f"Resultados escritos en: {csv_path}")


if __name__ == "__main__":
    main()
