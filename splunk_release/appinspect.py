"""Submit packages to AppInspect and save its reports."""

import base64
import json
import os
import sys
import time
import uuid
from pathlib import Path

from splunk_release.acs import package_identity
from splunk_release.azure import http

# Request checks for private Victoria apps and future cloud vetting.
APPINSPECT_TAGS = "private_victoria,future"

def appinspect_token():
    basic = base64.b64encode(
        f"{os.environ['SPLUNK_USERNAME']}:{os.environ['SPLUNK_PASSWORD']}".encode()
    ).decode()
    return json.loads(
        http(
            "https://api.splunk.com/2.0/rest/login/splunk",
            {"Authorization": f"Basic {basic}"},
        )
    )["data"]["token"]

def appinspect_passed(status, report):
    """Return true only for SUCCESS with zero failures, errors, and manual checks."""
    summary = report.get("summary", {})
    return (
        status == "SUCCESS"
        and summary.get("failure") == 0
        and summary.get("error") == 0
        and summary.get("manual_check") == 0
    )

def save_appinspect_report(artifact_dir, html, report):
    Path(artifact_dir, "appinspect-report.html").write_bytes(html)
    Path(artifact_dir, "appinspect-report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )

def appinspect(artifact_dir):
    pkg, _, _ = package_identity(artifact_dir)
    auth = {"Authorization": f"Bearer {appinspect_token()}"}
    content_type, body = multipart(pkg)
    response = json.loads(
        http(
            "https://appinspect.splunk.com/v1/app/validate",
            {**auth, "Content-Type": content_type},
            body,
        )
    )
    request_id = response["request_id"]
    tags = f"?included_tags={APPINSPECT_TAGS}"
    status_url = f"https://appinspect.splunk.com/v1/app/validate/status/{request_id}{tags}"
    deadline = time.monotonic() + 30 * 60
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            sys.exit("AppInspect timed out after 30 minutes")
        status_body = http(
            status_url, {**auth, "Accept": "application/json"}, timeout=min(900, remaining)
        )
        status = json.loads(status_body)["status"]
        if status != "PROCESSING":
            break
        time.sleep(min(15, remaining))
    report_url = f"https://appinspect.splunk.com/v1/app/report/{request_id}{tags}"
    html = http(report_url, {**auth, "Accept": "text/html"})
    report = json.loads(
        http(
            report_url,
            {**auth, "Accept": "application/json"},
        )
    )
    save_appinspect_report(artifact_dir, html, report)
    summary = report.get("summary", {})
    print(
        f"AppInspect {status}: {json.dumps(summary, separators=(',', ':'), sort_keys=True)}"
    )
    if summary.get("future_failure"):
        print(
            "##vso[task.logissue type=warning]AppInspect future_failure: "
            f"{summary['future_failure']} checks will become cloud vetting failures"
        )
    if not appinspect_passed(status, report):
        sys.exit("AppInspect did not pass")

def multipart(pkg):
    """Build (content_type, body) for a multipart/form-data POST with app_package."""
    boundary = uuid.uuid4().hex
    head = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="app_package"; '
        f'filename="{pkg.name}"\r\nContent-Type: application/gzip\r\n\r\n'
    )
    body = head.encode() + pkg.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    return f"multipart/form-data; boundary={boundary}", body
