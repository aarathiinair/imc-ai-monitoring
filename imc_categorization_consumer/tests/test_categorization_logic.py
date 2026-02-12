import pytest

from prtg_categorization_consumer.business_logic.categorization import categorize
from prtg_categorization_consumer.parsing.prtg_email_parser import parse_prtg_email_body
from prtg_categorization_consumer.models.model import OutlookEmail


def make_email(subject, body, message_id="test123"):
    return OutlookEmail(subject=subject, body=body, message_id=message_id)


# ---------------------------
# PARSING TESTS
# ---------------------------

def test_parse_valid_prtg_body():
    body = "Device: A\nSensor: B\nStatus: Down\nPriority: ***"
    parsed = parse_prtg_email_body(body)
    assert parsed.get("device") == "A"
    assert parsed.get("sensor") == "B"


def test_missing_device_field():
    body = "Sensor: WAN"
    parsed = parse_prtg_email_body(body)
    assert parsed is not None


def test_missing_sensor_field():
    body = "Device: Router"
    parsed = parse_prtg_email_body(body)
    assert parsed is not None


# ---------------------------
# DOWN / RECOVERY LOGIC
# ---------------------------

def test_down_alert_creates_ticket():
    body = "Device: A\nSensor: B\nStatus: Down\nPriority: ***"
    email = make_email("A // B // Down", body)
    parsed = parse_prtg_email_body(body)

    result = categorize(email, parsed, open_ticket_exists=False)
    assert result["action"] == "CREATE_TICKET"


def test_recovery_email_no_action():
    email = make_email(
        "A // B // Down ended (now: Up)",
        "Status: Down"
    )
    parsed = parse_prtg_email_body(email.body)

    result = categorize(email, parsed, open_ticket_exists=False)
    assert result["action"] == "NO_ACTION"


def test_ignore_non_prtg_email():
    email = make_email("Hello world", "Random body")
    parsed = {}

    result = categorize(email, parsed, open_ticket_exists=False)
    assert result["action"] == "NO_ACTION"


# ---------------------------
# ERROR SIGNATURE
# ---------------------------

def test_error_signature_generation():
    body = "Device: Router\nSensor: WAN\nStatus: Down"
    email = make_email("Router Down", body)
    parsed = parse_prtg_email_body(body)

    result = categorize(email, parsed, False)
    assert "::" in result["error_signature"]


# ---------------------------
# DEDUP TESTS
# ---------------------------

def test_duplicate_ticket_prevented():
    body = "Status: Down"
    email = make_email("Router Down", body)
    parsed = parse_prtg_email_body(body)

    result = categorize(email, parsed, open_ticket_exists=True)
    assert result["action"] == "NO_ACTION"


# ---------------------------
# PRIORITY TESTS
# ---------------------------

def test_priority_low():
    body = "Priority: **"
    email = make_email("Down", body)
    parsed = parse_prtg_email_body(body)

    result = categorize(email, parsed, False)
    assert result["jira"]["priority"] == "Low"


def test_priority_medium():
    body = "Priority: ***"
    email = make_email("Down", body)
    parsed = parse_prtg_email_body(body)

    result = categorize(email, parsed, False)
    assert result["jira"]["priority"] == "Medium"


def test_priority_high():
    body = "Priority: *****"
    email = make_email("Down", body)
    parsed = parse_prtg_email_body(body)

    result = categorize(email, parsed, False)
    assert result["jira"]["priority"] == "High"


def test_priority_default_medium():
    body = "Device: A"
    email = make_email("Down", body)
    parsed = parse_prtg_email_body(body)

    result = categorize(email, parsed, False)
    assert result["jira"]["priority"] == "Medium"


# ---------------------------
# SINGLE LINE ALERT
# ---------------------------

def test_single_line_location_unavailable():
    body = "Frankfurt location not available"
    email = make_email("Location down", body)

    result = categorize(email, {}, False)
    assert result["action"] == "CREATE_TICKET"


# ---------------------------
# AI TESTS
# ---------------------------

def test_ai_summary_present_for_down():
    body = "Device: A\nSensor: B\nStatus: Down\nPriority: ***"
    email = make_email("A Down", body)
    parsed = parse_prtg_email_body(body)

    result = categorize(email, parsed, False)

    desc = result["jira"]["description"]
    assert len(desc) > 20


def test_ai_not_called_for_recovery():
    email = make_email("Down ended (now: Up)", "Status: Down")
    parsed = parse_prtg_email_body(email.body)

    result = categorize(email, parsed, False)
    assert result["action"] == "NO_ACTION"


def test_ai_failure_fallback(monkeypatch):
    def mock_ai(*args, **kwargs):
        raise Exception("AI fail")

    monkeypatch.setattr(
        "app.core.monitoring.prtg_logic.generate_ai_description",
        mock_ai
    )

    body = "Device: A\nSensor: B\nStatus: Down"
    email = make_email("Down", body)
    parsed = parse_prtg_email_body(body)

    result = categorize(email, parsed, False)
    assert result["action"] == "CREATE_TICKET"


# ---------------------------
# JIRA OUTPUT TESTS
# ---------------------------

def test_jira_title_from_subject():
    email = make_email("Router Down", "Status: Down")
    parsed = parse_prtg_email_body(email.body)

    result = categorize(email, parsed, False)
    assert result["jira"]["title"] == "Router Down"


def test_description_contains_full_email():
    body = "Device: A\nSensor: B\nStatus: Down"
    email = make_email("Down", body)
    parsed = parse_prtg_email_body(body)

    result = categorize(email, parsed, False)
    assert body in result["jira"]["description"]


def test_assignment_group():
    email = make_email("Down", "Status: Down")
    parsed = parse_prtg_email_body(email.body)

    result = categorize(email, parsed, False)
    assert result["jira"]["assignment_group"] == "Telecommunication Group"


def test_json_structure():
    email = make_email("Down", "Status: Down")
    parsed = parse_prtg_email_body(email.body)

    result = categorize(email, parsed, False)

    assert "action" in result
    assert "source" in result
    assert "error_signature" in result
