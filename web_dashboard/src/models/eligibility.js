// src/models/eligibility.js
export class EligibilityCheck {
    constructor(data) {
      this.checkId = data.check_id;
      this.patientId = data.patient_id;
      this.trialId = data.trial_id;
      this.overallScore = data.overall_score;
      this.confidenceScore = data.confidence_score;
      this.status = data.status;
      this.explanation = data.explanation;
      this.evidence = data.evidence;
      this.createdAt = new Date(data.created_at);
    }
  }
  