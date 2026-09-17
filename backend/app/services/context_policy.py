"""
VoxGuard Explainable Advisory Policy Engine

Provides a pure, deterministic, unit-testable policy function evaluating call risk updates
and validated transaction context to produce explainable security advisories.

Policy Principles:
1. High acoustic risk always recommends 'block_and_report'.
2. Medium acoustic risk recommends at least 'pause_and_verify'.
3. Low acoustic risk with concerning context (unknown caller + OTP/PIN or high-value transfer >= ₹10,000)
   recommends at least 'pause_and_verify'.
4. Low acoustic risk with no concerning context recommends 'continue_with_caution'.
5. Deterministic and explainable: ML acoustic scores are never altered by this advisory layer.
"""

from typing import Optional, List
from app.models.schemas import (
    SimulationContext,
    AdvisoryResult,
    AdvisoryRecommendation
)

# Conservative demo threshold for high-value transfer warning (₹10,000)
DEMO_HIGH_VALUE_TRANSFER_THRESHOLD = 10000.0


def evaluate_advisory_policy(
    rolling_risk_score: float,
    alert_level: str,
    context: Optional[SimulationContext] = None
) -> AdvisoryResult:
    """
    Evaluates acoustic alert level, rolling risk score, and optional call/transaction context
    to return a structured AdvisoryResult.

    Parameters:
    - rolling_risk_score: float (0.0 to 1.0)
    - alert_level: "low" | "medium" | "high"
    - context: Optional[SimulationContext]

    Returns:
    - AdvisoryResult (recommendation, reason_codes, user_message, requires_user_confirmation)
    """

    # 1. High Acoustic Risk Rule
    if alert_level == "high":
        reasons = ["high_acoustic_spoof_risk"]
        if context:
            if context.caller_context == "unknown_contact":
                reasons.append("unknown_caller")
            if context.transaction_type == "otp_or_pin_request":
                reasons.append("sensitive_credential_request")
            elif context.transaction_type == "fund_transfer" and context.transaction_amount and context.transaction_amount >= DEMO_HIGH_VALUE_TRANSFER_THRESHOLD:
                reasons.append("high_value_transaction")

        return AdvisoryResult(
            recommendation="block_and_report",
            reason_codes=sorted(list(set(reasons))),
            user_message="High voice-cloning risk detected. Do not approve this transaction; verify through an official channel.",
            requires_user_confirmation=True
        )

    # 2. Medium Acoustic Risk Rule
    if alert_level == "medium":
        reasons = ["medium_acoustic_spoof_risk"]
        if context:
            if context.caller_context == "unknown_contact":
                reasons.append("unknown_caller")
            if context.transaction_type == "otp_or_pin_request":
                reasons.append("sensitive_credential_request")
            elif context.transaction_type == "fund_transfer" and context.transaction_amount and context.transaction_amount >= DEMO_HIGH_VALUE_TRANSFER_THRESHOLD:
                reasons.append("high_value_transaction")

        return AdvisoryResult(
            recommendation="pause_and_verify",
            reason_codes=sorted(list(set(reasons))),
            user_message="Suspicious voice acoustic patterns detected. Pause the call and confirm caller identity before proceeding.",
            requires_user_confirmation=True
        )

    # 3. Low Acoustic Risk Rules (Context Evaluation)
    if not context:
        return AdvisoryResult(
            recommendation="continue_with_caution",
            reason_codes=["context_not_provided"],
            user_message="Low acoustic risk detected. Proceed with caution.",
            requires_user_confirmation=True
        )

    reasons: List[str] = []
    is_unknown = (context.caller_context == "unknown_contact")
    is_otp_req = (context.transaction_type == "otp_or_pin_request")
    is_high_val = (
        context.transaction_type == "fund_transfer"
        and context.transaction_amount is not None
        and context.transaction_amount >= DEMO_HIGH_VALUE_TRANSFER_THRESHOLD
    )

    if is_unknown:
        reasons.append("unknown_caller")
    if is_otp_req:
        reasons.append("sensitive_credential_request")
    if is_high_val:
        reasons.append("high_value_transaction")

    # Unknown caller + OTP/PIN request rule
    if is_unknown and is_otp_req:
        return AdvisoryResult(
            recommendation="pause_and_verify",
            reason_codes=sorted(list(set(reasons))),
            user_message="Credential or PIN requested by an unknown caller. Pause and verify identity through an official channel.",
            requires_user_confirmation=True
        )

    # Unknown caller + High-value transfer rule
    if is_unknown and is_high_val:
        return AdvisoryResult(
            recommendation="pause_and_verify",
            reason_codes=sorted(list(set(reasons))),
            user_message=f"High-value transfer requested by an unknown caller (>= ₹{int(DEMO_HIGH_VALUE_TRANSFER_THRESHOLD):,}). Pause and verify before proceeding.",
            requires_user_confirmation=True
        )

    # Other credential request (even if known caller)
    if is_otp_req:
        return AdvisoryResult(
            recommendation="pause_and_verify",
            reason_codes=sorted(list(set(reasons))),
            user_message="Sensitive credential or PIN requested. Pause and confirm caller identity before sharing credentials.",
            requires_user_confirmation=True
        )

    # Low risk with no concerning context
    if not reasons or (context.caller_context == "not_provided" and context.transaction_type == "not_provided"):
        reasons = ["context_not_provided"]

    return AdvisoryResult(
        recommendation="continue_with_caution",
        reason_codes=sorted(list(set(reasons))),
        user_message="Low acoustic risk detected. Proceed with caution and verify sensitive requests.",
        requires_user_confirmation=context.user_confirmation_required
    )
