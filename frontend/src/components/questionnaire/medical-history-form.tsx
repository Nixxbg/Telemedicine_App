"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

interface MedicalHistoryData {
  // Personal Medical History
  chronic_conditions: string[];
  current_medications: Array<{
    name: string;
    dosage: string;
    frequency: string;
    prescribing_doctor?: string;
  }>;
  allergies: Array<{
    allergen: string;
    reaction: string;
    severity: 'mild' | 'moderate' | 'severe';
  }>;
  previous_surgeries: Array<{
    procedure: string;
    date: string;
    hospital?: string;
    complications?: string;
  }>;
  immunizations: Array<{
    vaccine: string;
    date: string;
  }>;
  
  // Family Medical History
  family_history: Array<{
    relation: string;
    condition: string;
    age_of_onset?: number;
  }>;
  
  // Lifestyle Factors
  smoking_status: 'never' | 'former' | 'current';
  alcohol_consumption: 'none' | 'occasional' | 'moderate' | 'heavy';
  exercise_frequency: 'none' | 'rarely' | 'weekly' | 'daily';
  dietary_restrictions: string[];
  
  // Additional Information
  emergency_medical_info: string;
  healthcare_goals: string;
  additional_notes: string;
}

interface MedicalHistoryFormProps {
  initialData?: Partial<MedicalHistoryData>;
  onSave: (data: MedicalHistoryData, isComplete: boolean) => Promise<void>;
  onNext?: () => void;
  loading?: boolean;
}

export function MedicalHistoryForm({ 
  initialData = {}, 
  onSave, 
  onNext, 
  loading = false 
}: MedicalHistoryFormProps) {
  const [formData, setFormData] = useState<MedicalHistoryData>({
    chronic_conditions: initialData.chronic_conditions || [],
    current_medications: initialData.current_medications || [],
    allergies: initialData.allergies || [],
    previous_surgeries: initialData.previous_surgeries || [],
    immunizations: initialData.immunizations || [],
    family_history: initialData.family_history || [],
    smoking_status: initialData.smoking_status || 'never',
    alcohol_consumption: initialData.alcohol_consumption || 'none',
    exercise_frequency: initialData.exercise_frequency || 'none',
    dietary_restrictions: initialData.dietary_restrictions || [],
    emergency_medical_info: initialData.emergency_medical_info || '',
    healthcare_goals: initialData.healthcare_goals || '',
    additional_notes: initialData.additional_notes || ''
  });

  const [currentStep, setCurrentStep] = useState(0);
  const [newCondition, setNewCondition] = useState('');
  const [newMedication, setNewMedication] = useState({
    name: '', dosage: '', frequency: '', prescribing_doctor: ''
  });
  const [newAllergy, setNewAllergy] = useState<{
    allergen: string;
    reaction: string;
    severity: 'mild' | 'moderate' | 'severe';
  }>({
    allergen: '', reaction: '', severity: 'mild'
  });

  const steps = [
    'Medical Conditions',
    'Medications & Allergies', 
    'Surgical History',
    'Family History',
    'Lifestyle',
    'Additional Information'
  ];

  const getCompletionPercentage = () => {
    let completed = 0;
    let total = 0;

    // Count completed sections
    if (formData.chronic_conditions.length > 0) completed++;
    total++;
    
    if (formData.current_medications.length > 0 || formData.allergies.length > 0) completed++;
    total++;
    
    if (formData.previous_surgeries.length > 0 || formData.immunizations.length > 0) completed++;
    total++;
    
    if (formData.family_history.length > 0) completed++;
    total++;
    
    if (formData.smoking_status !== 'never' || formData.alcohol_consumption !== 'none' || 
        formData.exercise_frequency !== 'none') completed++;
    total++;
    
    if (formData.healthcare_goals.trim() || formData.additional_notes.trim()) completed++;
    total++;

    return Math.round((completed / total) * 100);
  };

  const handleSave = async (isComplete: boolean = false) => {
    await onSave(formData, isComplete);
  };

  const addCondition = () => {
    if (newCondition.trim()) {
      setFormData(prev => ({
        ...prev,
        chronic_conditions: [...prev.chronic_conditions, newCondition.trim()]
      }));
      setNewCondition('');
    }
  };

  const removeCondition = (index: number) => {
    setFormData(prev => ({
      ...prev,
      chronic_conditions: prev.chronic_conditions.filter((_, i) => i !== index)
    }));
  };

  const addMedication = () => {
    if (newMedication.name.trim()) {
      setFormData(prev => ({
        ...prev,
        current_medications: [...prev.current_medications, { ...newMedication }]
      }));
      setNewMedication({ name: '', dosage: '', frequency: '', prescribing_doctor: '' });
    }
  };

  const removeMedication = (index: number) => {
    setFormData(prev => ({
      ...prev,
      current_medications: prev.current_medications.filter((_, i) => i !== index)
    }));
  };

  const addAllergy = () => {
    if (newAllergy.allergen.trim()) {
      setFormData(prev => ({
        ...prev,
        allergies: [...prev.allergies, { ...newAllergy }]
      }));
      setNewAllergy({ allergen: '', reaction: '', severity: 'mild' });
    }
  };

  const removeAllergy = (index: number) => {
    setFormData(prev => ({
      ...prev,
      allergies: prev.allergies.filter((_, i) => i !== index)
    }));
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 0: // Medical Conditions
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium mb-4">Current Medical Conditions</h3>
              <div className="space-y-3">
                {formData.chronic_conditions.map((condition, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                    <span>{condition}</span>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => removeCondition(index)}
                    >
                      Remove
                    </Button>
                  </div>
                ))}
                <div className="flex gap-2">
                  <Input
                    value={newCondition}
                    onChange={(e) => setNewCondition(e.target.value)}
                    placeholder="Enter a medical condition"
                    onKeyPress={(e) => e.key === 'Enter' && addCondition()}
                  />
                  <Button type="button" onClick={addCondition}>
                    Add
                  </Button>
                </div>
              </div>
            </div>
          </div>
        );

      case 1: // Medications & Allergies
        return (
          <div className="space-y-8">
            {/* Current Medications */}
            <div>
              <h3 className="text-lg font-medium mb-4">Current Medications</h3>
              <div className="space-y-3">
                {formData.current_medications.map((med, index) => (
                  <div key={index} className="p-4 bg-gray-50 rounded-md">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium">{med.name}</p>
                        <p className="text-sm text-gray-600">
                          {med.dosage} - {med.frequency}
                        </p>
                        {med.prescribing_doctor && (
                          <p className="text-sm text-gray-500">
                            Prescribed by: {med.prescribing_doctor}
                          </p>
                        )}
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeMedication(index)}
                      >
                        Remove
                      </Button>
                    </div>
                  </div>
                ))}
                
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    value={newMedication.name}
                    onChange={(e) => setNewMedication(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="Medication name"
                  />
                  <Input
                    value={newMedication.dosage}
                    onChange={(e) => setNewMedication(prev => ({ ...prev, dosage: e.target.value }))}
                    placeholder="Dosage (e.g., 10mg)"
                  />
                  <Input
                    value={newMedication.frequency}
                    onChange={(e) => setNewMedication(prev => ({ ...prev, frequency: e.target.value }))}
                    placeholder="Frequency (e.g., twice daily)"
                  />
                  <Input
                    value={newMedication.prescribing_doctor}
                    onChange={(e) => setNewMedication(prev => ({ ...prev, prescribing_doctor: e.target.value }))}
                    placeholder="Prescribing doctor (optional)"
                  />
                </div>
                <Button type="button" onClick={addMedication} className="w-full">
                  Add Medication
                </Button>
              </div>
            </div>

            {/* Allergies */}
            <div>
              <h3 className="text-lg font-medium mb-4">Allergies</h3>
              <div className="space-y-3">
                {formData.allergies.map((allergy, index) => (
                  <div key={index} className="p-4 bg-red-50 rounded-md">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium text-red-800">{allergy.allergen}</p>
                        <p className="text-sm text-red-700">
                          Reaction: {allergy.reaction}
                        </p>
                        <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium mt-1 ${
                          allergy.severity === 'severe' ? 'bg-red-200 text-red-800' :
                          allergy.severity === 'moderate' ? 'bg-orange-200 text-orange-800' :
                          'bg-yellow-200 text-yellow-800'
                        }`}>
                          {allergy.severity}
                        </span>
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeAllergy(index)}
                      >
                        Remove
                      </Button>
                    </div>
                  </div>
                ))}
                
                <div className="grid grid-cols-3 gap-2">
                  <Input
                    value={newAllergy.allergen}
                    onChange={(e) => setNewAllergy(prev => ({ ...prev, allergen: e.target.value }))}
                    placeholder="Allergen"
                  />
                  <Input
                    value={newAllergy.reaction}
                    onChange={(e) => setNewAllergy(prev => ({ ...prev, reaction: e.target.value }))}
                    placeholder="Reaction"
                  />
                  <select
                    value={newAllergy.severity}
                    onChange={(e) => setNewAllergy(prev => ({ 
                      ...prev, 
                      severity: e.target.value as 'mild' | 'moderate' | 'severe' 
                    }))}
                    className="px-3 py-2 border border-input rounded-md"
                  >
                    <option value="mild">Mild</option>
                    <option value="moderate">Moderate</option>
                    <option value="severe">Severe</option>
                  </select>
                </div>
                <Button type="button" onClick={addAllergy} className="w-full">
                  Add Allergy
                </Button>
              </div>
            </div>
          </div>
        );

      case 4: // Lifestyle
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="text-sm font-medium mb-2 block">Smoking Status</label>
                <select
                  value={formData.smoking_status}
                  onChange={(e) => setFormData(prev => ({ 
                    ...prev, 
                    smoking_status: e.target.value as any 
                  }))}
                  className="w-full px-3 py-2 border border-input rounded-md"
                >
                  <option value="never">Never</option>
                  <option value="former">Former smoker</option>
                  <option value="current">Current smoker</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Alcohol Consumption</label>
                <select
                  value={formData.alcohol_consumption}
                  onChange={(e) => setFormData(prev => ({ 
                    ...prev, 
                    alcohol_consumption: e.target.value as any 
                  }))}
                  className="w-full px-3 py-2 border border-input rounded-md"
                >
                  <option value="none">None</option>
                  <option value="occasional">Occasional</option>
                  <option value="moderate">Moderate</option>
                  <option value="heavy">Heavy</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Exercise Frequency</label>
                <select
                  value={formData.exercise_frequency}
                  onChange={(e) => setFormData(prev => ({ 
                    ...prev, 
                    exercise_frequency: e.target.value as any 
                  }))}
                  className="w-full px-3 py-2 border border-input rounded-md"
                >
                  <option value="none">None</option>
                  <option value="rarely">Rarely</option>
                  <option value="weekly">Weekly</option>
                  <option value="daily">Daily</option>
                </select>
              </div>
            </div>
          </div>
        );

      case 5: // Additional Information
        return (
          <div className="space-y-6">
            <div>
              <label className="text-sm font-medium mb-2 block">
                Emergency Medical Information
              </label>
              <Textarea
                value={formData.emergency_medical_info}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  emergency_medical_info: e.target.value 
                }))}
                placeholder="Important medical information for emergency situations..."
                rows={3}
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">
                Healthcare Goals
              </label>
              <Textarea
                value={formData.healthcare_goals}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  healthcare_goals: e.target.value 
                }))}
                placeholder="What are your main health and wellness goals?"
                rows={3}
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">
                Additional Notes
              </label>
              <Textarea
                value={formData.additional_notes}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  additional_notes: e.target.value 
                }))}
                placeholder="Any other information you'd like your healthcare provider to know..."
                rows={4}
              />
            </div>
          </div>
        );

      default:
        return <div>Step not implemented</div>;
    }
  };

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle>Medical History Questionnaire</CardTitle>
        <CardDescription>
          Help us provide better care by sharing your medical history
        </CardDescription>
        <div className="mt-4">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Progress</span>
            <span>{getCompletionPercentage()}% Complete</span>
          </div>
          <Progress value={getCompletionPercentage()} className="w-full" />
        </div>
      </CardHeader>
      <CardContent>
        {/* Step Navigator */}
        <div className="flex flex-wrap gap-2 mb-8">
          {steps.map((step, index) => (
            <button
              key={index}
              onClick={() => setCurrentStep(index)}
              className={`px-3 py-2 text-sm rounded-md transition-colors ${
                index === currentStep
                  ? 'bg-blue-600 text-white'
                  : index < currentStep
                  ? 'bg-green-100 text-green-800'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {index + 1}. {step}
            </button>
          ))}
        </div>

        {/* Step Content */}
        <div className="mb-8">
          {renderStepContent()}
        </div>

        {/* Navigation */}
        <div className="flex justify-between">
          <Button
            type="button"
            variant="outline"
            onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
            disabled={currentStep === 0}
          >
            Previous
          </Button>

          <div className="space-x-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => handleSave(false)}
              disabled={loading}
            >
              {loading ? 'Saving...' : 'Save Progress'}
            </Button>

            {currentStep < steps.length - 1 ? (
              <Button
                type="button"
                onClick={() => setCurrentStep(Math.min(steps.length - 1, currentStep + 1))}
              >
                Next
              </Button>
            ) : (
              <Button
                type="button"
                onClick={() => handleSave(true)}
                disabled={loading}
              >
                {loading ? 'Completing...' : 'Complete Questionnaire'}
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}