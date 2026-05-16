# backend/app/services/matching_engine.py
from typing import Dict, List, Tuple
from app.services.nlp_engine import nlp_engine
import logging
import re

logger = logging.getLogger(__name__)


class MatchingEngine:
    """
    Eligibility matching engine.
    Uses batch semantic similarity + keyword matching + numeric range checks
    to produce per-patient, per-trial scores.

    Key design choices:
    - Inclusion: combined score from semantic + keyword + numeric.
      A criterion is "satisfied" if combined >= INCLUDE_THRESHOLD.
    - Exclusion: requires STRONGER evidence to trigger (higher threshold).
      Numeric checks can VETO a false-positive exclusion: if a numeric
      criterion is checked and the patient does NOT violate it, the
      exclusion is suppressed even if semantic/keyword scores are high.
    """

    INCLUDE_THRESHOLD = 0.40
    EXCLUDE_THRESHOLD = 0.55  # raised from 0.45 — exclusions need stronger signal

    def check_eligibility(self, patient_data: Dict, trial_data: Dict) -> Dict:
        logger.info("=" * 60)
        logger.info("ELIGIBILITY CHECK")
        logger.info(f"  Patient : {patient_data.get('name', 'Unknown')}")
        logger.info(f"  Trial   : {trial_data.get('title', 'Unknown')}")

        patient_text = self._format_patient_text(patient_data)
        trial_inclusion: List[str] = trial_data.get("inclusion_criteria") or []
        trial_exclusion: List[str] = trial_data.get("exclusion_criteria") or []

        logger.info(f"  Inclusion criteria : {len(trial_inclusion)}")
        logger.info(f"  Exclusion criteria : {len(trial_exclusion)}")
        logger.info(f"  Patient text ({len(patient_text)} chars): {patient_text[:200]}")

        # --- Batch similarity for all criteria at once ---
        all_criteria = trial_inclusion + trial_exclusion
        if all_criteria:
            all_similarities = nlp_engine.batch_similarity(patient_text, all_criteria)
        else:
            all_similarities = []

        inc_similarities = all_similarities[: len(trial_inclusion)]
        exc_similarities = all_similarities[len(trial_inclusion):]

        # --- Score inclusion ---
        inclusion_matches = self._score_inclusion(
            patient_text, patient_data, trial_inclusion, inc_similarities
        )

        # --- Score exclusion (with veto logic) ---
        exclusion_matches = self._score_exclusion(
            patient_text, patient_data, trial_exclusion, exc_similarities
        )

        # --- Overall score ---
        overall_score = self._compute_overall_score(
            inclusion_matches, exclusion_matches, trial_inclusion, trial_exclusion
        )

        # --- Status ---
        status = self._determine_status(overall_score, inclusion_matches, exclusion_matches)

        # --- Confidence ---
        confidence = self._calculate_confidence(
            inclusion_matches, exclusion_matches, trial_inclusion, trial_exclusion
        )

        logger.info(
            f"  Result: status={status}, overall={overall_score:.3f}, confidence={confidence:.1f}%"
        )
        logger.info("=" * 60)

        return {
            "overall_score": float(overall_score),
            "confidence_score": float(confidence),
            "status": status,
            "matched_criteria": inclusion_matches,
            "excluded_criteria": exclusion_matches,
            "evidence": self._extract_evidence(inclusion_matches, exclusion_matches),
            "patient_summary": self._summarize_patient(patient_data),
            "trial_summary": self._summarize_trial(trial_data),
            "patient_data": patient_data,
        }

    # ------------------------------------------------------------------
    # Patient text formatter
    # ------------------------------------------------------------------
    def _format_patient_text(self, patient_data: Dict) -> str:
        parts: List[str] = []

        if patient_data.get("name"):
            parts.append(f"Patient: {patient_data['name']}")
        if patient_data.get("age"):
            age = patient_data["age"]
            parts.append(f"Age: {age} years old, {age}-year-old")
        if patient_data.get("gender"):
            parts.append(f"Gender: {patient_data['gender']}")

        conditions = patient_data.get("conditions") or patient_data.get("comorbidities") or []
        if conditions:
            cond_str = ", ".join(str(c) for c in conditions)
            parts.append(f"Medical conditions: {cond_str}")
            parts.append(f"Diagnosed with: {cond_str}")
            parts.append(nlp_engine.expand_synonyms(cond_str))

        medications = patient_data.get("medications") or []
        if medications:
            med_str = ", ".join(str(m) for m in medications)
            parts.append(f"Current medications: {med_str}")
            parts.append(f"Taking: {med_str}")
            parts.append(nlp_engine.expand_synonyms(med_str))

        lab_values: Dict = patient_data.get("lab_values") or {}
        lab_verbose = {
            "hba1c": "HbA1c {v}%",
            "fasting_glucose": "fasting glucose {v} mg/dL",
            "glucose": "glucose {v} mg/dL",
            "bmi": "BMI {v}",
            "systolic_bp": "systolic blood pressure {v} mmHg",
            "diastolic_bp": "diastolic blood pressure {v} mmHg",
            "egfr": "eGFR {v} mL/min",
            "creatinine": "creatinine {v} mg/dL",
            "cholesterol": "total cholesterol {v} mg/dL",
            "ldl": "LDL {v} mg/dL",
            "hdl": "HDL {v} mg/dL",
            "triglycerides": "triglycerides {v} mg/dL",
            "alt": "ALT {v} U/L",
            "ast": "AST {v} U/L",
            "hemoglobin": "hemoglobin {v} g/dL",
            "o2_saturation": "oxygen saturation {v}%",
        }
        for key, template in lab_verbose.items():
            if key in lab_values:
                parts.append(template.format(v=lab_values[key]))

        return ". ".join(parts) + "."

    # ------------------------------------------------------------------
    # Safe float conversion
    # ------------------------------------------------------------------
    @staticmethod
    def _safe_float(val: str) -> float:
        if val is None:
            return 0.0
        return float(str(val).rstrip('.'))

    # ------------------------------------------------------------------
    # INCLUSION scoring
    # ------------------------------------------------------------------
    def _score_inclusion(
        self,
        patient_text: str,
        patient_data: Dict,
        criteria: List[str],
        similarities: List[float],
    ) -> List[Dict]:
        """Score inclusion criteria. Higher is better."""
        matches: List[Dict] = []

        for idx, criterion in enumerate(criteria):
            if not criterion or not criterion.strip():
                continue

            criterion_clean = criterion.strip()
            semantic = similarities[idx] if idx < len(similarities) else 0.0
            keyword = self._keyword_match_score(patient_text, criterion_clean)
            numeric = self._numeric_match_score_inclusion(patient_text, criterion_clean)

            # Weighted combination — numeric gets a boost for inclusion
            if numeric > 0:
                # If numeric check passed, ensure it contributes strongly
                combined = (semantic * 0.30) + (keyword * 0.25) + (numeric * 0.45)
            else:
                combined = (semantic * 0.50) + (keyword * 0.30) + (numeric * 0.20)

            logger.debug(
                f"  [inclusion] '{criterion_clean[:60]}' "
                f"sem={semantic:.3f} kw={keyword:.3f} num={numeric:.3f} → {combined:.3f}"
            )

            if combined >= self.INCLUDE_THRESHOLD:
                matches.append({
                    "criterion": criterion_clean,
                    "score": float(combined),
                    "type": "inclusion",
                    "semantic_score": float(semantic),
                    "keyword_score": float(keyword),
                    "numeric_score": float(numeric),
                })
                logger.info(f"  ✅ MATCH [inclusion]: '{criterion_clean[:60]}' ({combined:.3f})")

        logger.info(f"  inclusion: {len(matches)}/{len(criteria)} criteria matched")
        return matches

    # ------------------------------------------------------------------
    # EXCLUSION scoring — with VETO logic
    # ------------------------------------------------------------------
    def _score_exclusion(
        self,
        patient_text: str,
        patient_data: Dict,
        criteria: List[str],
        similarities: List[float],
    ) -> List[Dict]:
        """
        Score exclusion criteria.
        Key difference from inclusion: if a numeric check is relevant
        AND the patient does NOT violate it, the exclusion is VETOED.

        Also performs exact-match differentiation for confusable terms
        like "Type 1 Diabetes" vs "Type 2 Diabetes".
        """
        matches: List[Dict] = []
        conditions = patient_data.get("conditions") or patient_data.get("comorbidities") or []
        conditions_lower = [str(c).lower() for c in conditions]

        for idx, criterion in enumerate(criteria):
            if not criterion or not criterion.strip():
                continue

            criterion_clean = criterion.strip()
            criterion_lower = criterion_clean.lower()
            semantic = similarities[idx] if idx < len(similarities) else 0.0
            keyword = self._keyword_match_score(patient_text, criterion_clean)

            # ---------- Exact-match differentiation ----------
            # Prevent "Type 1 Diabetes" exclusion from being triggered
            # on a "Type 2 Diabetes" patient and vice versa.
            vetoed = False

            if "type 1" in criterion_lower and "diabetes" in criterion_lower:
                # Exclude only if patient actually HAS Type 1 Diabetes
                has_t1 = any("type 1" in c for c in conditions_lower)
                if not has_t1:
                    logger.info(
                        f"  🛡️ VETO [exclusion]: '{criterion_clean[:60]}' — "
                        f"patient does not have Type 1 Diabetes"
                    )
                    vetoed = True

            if "type 2" in criterion_lower and "diabetes" in criterion_lower:
                has_t2 = any("type 2" in c for c in conditions_lower)
                if not has_t2:
                    logger.info(
                        f"  🛡️ VETO [exclusion]: '{criterion_clean[:60]}' — "
                        f"patient does not have Type 2 Diabetes"
                    )
                    vetoed = True

            # Check for generic "diabetes" exclusion
            if ("diabetes" in criterion_lower
                    and "type 1" not in criterion_lower
                    and "type 2" not in criterion_lower):
                has_any_diabetes = any("diabetes" in c for c in conditions_lower)
                if not has_any_diabetes:
                    logger.info(
                        f"  🛡️ VETO [exclusion]: '{criterion_clean[:60]}' — "
                        f"patient does not have Diabetes"
                    )
                    vetoed = True

            # Check for specific condition-based exclusions (COPD, Asthma, etc.)
            for cond_name in ["copd", "asthma", "cancer", "pregnancy", "pregnant",
                              "heart failure", "liver disease", "hepatitis"]:
                if cond_name in criterion_lower:
                    has_cond = any(cond_name in c for c in conditions_lower)
                    if not has_cond:
                        logger.info(
                            f"  🛡️ VETO [exclusion]: '{criterion_clean[:60]}' — "
                            f"patient does not have {cond_name}"
                        )
                        vetoed = True
                    break

            if vetoed:
                continue

            # ---------- Numeric VETO ----------
            # If criterion contains a numeric condition (e.g. "eGFR < 30")
            # and the patient's value does NOT violate it, veto the exclusion.
            numeric_result = self._numeric_exclusion_check(patient_text, criterion_clean)
            if numeric_result == "pass":
                # Patient's numeric values do NOT violate this exclusion
                logger.info(
                    f"  🛡️ VETO [exclusion]: '{criterion_clean[:60]}' — "
                    f"numeric check shows patient does not violate this"
                )
                continue
            elif numeric_result == "fail":
                # Patient's numeric values DO violate this exclusion
                matches.append({
                    "criterion": criterion_clean,
                    "score": 0.90,  # high confidence numeric exclusion
                    "type": "exclusion",
                    "semantic_score": float(semantic),
                    "keyword_score": float(keyword),
                    "numeric_score": 1.0,
                })
                logger.info(f"  ❌ EXCL [exclusion]: '{criterion_clean[:60]}' (numeric violation)")
                continue

            # ---------- Standard semantic+keyword scoring ----------
            combined = (semantic * 0.55) + (keyword * 0.45)

            logger.debug(
                f"  [exclusion] '{criterion_clean[:60]}' "
                f"sem={semantic:.3f} kw={keyword:.3f} → {combined:.3f}"
            )

            if combined >= self.EXCLUDE_THRESHOLD:
                matches.append({
                    "criterion": criterion_clean,
                    "score": float(combined),
                    "type": "exclusion",
                    "semantic_score": float(semantic),
                    "keyword_score": float(keyword),
                    "numeric_score": 0.0,
                })
                logger.info(f"  ❌ EXCL [exclusion]: '{criterion_clean[:60]}' ({combined:.3f})")

        logger.info(f"  exclusion: {len(matches)}/{len(criteria)} criteria triggered")
        return matches

    # ------------------------------------------------------------------
    # Keyword matching
    # ------------------------------------------------------------------
    def _keyword_match_score(self, text: str, criterion: str) -> float:
        text_exp = nlp_engine.expand_synonyms(text).lower()
        criterion_exp = nlp_engine.expand_synonyms(criterion).lower()

        stop_words = {
            "with", "from", "have", "been", "that", "this", "will", "your",
            "their", "must", "shall", "should", "would", "could", "which",
            "patient", "subject", "study", "trial", "years", "year",
            "currently", "diagnosed", "least", "prior",
        }
        keywords = [
            w for w in re.findall(r"\b[a-z]+\b", criterion_exp)
            if len(w) > 3 and w not in stop_words
        ]

        if not keywords:
            return 0.0

        matched = sum(1 for kw in keywords if kw in text_exp)
        return float(matched / len(keywords))

    # ------------------------------------------------------------------
    # Numeric matching for INCLUSION
    # ------------------------------------------------------------------
    def _numeric_match_score_inclusion(self, text: str, criterion: str) -> float:
        """
        Check numeric values for INCLUSION criteria.
        Returns 0–1 indicating how well the patient satisfies the range.
        """
        score = 0.0
        checks_run = 0

        # ---- Age ----
        age_crit = re.search(
            r"age[^\d]*(\d+)\s*(?:[-–to]+\s*(\d+))?", criterion, re.IGNORECASE
        )
        age_text = re.search(r"age[:\s]+(\d+)", text, re.IGNORECASE)
        if age_crit and age_text:
            checks_run += 1
            patient_age = int(age_text.group(1))
            min_age = int(age_crit.group(1))
            max_age = int(age_crit.group(2)) if age_crit.group(2) else 120
            if min_age <= patient_age <= max_age:
                score += 1.0
                logger.debug(f"    Age {patient_age} ∈ [{min_age},{max_age}] ✓")

        # ---- HbA1c ----
        hba1c_crit = re.search(
            r"hba1c\s*[≥>=<≤]{1,2}\s*([\d.]+)|hba1c.*?([\d.]+)\s*[-–to]+\s*([\d.]+)",
            criterion, re.IGNORECASE
        )
        hba1c_text = re.search(r"hba1c\s*:?\s*([\d.]+)", text, re.IGNORECASE)
        if hba1c_crit and hba1c_text:
            checks_run += 1
            patient_v = self._safe_float(hba1c_text.group(1))
            g = hba1c_crit.groups()
            if g[1] and g[2]:
                if self._safe_float(g[1]) <= patient_v <= self._safe_float(g[2]):
                    score += 1.0
            elif g[0]:
                threshold_v = self._safe_float(g[0])
                op_m = re.search(r"([≥><≤=]{1,2})\s*" + re.escape(g[0]), criterion)
                op = op_m.group(1) if op_m else ">="
                if ("≥" in op or ">=" in op) and patient_v >= threshold_v:
                    score += 1.0
                elif ("≤" in op or "<=" in op) and patient_v <= threshold_v:
                    score += 1.0
                elif ">" in op and patient_v > threshold_v:
                    score += 1.0
                elif "<" in op and patient_v < threshold_v:
                    score += 1.0

        # ---- BMI ----
        bmi_crit = re.search(
            r"bmi\s*[≥>=<≤]{1,2}\s*([\d.]+)|bmi.*?([\d.]+)\s*[-–to]+\s*([\d.]+)",
            criterion, re.IGNORECASE
        )
        bmi_text = re.search(r"bmi\s*:?\s*([\d.]+)", text, re.IGNORECASE)
        if bmi_crit and bmi_text:
            checks_run += 1
            patient_v = self._safe_float(bmi_text.group(1))
            g = bmi_crit.groups()
            if g[1] and g[2] and self._safe_float(g[1]) <= patient_v <= self._safe_float(g[2]):
                score += 1.0
            elif g[0]:
                threshold_v = self._safe_float(g[0])
                op_m = re.search(r"([≥><≤=]{1,2})\s*" + re.escape(g[0]), criterion)
                op = op_m.group(1) if op_m else ">="
                if ("≥" in op or ">=" in op) and patient_v >= threshold_v:
                    score += 1.0
                elif ("≤" in op or "<=" in op) and patient_v <= threshold_v:
                    score += 1.0

        # ---- eGFR ----
        egfr_crit = re.search(r"egfr\s*[≥>=<≤]{1,2}\s*([\d.]+)", criterion, re.IGNORECASE)
        egfr_range = re.search(
            r"egfr.*?(\d+)\s*(?:to|[-–])\s*(\d+)", criterion, re.IGNORECASE
        )
        egfr_text = re.search(r"egfr\s*:?\s*(\d+)", text, re.IGNORECASE)
        if egfr_range and egfr_text:
            checks_run += 1
            patient_v = self._safe_float(egfr_text.group(1))
            low = self._safe_float(egfr_range.group(1))
            high = self._safe_float(egfr_range.group(2))
            if low <= patient_v <= high:
                score += 1.0
        elif egfr_crit and egfr_text:
            checks_run += 1
            patient_v = self._safe_float(egfr_text.group(1))
            threshold_v = self._safe_float(egfr_crit.group(1))
            op_m = re.search(r"([≥><≤=]{1,2})\s*" + re.escape(egfr_crit.group(1)), criterion)
            op = op_m.group(1) if op_m else ">="
            if ("≥" in op or ">=" in op) and patient_v >= threshold_v:
                score += 1.0
            elif ("≤" in op or "<=" in op or "<" in op) and patient_v <= threshold_v:
                score += 1.0

        if checks_run == 0:
            return 0.0
        return min(1.0, score / checks_run)

    # ------------------------------------------------------------------
    # Numeric check for EXCLUSION — returns "pass" / "fail" / "no_check"
    # ------------------------------------------------------------------
    def _numeric_exclusion_check(self, text: str, criterion: str) -> str:
        """
        For exclusion criteria containing numeric thresholds (e.g. "eGFR < 30"),
        check whether the patient ACTUALLY violates the condition.

        Returns:
          "fail"     — patient violates the exclusion (should be excluded)
          "pass"     — patient does NOT violate (veto the exclusion)
          "no_check" — no numeric comparison possible
        """
        criterion_lower = criterion.lower()

        # ---- eGFR < X ----
        egfr_exc = re.search(r"egfr\s*[<≤]\s*(\d+)", criterion, re.IGNORECASE)
        egfr_text = re.search(r"egfr\s*:?\s*(\d+)", text, re.IGNORECASE)
        if egfr_exc and egfr_text:
            patient_v = self._safe_float(egfr_text.group(1))
            threshold = self._safe_float(egfr_exc.group(1))
            if patient_v < threshold:
                logger.debug(f"    eGFR {patient_v} < {threshold} → EXCLUDED")
                return "fail"
            else:
                logger.debug(f"    eGFR {patient_v} >= {threshold} → PASS (not excluded)")
                return "pass"

        # ---- HbA1c > X (exclusion for high values) ----
        hba1c_exc = re.search(r"hba1c\s*[>≥]\s*([\d.]+)", criterion, re.IGNORECASE)
        hba1c_text = re.search(r"hba1c\s*:?\s*([\d.]+)", text, re.IGNORECASE)
        if hba1c_exc and hba1c_text:
            patient_v = self._safe_float(hba1c_text.group(1))
            threshold = self._safe_float(hba1c_exc.group(1))
            if patient_v > threshold:
                return "fail"
            else:
                return "pass"

        # ---- BMI > X or BMI < X ----
        bmi_exc = re.search(r"bmi\s*([<>≤≥]{1,2})\s*([\d.]+)", criterion, re.IGNORECASE)
        bmi_text = re.search(r"bmi\s*:?\s*([\d.]+)", text, re.IGNORECASE)
        if bmi_exc and bmi_text:
            patient_v = self._safe_float(bmi_text.group(2))
            threshold = self._safe_float(bmi_exc.group(2))
            op = bmi_exc.group(1)
            if "<" in op and patient_v < threshold:
                return "fail"
            elif ">" in op and patient_v > threshold:
                return "fail"
            else:
                return "pass"

        return "no_check"

    # ------------------------------------------------------------------
    # Overall score & status
    # ------------------------------------------------------------------
    def _compute_overall_score(
        self,
        inclusion_matches: List[Dict],
        exclusion_matches: List[Dict],
        all_inclusion: List[str],
        all_exclusion: List[str],
    ) -> float:
        n_inc = len(all_inclusion)
        n_exc = len(all_exclusion)

        # --- Inclusion component ---
        if n_inc > 0:
            coverage = len(inclusion_matches) / n_inc
            quality = (
                sum(m["score"] for m in inclusion_matches) / len(inclusion_matches)
                if inclusion_matches else 0.0
            )
            inclusion_component = (coverage * 0.6) + (quality * 0.4)
        else:
            inclusion_component = 0.5

        # --- Exclusion penalty ---
        if n_exc > 0 and exclusion_matches:
            exc_quality = sum(m["score"] for m in exclusion_matches) / len(exclusion_matches)
            exc_coverage = len(exclusion_matches) / n_exc
            exclusion_penalty = (exc_quality * 0.5 + exc_coverage * 0.5) * 0.50
        else:
            exclusion_penalty = 0.0

        # --- Bonus for no exclusions triggered (positive signal) ---
        if n_exc > 0 and len(exclusion_matches) == 0:
            inclusion_component = min(1.0, inclusion_component + 0.10)

        overall = max(0.0, min(1.0, inclusion_component - exclusion_penalty))
        return overall

    def _determine_status(
        self, overall: float, inclusion_matches: List, exclusion_matches: List
    ) -> str:
        high_risk_exclusions = [m for m in exclusion_matches if m["score"] >= 0.65]
        if high_risk_exclusions:
            return "not_eligible"
        if overall >= 0.55 and len(exclusion_matches) == 0:
            return "eligible"
        if overall <= 0.25 or len(exclusion_matches) >= 2:
            return "not_eligible"
        return "unknown"

    # ------------------------------------------------------------------
    # Confidence
    # ------------------------------------------------------------------
    def _calculate_confidence(
        self,
        inclusion_matches: List[Dict],
        exclusion_matches: List[Dict],
        all_inclusion: List[str],
        all_exclusion: List[str],
    ) -> float:
        n_inc = len(all_inclusion)
        n_exc = len(all_exclusion)
        total_criteria = n_inc + n_exc

        if total_criteria == 0:
            return 30.0

        addressed = len(inclusion_matches) + len(exclusion_matches)
        # For exclusion, NOT triggering is also "addressing" the criterion
        exc_not_triggered = n_exc - len(exclusion_matches)
        total_addressed = len(inclusion_matches) + n_exc  # all exclusions are "checked"

        coverage_pct = (total_addressed / total_criteria) * 55

        all_matches = inclusion_matches + exclusion_matches
        if all_matches:
            avg_quality = sum(m["score"] for m in all_matches) / len(all_matches)
            quality_pts = avg_quality * 30
        else:
            quality_pts = 10.0 if len(inclusion_matches) == 0 and n_inc == 0 else 0.0

        # Bonus: no exclusions triggered despite checking = strong positive signal
        consistency_pts = 15.0 if len(exclusion_matches) == 0 and n_exc > 0 else 0.0

        confidence = coverage_pct + quality_pts + consistency_pts

        # Hard caps
        if len(inclusion_matches) == 0 and n_inc > 0:
            confidence = min(confidence, 35.0)
        if len(exclusion_matches) > 3:
            confidence = min(confidence, 30.0)

        return float(max(10.0, min(95.0, confidence)))

    # ------------------------------------------------------------------
    # Evidence & summaries
    # ------------------------------------------------------------------
    def _extract_evidence(
        self, inclusion_matches: List[Dict], exclusion_matches: List[Dict]
    ) -> Dict:
        def _fmt(match: Dict) -> Dict:
            return {
                "criterion": match["criterion"],
                "match_score": round(float(match["score"]), 3),
                "semantic_score": round(float(match.get("semantic_score", 0)), 3),
                "keyword_score": round(float(match.get("keyword_score", 0)), 3),
                "numeric_score": round(float(match.get("numeric_score", 0)), 3),
                "type": match["type"],
            }

        return {
            "inclusion_evidence": [
                _fmt(m)
                for m in sorted(inclusion_matches, key=lambda x: x["score"], reverse=True)[:5]
            ],
            "exclusion_evidence": [
                _fmt(m)
                for m in sorted(exclusion_matches, key=lambda x: x["score"], reverse=True)[:5]
            ],
        }

    def _summarize_patient(self, patient_data: Dict) -> str:
        name = patient_data.get("name", "Unknown Patient")
        age = patient_data.get("age", "unknown age")
        gender = patient_data.get("gender", "unknown gender")
        conditions = patient_data.get("conditions") or patient_data.get("comorbidities") or []
        labs: Dict = patient_data.get("lab_values") or {}

        summary = f"{name}, {age} years old, {gender}"
        if conditions:
            summary += f", diagnosed with {', '.join(str(c) for c in conditions[:3])}"
        if labs.get("hba1c"):
            summary += f", HbA1c {labs['hba1c']}%"
        if labs.get("bmi"):
            summary += f", BMI {labs['bmi']}"
        return summary

    def _summarize_trial(self, trial_data: Dict) -> str:
        trial_id = trial_data.get("trial_id", "Unknown")
        title = trial_data.get("title", "Unknown Trial")
        condition = trial_data.get("condition", "")
        n_inc = len(trial_data.get("inclusion_criteria") or [])
        n_exc = len(trial_data.get("exclusion_criteria") or [])
        summary = f"Trial {trial_id}: {title}"
        if condition:
            summary += f" (Target: {condition})"
        summary += f" — {n_inc} inclusion / {n_exc} exclusion criteria"
        return summary


matching_engine = MatchingEngine()
