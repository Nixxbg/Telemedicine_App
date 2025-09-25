"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

interface SymptomsData {
  chief_complaint: string;
  symptom_duration: string;
  symptom_severity: 1 | 2 | 3 | 4 | 5;
  symptom_frequency: 'constant' | 'intermittent' | 'once' | 'daily' | 'weekly';
  location: string;
  quality: string;
  radiation: string;
  associated_symptoms: string[];
  alleviating_factors: string[];
  aggravating_factors: string[];
  previous_episodes: boolean;
  previous_episodes_details: string;
  current_treatments: string[];
  treatment_effectiveness: string;
  functional_impact: string;
  urgency_level: 'low' | 'medium' | 'high' | 'urgent';
  additional_concerns: string;
}

interface SymptomsFormProps {
  initialData?: Partial<SymptomsData>;
  onSubmit: (data: SymptomsData) => Promise<void>;
  loading?: boolean;
}

export function SymptomsForm({ 
  initialData = {}, 
  onSubmit, 
  loading = false 
}: SymptomsFormProps) {
  const [formData, setFormData] = useState<SymptomsData>({
    chief_complaint: initialData.chief_complaint || '',
    symptom_duration: initialData.symptom_duration || '',
    symptom_severity: initialData.symptom_severity || 1,
    symptom_frequency: initialData.symptom_frequency || 'once',
    location: initialData.location || '',
    quality: initialData.quality || '',
    radiation: initialData.radiation || '',
    associated_symptoms: initialData.associated_symptoms || [],
    alleviating_factors: initialData.alleviating_factors || [],
    aggravating_factors: initialData.aggravating_factors || [],
    previous_episodes: initialData.previous_episodes || false,
    previous_episodes_details: initialData.previous_episodes_details || '',
    current_treatments: initialData.current_treatments || [],
    treatment_effectiveness: initialData.treatment_effectiveness || '',
    functional_impact: initialData.functional_impact || '',
    urgency_level: initialData.urgency_level || 'low',
    additional_concerns: initialData.additional_concerns || ''
  });

  const [newSymptom, setNewSymptom] = useState('');
  const [newAlleviatingFactor, setNewAlleviatingFactor] = useState('');
  const [newAggravatingFactor, setNewAggravatingFactor] = useState('');
  const [newTreatment, setNewTreatment] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit(formData);
  };

  const updateField = (field: keyof SymptomsData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const addToArray = (field: 'associated_symptoms' | 'alleviating_factors' | 'aggravating_factors' | 'current_treatments', value: string) => {
    if (value.trim()) {
      setFormData(prev => ({
        ...prev,
        [field]: [...prev[field], value.trim()]
      }));
    }
  };

  const removeFromArray = (field: 'associated_symptoms' | 'alleviating_factors' | 'aggravating_factors' | 'current_treatments', index: number) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].filter((_, i) => i !== index)
    }));
  };

  const getSeverityColor = (severity: number) => {
    if (severity <= 2) return 'text-green-600';
    if (severity <= 3) return 'text-yellow-600'; 
    if (severity <= 4) return 'text-orange-600';
    return 'text-red-600';
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'low': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';  
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'urgent': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle>Current Symptoms Assessment</CardTitle>
        <CardDescription>
          Please describe your current symptoms in detail to help your healthcare provider
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Primary Complaint */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Primary Concern</h3>
            
            <div>
              <label className="text-sm font-medium mb-2 block">
                Chief Complaint *
              </label>
              <Textarea
                value={formData.chief_complaint}
                onChange={(e) => updateField('chief_complaint', e.target.value)}
                placeholder="In your own words, what is the main problem you're experiencing?"
                rows={3}
                required
                disabled={loading}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  How long have you had this symptom?
                </label>
                <Input
                  value={formData.symptom_duration}
                  onChange={(e) => updateField('symptom_duration', e.target.value)}
                  placeholder="e.g., 3 days, 2 weeks, 1 month"
                  disabled={loading}
                />
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">
                  Urgency Level
                </label>
                <select
                  value={formData.urgency_level}
                  onChange={(e) => updateField('urgency_level', e.target.value)}
                  className="w-full px-3 py-2 border border-input rounded-md"
                  disabled={loading}
                >
                  <option value="low">Low - Can wait for routine appointment</option>
                  <option value="medium">Medium - Should be seen within a week</option>
                  <option value="high">High - Should be seen within 24-48 hours</option>
                  <option value="urgent">Urgent - Needs immediate attention</option>
                </select>
                <div className="mt-1">
                  <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${getUrgencyColor(formData.urgency_level)}`}>
                    {formData.urgency_level.toUpperCase()}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Symptom Details */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Symptom Details</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Pain/Symptom Severity (1-5 scale)
                </label>
                <div className="space-y-2">
                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={formData.symptom_severity}
                    onChange={(e) => updateField('symptom_severity', parseInt(e.target.value) as any)}
                    className="w-full"
                    disabled={loading}
                  />
                  <div className="flex justify-between text-sm text-gray-600">
                    <span>1 - Minimal</span>
                    <span>3 - Moderate</span>
                    <span>5 - Severe</span>
                  </div>
                  <div className="text-center">
                    <span className={`text-lg font-bold ${getSeverityColor(formData.symptom_severity)}`}>
                      {formData.symptom_severity}/5
                    </span>
                  </div>
                </div>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">
                  Frequency
                </label>
                <select
                  value={formData.symptom_frequency}
                  onChange={(e) => updateField('symptom_frequency', e.target.value)}
                  className="w-full px-3 py-2 border border-input rounded-md"
                  disabled={loading}
                >
                  <option value="once">Happened once</option>
                  <option value="intermittent">Comes and goes</option>
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="constant">Constant</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Location
                </label>
                <Input
                  value={formData.location}
                  onChange={(e) => updateField('location', e.target.value)}
                  placeholder="Where do you feel it?"
                  disabled={loading}
                />
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">
                  Quality/Character
                </label>
                <Input
                  value={formData.quality}
                  onChange={(e) => updateField('quality', e.target.value)}
                  placeholder="Sharp, dull, burning, throbbing?"
                  disabled={loading}
                />
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">
                  Radiation
                </label>
                <Input
                  value={formData.radiation}
                  onChange={(e) => updateField('radiation', e.target.value)}
                  placeholder="Does it spread anywhere?"
                  disabled={loading}
                />
              </div>
            </div>
          </div>

          {/* Associated Symptoms */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Associated Symptoms</h3>
            
            <div className="space-y-3">
              {formData.associated_symptoms.map((symptom, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                  <span>{symptom}</span>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => removeFromArray('associated_symptoms', index)}
                    disabled={loading}
                  >
                    Remove
                  </Button>
                </div>
              ))}
              
              <div className="flex gap-2">
                <Input
                  value={newSymptom}
                  onChange={(e) => setNewSymptom(e.target.value)}
                  placeholder="Any other symptoms you're experiencing?"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      addToArray('associated_symptoms', newSymptom);
                      setNewSymptom('');
                    }
                  }}
                  disabled={loading}
                />
                <Button
                  type="button"
                  onClick={() => {
                    addToArray('associated_symptoms', newSymptom);
                    setNewSymptom('');
                  }}
                  disabled={loading}
                >
                  Add
                </Button>
              </div>
            </div>
          </div>

          {/* Modifying Factors */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-4">
              <h3 className="text-lg font-medium">What Makes It Better?</h3>
              
              <div className="space-y-3">
                {formData.alleviating_factors.map((factor, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-green-50 rounded-md">
                    <span>{factor}</span>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => removeFromArray('alleviating_factors', index)}
                      disabled={loading}
                    >
                      Remove
                    </Button>
                  </div>
                ))}
                
                <div className="flex gap-2">
                  <Input
                    value={newAlleviatingFactor}
                    onChange={(e) => setNewAlleviatingFactor(e.target.value)}
                    placeholder="Rest, medication, heat, etc."
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        addToArray('alleviating_factors', newAlleviatingFactor);
                        setNewAlleviatingFactor('');
                      }
                    }}
                    disabled={loading}
                  />
                  <Button
                    type="button"
                    onClick={() => {
                      addToArray('alleviating_factors', newAlleviatingFactor);
                      setNewAlleviatingFactor('');
                    }}
                    disabled={loading}
                  >
                    Add
                  </Button>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="text-lg font-medium">What Makes It Worse?</h3>
              
              <div className="space-y-3">
                {formData.aggravating_factors.map((factor, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-red-50 rounded-md">
                    <span>{factor}</span>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => removeFromArray('aggravating_factors', index)}
                      disabled={loading}
                    >
                      Remove
                    </Button>
                  </div>
                ))}
                
                <div className="flex gap-2">
                  <Input
                    value={newAggravatingFactor}
                    onChange={(e) => setNewAggravatingFactor(e.target.value)}
                    placeholder="Movement, stress, food, etc."
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        addToArray('aggravating_factors', newAggravatingFactor);
                        setNewAggravatingFactor('');
                      }
                    }}
                    disabled={loading}
                  />
                  <Button
                    type="button"
                    onClick={() => {
                      addToArray('aggravating_factors', newAggravatingFactor);
                      setNewAggravatingFactor('');
                    }}
                    disabled={loading}
                  >
                    Add
                  </Button>
                </div>
              </div>
            </div>
          </div>

          {/* Previous Episodes & Current Treatment */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Previous Episodes & Treatment</h3>
            
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  id="previous_episodes"
                  checked={formData.previous_episodes}
                  onChange={(e) => updateField('previous_episodes', e.target.checked)}
                  disabled={loading}
                />
                <label htmlFor="previous_episodes" className="text-sm font-medium">
                  I have experienced similar symptoms before
                </label>
              </div>

              {formData.previous_episodes && (
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Please describe the previous episodes
                  </label>
                  <Textarea
                    value={formData.previous_episodes_details}
                    onChange={(e) => updateField('previous_episodes_details', e.target.value)}
                    placeholder="When did they occur? How were they treated? What was the outcome?"
                    rows={3}
                    disabled={loading}
                  />
                </div>
              )}

              <div>
                <h4 className="text-md font-medium mb-3">Current Treatments</h4>
                <div className="space-y-3">
                  {formData.current_treatments.map((treatment, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-blue-50 rounded-md">
                      <span>{treatment}</span>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeFromArray('current_treatments', index)}
                        disabled={loading}
                      >
                        Remove
                      </Button>
                    </div>
                  ))}
                  
                  <div className="flex gap-2">
                    <Input
                      value={newTreatment}
                      onChange={(e) => setNewTreatment(e.target.value)}
                      placeholder="Medications, therapies, home remedies, etc."
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          addToArray('current_treatments', newTreatment);
                          setNewTreatment('');
                        }
                      }}
                      disabled={loading}
                    />
                    <Button
                      type="button"
                      onClick={() => {
                        addToArray('current_treatments', newTreatment);
                        setNewTreatment('');
                      }}
                      disabled={loading}
                    >
                      Add
                    </Button>
                  </div>
                </div>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">
                  How effective have your current treatments been?
                </label>
                <Textarea
                  value={formData.treatment_effectiveness}
                  onChange={(e) => updateField('treatment_effectiveness', e.target.value)}
                  placeholder="Are they helping? Any side effects?"
                  rows={2}
                  disabled={loading}
                />
              </div>
            </div>
          </div>

          {/* Impact and Additional Concerns */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Impact & Additional Information</h3>
            
            <div>
              <label className="text-sm font-medium mb-2 block">
                How are these symptoms affecting your daily life?
              </label>
              <Textarea
                value={formData.functional_impact}
                onChange={(e) => updateField('functional_impact', e.target.value)}
                placeholder="Work, sleep, activities, mood, etc."
                rows={3}
                disabled={loading}
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">
                Any other concerns or questions?
              </label>
              <Textarea
                value={formData.additional_concerns}
                onChange={(e) => updateField('additional_concerns', e.target.value)}
                placeholder="Anything else you'd like your healthcare provider to know?"
                rows={3}
                disabled={loading}
              />
            </div>
          </div>

          <div className="flex justify-end pt-4">
            <Button 
              type="submit" 
              disabled={loading || !formData.chief_complaint.trim()}
            >
              {loading ? 'Submitting...' : 'Submit Symptoms Assessment'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}