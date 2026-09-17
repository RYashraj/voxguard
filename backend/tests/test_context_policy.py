"""
Unit Tests for VoxGuard Explainable Advisory Policy Engine
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.schemas import SimulationContext, AdvisoryResult
from app.services.context_policy import (
    evaluate_advisory_policy,
    DEMO_HIGH_VALUE_TRANSFER_THRESHOLD
)


def test_policy_low_risk_known_caller():
    """Requirement Test 1: Low risk + known caller -> continue_with_caution."""
    ctx = SimulationContext(
        caller_context="known_contact",
        transaction_type="not_provided",
        user_confirmation_required=True
    )
    result = evaluate_advisory_policy(rolling_risk_score=0.15, alert_level="low", context=ctx)

    assert result.recommendation == "continue_with_caution"
    assert "low_acoustic_spoof_risk" not in result.reason_codes
    assert result.requires_user_confirmation is True
    assert isinstance(result.user_message, str)


def test_policy_medium_risk():
    """Requirement Test 2: Medium risk -> pause_and_verify."""
    result = evaluate_advisory_policy(rolling_risk_score=0.55, alert_level="medium", context=None)

    assert result.recommendation == "pause_and_verify"
    assert "medium_acoustic_spoof_risk" in result.reason_codes
    assert result.requires_user_confirmation is True


def test_policy_high_risk():
    """Requirement Test 3: High risk -> block_and_report."""
    result = evaluate_advisory_policy(rolling_risk_score=0.88, alert_level="high", context=None)

    assert result.recommendation == "block_and_report"
    assert "high_acoustic_spoof_risk" in result.reason_codes
    assert result.requires_user_confirmation is True


def test_policy_unknown_caller_otp_request():
    """Requirement Test 4: Unknown caller + OTP/PIN request + low risk -> pause_and_verify."""
    ctx = SimulationContext(
        caller_context="unknown_contact",
        transaction_type="otp_or_pin_request"
    )
    result = evaluate_advisory_policy(rolling_risk_score=0.10, alert_level="low", context=ctx)

    assert result.recommendation == "pause_and_verify"
    assert "unknown_caller" in result.reason_codes
    assert "sensitive_credential_request" in result.reason_codes
    assert result.requires_user_confirmation is True


def test_policy_unknown_caller_high_value_transfer():
    """Requirement Test 5: Unknown caller + high-value transfer (>= ₹10,000) + low risk -> pause_and_verify."""
    ctx = SimulationContext(
        caller_context="unknown_contact",
        transaction_type="fund_transfer",
        transaction_amount=15000.0
    )
    result = evaluate_advisory_policy(rolling_risk_score=0.20, alert_level="low", context=ctx)

    assert result.recommendation == "pause_and_verify"
    assert "unknown_caller" in result.reason_codes
    assert "high_value_transaction" in result.reason_codes
    assert result.requires_user_confirmation is True


def test_policy_unknown_caller_low_value_transfer():
    """Low risk + unknown caller + transfer under ₹10,000 -> continue_with_caution."""
    ctx = SimulationContext(
        caller_context="unknown_contact",
        transaction_type="fund_transfer",
        transaction_amount=5000.0
    )
    result = evaluate_advisory_policy(rolling_risk_score=0.10, alert_level="low", context=ctx)

    assert result.recommendation == "continue_with_caution"
    assert "unknown_caller" in result.reason_codes
    assert "high_value_transaction" not in result.reason_codes
