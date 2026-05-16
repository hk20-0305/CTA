// src/models/patient.js
export class Patient {
    constructor(data) {
      this.id = data.id;
      this.mrn = data.mrn;
      this.name = data.name;
      this.age = data.age;
      this.gender = data.gender;
      this.medications = data.medications || [];
      this.conditions = data.conditions || [];
      this.labValues = data.lab_values || {};
      this.createdAt = new Date(data.created_at);
    }
  }
  