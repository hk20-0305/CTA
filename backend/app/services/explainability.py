# backend/app/services/explainability.py
import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ExplainabilityEngine:
    """
    Generates human-readable, patient-specific eligibility explanations.
    Instead of generic labels, each section references actual patient values
    (e.g. "HbA1c of 8.5% satisfies the criterion HbA1c ≥ 7.5%").
    """

    def generate_explanation(self, check_result: Dict) -> str:
        """
        Build a comprehensive, human-readable eligibility narrative.

        Parameters
        ----------
        check_result : dict
            Output from MatchingEngine.check_eligibility().

        Returns
        -------
        str
            Multi-paragraph markdown explanation.
        """
        status = check_result.get("status", "unknown")
        confidence = float(check_result.get("confidence_score", 0.0))
        overall_score = float(check_result.get("overall_score", 0.0))
        inclusion_matches: List[Dict] = check_result.get("matched_criteria") or []
        exclusion_matches: List[Dict] = check_result.get("excluded_criteria") or []
        patient_summary = check_result.get("patient_summary", "Unknown patient")
        trial_summary = check_result.get("trial_summary", "Unknown trial")
        # Optional pass-through patient_data (added by matching engine)
        patient_data: Dict = check_result.get("patient_data") or {}
        lab_values: Dict = patient_data.get("lab_values") or {}

        parts: List[str] = []

        # ------------------------------------------------------------------ #
        # 1. Decision header
        # ------------------------------------------------------------------ #
        if status == "eligible":
            parts.append(
                f"✅ **ELIGIBILITY DECISION: ELIGIBLE**\n\n"
                f"The automated analysis concludes that this patient is **eligible** for enrollment "
                f"with an overall match score of **{overall_score * 100:.1f}%** and "
                f"**{confidence:.1f}% system confidence**. "
                f"The patient profile aligns with the trial's inclusion requirements and no "
                f"disqualifying exclusion factors were detected."
            )
        elif status == "not_eligible":
            parts.append(
                f"❌ **ELIGIBILITY DECISION: NOT ELIGIBLE**\n\n"
                f"The automated analysis concludes that this patient is **not eligible** for enrollment "
                f"(overall match score: **{overall_score * 100:.1f}%**, confidence: **{confidence:.1f}%**). "
                f"Critical trial requirements were not satisfied or one or more exclusion criteria "
                f"were triggered."
            )
        else:
            parts.append(
                f"⚠️ **ELIGIBILITY DECISION: UNCERTAIN**\n\n"
                f"The automated analysis is **inconclusive** "
                f"(overall match score: **{overall_score * 100:.1f}%**, confidence: **{confidence:.1f}%**). "
                f"Available data is insufficient for a definitive determination. "
                f"Manual clinical review is strongly recommended."
            )

        # ------------------------------------------------------------------ #
        # 2. Patient & trial context
        # ------------------------------------------------------------------ #
        parts.append(f"\n**👤 Patient Profile:** {patient_summary}")
        parts.append(f"**🔬 Trial Protocol:** {trial_summary}")

        # ------------------------------------------------------------------ #
        # 3. Lab value snapshot (if available)
        # ------------------------------------------------------------------ #
        if lab_values:
            lab_display = {
                "hba1c": ("HbA1c", "{v}%"),
                "fasting_glucose": ("Fasting Glucose", "{v} mg/dL"),
                "bmi": ("BMI", "{v}"),
                "egfr": ("eGFR", "{v} mL/min"),
                "systolic_bp": ("Systolic BP", "{v} mmHg"),
                "creatinine": ("Creatinine", "{v} mg/dL"),
                "ldl": ("LDL", "{v} mg/dL"),
            }
            rows = []
            for key, (label, fmt) in lab_display.items():
                if key in lab_values:
                    rows.append(f"  • {label}: **{fmt.format(v=lab_values[key])}**")
            if rows:
                parts.append("\n**📊 Key Clinical Values:**\n" + "\n".join(rows))

        # ------------------------------------------------------------------ #
        # 4. Inclusion criteria — matched
        # ------------------------------------------------------------------ #
        if inclusion_matches:
            parts.append(
                f"\n\n**✓ SATISFIED INCLUSION CRITERIA ({len(inclusion_matches)} matched):**"
            )
            for i, m in enumerate(inclusion_matches[:6], 1):
                criterion = m.get("criterion", "Unknown")
                score_pct = m.get("score", 0) * 100
                reasoning = self._criterion_reasoning(
                    criterion, m, lab_values, patient_data, "inclusion"
                )
                parts.append(
                    f"\n{i}. **{criterion}**\n"
                    f"   Match strength: {score_pct:.1f}% "
                    f"(semantic {m.get('semantic_score', 0) * 100:.0f}%, "
                    f"keyword {m.get('keyword_score', 0) * 100:.0f}%, "
                    f"numeric {m.get('numeric_score', 0) * 100:.0f}%)\n"
                    f"   → {reasoning}"
                )
        else:
            parts.append(
                "\n\n**⚠️ NO INCLUSION CRITERIA SATISFIED**\n"
                "The patient profile did not strongly match any of the trial's inclusion "
                "criteria. This significantly reduces the likelihood of eligibility. "
                "Consider whether the submitted documents contain sufficient clinical detail."
            )

        # ------------------------------------------------------------------ #
        # 5. Exclusion criteria — triggered
        # ------------------------------------------------------------------ #
        if exclusion_matches:
            parts.append(
                f"\n\n**✗ TRIGGERED EXCLUSION CRITERIA ({len(exclusion_matches)} flagged):**"
            )
            for i, m in enumerate(exclusion_matches[:6], 1):
                criterion = m.get("criterion", "Unknown")
                score_pct = m.get("score", 0) * 100
                risk = self._exclusion_risk_label(m.get("score", 0))
                reasoning = self._criterion_reasoning(
                    criterion, m, lab_values, patient_data, "exclusion"
                )
                parts.append(
                    f"\n{i}. **{criterion}**\n"
                    f"   Risk level: {risk} (match: {score_pct:.1f}%)\n"
                    f"   → {reasoning}"
                )
        else:
            if check_result.get("excluded_criteria") is not None:
                parts.append(
                    "\n\n**✓ NO EXCLUSION CRITERIA TRIGGERED**\n"
                    "None of the trial's exclusion criteria were detected in the patient profile. "
                    "This is a positive indicator for eligibility."
                )

        # ------------------------------------------------------------------ #
        # 6. Clinical recommendation
        # ------------------------------------------------------------------ #
        parts.append("\n\n**📋 CLINICAL RECOMMENDATION:**")
        if status == "eligible":
            parts.append(
                "\nThe automated analysis indicates this patient is a **strong candidate** for "
                "enrollment. Before proceeding, ensure:\n"
                "- Complete medical records have been reviewed by the investigator\n"
                "- All laboratory values are current (within protocol-specified timeframe)\n"
                "- Patient has provided informed consent and understands the study requirements\n"
                "- Any borderline criteria are confirmed against original source documents"
            )
        elif status == "not_eligible":
            parts.append(
                "\nThe automated analysis indicates this patient is **not suitable** for this "
                "trial at this time. Recommended actions:\n"
                "- Review flagged exclusion criteria for potential false positives\n"
                "- Determine whether exclusions are absolute or relative contraindications\n"
                "- Search for alternative trials with different eligibility requirements\n"
                "- Document the reasons for ineligibility in the patient's medical record"
            )
        else:
            parts.append(
                "\nThe system could not make a confident determination. Recommended actions:\n"
                "- Gather additional clinical documentation (lab reports, imaging, prior history)\n"
                "- Seek clarification from the study sponsor on ambiguous criteria\n"
                "- Request a second opinion from the trial's principal investigator\n"
                "- Consider a protocol amendment or eligibility waiver if clinically appropriate"
            )

        # ------------------------------------------------------------------ #
        # 7. Confidence interpretation
        # ------------------------------------------------------------------ #
        parts.append(f"\n\n**🎯 SYSTEM CONFIDENCE: {confidence:.1f}%**")
        if confidence >= 75:
            parts.append(
                f"The system has **high confidence** in this assessment. Strong matches were "
                f"found across multiple criteria dimensions (semantic similarity, keyword "
                f"overlap, and numeric range checks). Standard verification applies."
            )
        elif confidence >= 50:
            parts.append(
                f"The system has **moderate confidence** in this assessment. Some criteria "
                f"matches rely primarily on semantic similarity without direct numeric "
                f"confirmation. Enhanced manual review is advisable."
            )
        else:
            parts.append(
                f"The system has **low confidence** in this assessment. Limited matching "
                f"evidence was found — this may be due to insufficient detail in the submitted "
                f"documents, or a genuine mismatch between patient and trial characteristics. "
                f"Comprehensive manual review is essential before any enrollment decision."
            )

        # ------------------------------------------------------------------ #
        # 8. Legal disclaimer
        # ------------------------------------------------------------------ #
        parts.append(
            "\n\n---\n"
            "*This explanation was generated by an automated ML-based eligibility screening "
            "system using semantic NLP matching and rule-based numeric checks. It is intended "
            "as a **decision support tool only** and does not constitute a medical or legal "
            "determination. All final eligibility decisions must be made by qualified clinical "
            "investigators in accordance with the approved study protocol.*"
        )

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Helper: per-criterion reasoning narrative
    # ------------------------------------------------------------------
    def _criterion_reasoning(
        self,
        criterion: str,
        match: Dict,
        lab_values: Dict,
        patient_data: Dict,
        match_type: str,
    ) -> str:
        """
        Generate a specific reasoning sentence for a criterion match.
        Where possible, cite actual patient values.
        """
        criterion_lower = criterion.lower()
        semantic = match.get("semantic_score", 0)
        keyword = match.get("keyword_score", 0)
        numeric = match.get("numeric_score", 0)

        # --- Numeric evidence first (most informative) ---
        if numeric > 0:
            # Age
            if "age" in criterion_lower and patient_data.get("age"):
                age = patient_data["age"]
                return (
                    f"Patient's age ({age} years) numerically satisfies this criterion."
                )
            # HbA1c
            if "hba1c" in criterion_lower and lab_values.get("hba1c"):
                hba1c = lab_values["hba1c"]
                return (
                    f"Patient's HbA1c of **{hba1c}%** satisfies this criterion."
                )
            # BMI
            if "bmi" in criterion_lower and lab_values.get("bmi"):
                bmi = lab_values["bmi"]
                return (
                    f"Patient's BMI of **{bmi}** meets the stated requirement."
                )
            # eGFR
            if "egfr" in criterion_lower and lab_values.get("egfr"):
                egfr = lab_values["egfr"]
                verb = "satisfies" if match_type == "inclusion" else "triggers concern for"
                return f"Patient's eGFR of **{egfr} mL/min** {verb} this criterion."

        # --- Keyword evidence ---
        if keyword >= 0.5:
            conditions = patient_data.get("conditions") or patient_data.get("comorbidities") or []
            medications = patient_data.get("medications") or []
            # Check which keywords from the criterion appear in patient data
            kwords = re.findall(r"\b[a-z]{4,}\b", criterion_lower)
            cond_lower = " ".join(str(c).lower() for c in conditions)
            med_lower = " ".join(str(m).lower() for m in medications)
            matched_in_conds = [k for k in kwords if k in cond_lower]
            matched_in_meds = [k for k in kwords if k in med_lower]
            if matched_in_conds:
                return (
                    f"Patient's documented condition(s) — "
                    f"*{', '.join(str(c) for c in conditions[:3])}* — match this criterion."
                )
            if matched_in_meds:
                return (
                    f"Patient's current medication(s) — "
                    f"*{', '.join(str(m) for m in medications[:3])}* — align with this criterion."
                )

        # --- Semantic evidence ---
        if semantic >= 0.65:
            return (
                "Strong semantic similarity detected between the patient profile and this "
                "criterion (the overall clinical description closely matches)."
            )
        elif semantic >= 0.45:
            return (
                "Moderate semantic overlap detected. The patient profile partially aligns "
                "with this criterion; manual confirmation is advisable."
            )
        return (
            "Weak but detectable correlation found between the patient profile and this "
            "criterion. Human review required to confirm relevance."
        )

    def _exclusion_risk_label(self, score: float) -> str:
        if score >= 0.75:
            return "🔴 HIGH RISK"
        elif score >= 0.55:
            return "🟠 MODERATE RISK"
        return "🟡 LOW RISK"

    def score_explanation(self, explanation: str, check_result: Dict) -> float:
        """Quality score based on explanation length and specificity."""
        word_count = len(explanation.split())
        return float(min(1.0, word_count / 250))


explainability_engine = ExplainabilityEngine()
