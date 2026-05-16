// src/models/trial.js
export class Trial {
    constructor(data) {
      this.id = data.id;
      this.trialId = data.trial_id;
      this.title = data.title;
      this.condition = data.condition;
      this.phase = data.phase;
      this.inclusionCriteria = data.inclusion_criteria || [];
      this.exclusionCriteria = data.exclusion_criteria || [];
      this.createdAt = new Date(data.created_at);
    }
  }
  