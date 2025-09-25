"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PatientProfile, EmergencyContact } from "@/types";

interface PatientProfileProps {
  patient: PatientProfile;
  onUpdate: (updatedData: Partial<PatientProfile>) => Promise<void>;
  loading?: boolean;
}

interface EditablePatientData {
  first_name: string;
  last_name: string;
  phone_number: string;
  emergency_contact?: EmergencyContact;
}

export function PatientProfileComponent({ patient, onUpdate, loading = false }: PatientProfileProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState<EditablePatientData>({
    first_name: patient.first_name,
    last_name: patient.last_name,
    phone_number: patient.phone_number || '',
    emergency_contact: patient.emergency_contact || {
      name: '',
      phone: '',
      relationship: ''
    }
  });
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.first_name.trim()) {
      errors.first_name = 'First name is required';
    }

    if (!formData.last_name.trim()) {
      errors.last_name = 'Last name is required';
    }

    // Phone number validation (optional but must be valid if provided)
    if (formData.phone_number && !/^\+?[\d\s\-\(\)]+$/.test(formData.phone_number)) {
      errors.phone_number = 'Please enter a valid phone number';
    }

    // Emergency contact validation (all or none)
    const emergencyContact = formData.emergency_contact;
    if (emergencyContact && (emergencyContact.name || emergencyContact.phone || emergencyContact.relationship)) {
      if (!emergencyContact.name.trim()) {
        errors.emergency_contact_name = 'Emergency contact name is required';
      }
      if (!emergencyContact.phone.trim()) {
        errors.emergency_contact_phone = 'Emergency contact phone is required';
      }
      if (!emergencyContact.relationship.trim()) {
        errors.emergency_contact_relationship = 'Emergency contact relationship is required';
      }
      if (emergencyContact.phone && !/^\+?[\d\s\-\(\)]+$/.test(emergencyContact.phone)) {
        errors.emergency_contact_phone = 'Please enter a valid phone number';
      }
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      // Clean up emergency contact if all fields are empty
      const cleanedData = { ...formData };
      const emergencyContact = cleanedData.emergency_contact;
      if (emergencyContact && !emergencyContact.name && !emergencyContact.phone && !emergencyContact.relationship) {
        cleanedData.emergency_contact = undefined;
      }

      await onUpdate(cleanedData);
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to update profile:', error);
    }
  };

  const handleCancel = () => {
    setFormData({
      first_name: patient.first_name,
      last_name: patient.last_name,
      phone_number: patient.phone_number || '',
      emergency_contact: patient.emergency_contact || {
        name: '',
        phone: '',
        relationship: ''
      }
    });
    setValidationErrors({});
    setIsEditing(false);
  };

  const handleChange = (field: string, value: string) => {
    if (field.startsWith('emergency_contact.')) {
      const contactField = field.split('.')[1];
      setFormData(prev => ({
        ...prev,
        emergency_contact: {
          ...prev.emergency_contact!,
          [contactField]: value
        }
      }));
    } else {
      setFormData(prev => ({ ...prev, [field]: value }));
    }

    // Clear validation error for this field
    if (validationErrors[field]) {
      setValidationErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Patient Profile</CardTitle>
              <CardDescription>
                Manage your personal information and emergency contacts
              </CardDescription>
            </div>
            {!isEditing && (
              <Button onClick={() => setIsEditing(true)} disabled={loading}>
                Edit Profile
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Personal Information */}
            <div>
              <h3 className="text-lg font-medium mb-4">Personal Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label htmlFor="first_name" className="text-sm font-medium">
                    First Name
                  </label>
                  {isEditing ? (
                    <Input
                      id="first_name"
                      value={formData.first_name}
                      onChange={(e) => handleChange('first_name', e.target.value)}
                      disabled={loading}
                    />
                  ) : (
                    <p className="py-2 text-sm">{patient.first_name}</p>
                  )}
                  {validationErrors.first_name && (
                    <p className="text-sm text-red-600">{validationErrors.first_name}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <label htmlFor="last_name" className="text-sm font-medium">
                    Last Name
                  </label>
                  {isEditing ? (
                    <Input
                      id="last_name"
                      value={formData.last_name}
                      onChange={(e) => handleChange('last_name', e.target.value)}
                      disabled={loading}
                    />
                  ) : (
                    <p className="py-2 text-sm">{patient.last_name}</p>
                  )}
                  {validationErrors.last_name && (
                    <p className="text-sm text-red-600">{validationErrors.last_name}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <label htmlFor="email" className="text-sm font-medium">
                    Email Address
                  </label>
                  <p className="py-2 text-sm text-gray-600">{patient.user.email}</p>
                  <p className="text-xs text-gray-500">Contact support to change email</p>
                </div>

                <div className="space-y-2">
                  <label htmlFor="username" className="text-sm font-medium">
                    Username
                  </label>
                  <p className="py-2 text-sm text-gray-600">{patient.username}</p>
                  <p className="text-xs text-gray-500">Username cannot be changed</p>
                </div>

                <div className="space-y-2">
                  <label htmlFor="date_of_birth" className="text-sm font-medium">
                    Date of Birth
                  </label>
                  <p className="py-2 text-sm text-gray-600">{formatDate(patient.date_of_birth)}</p>
                  <p className="text-xs text-gray-500">Contact support to change date of birth</p>
                </div>

                <div className="space-y-2">
                  <label htmlFor="phone_number" className="text-sm font-medium">
                    Phone Number
                  </label>
                  {isEditing ? (
                    <Input
                      id="phone_number"
                      value={formData.phone_number}
                      onChange={(e) => handleChange('phone_number', e.target.value)}
                      placeholder="+1234567890"
                      disabled={loading}
                    />
                  ) : (
                    <p className="py-2 text-sm">{patient.phone_number || 'Not provided'}</p>
                  )}
                  {validationErrors.phone_number && (
                    <p className="text-sm text-red-600">{validationErrors.phone_number}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Emergency Contact */}
            <div>
              <h3 className="text-lg font-medium mb-4">Emergency Contact</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <label htmlFor="emergency_contact_name" className="text-sm font-medium">
                    Contact Name
                  </label>
                  {isEditing ? (
                    <Input
                      id="emergency_contact_name"
                      value={formData.emergency_contact?.name || ''}
                      onChange={(e) => handleChange('emergency_contact.name', e.target.value)}
                      placeholder="Emergency contact name"
                      disabled={loading}
                    />
                  ) : (
                    <p className="py-2 text-sm">{patient.emergency_contact?.name || 'Not provided'}</p>
                  )}
                  {validationErrors.emergency_contact_name && (
                    <p className="text-sm text-red-600">{validationErrors.emergency_contact_name}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <label htmlFor="emergency_contact_phone" className="text-sm font-medium">
                    Contact Phone
                  </label>
                  {isEditing ? (
                    <Input
                      id="emergency_contact_phone"
                      value={formData.emergency_contact?.phone || ''}
                      onChange={(e) => handleChange('emergency_contact.phone', e.target.value)}
                      placeholder="+1234567890"
                      disabled={loading}
                    />
                  ) : (
                    <p className="py-2 text-sm">{patient.emergency_contact?.phone || 'Not provided'}</p>
                  )}
                  {validationErrors.emergency_contact_phone && (
                    <p className="text-sm text-red-600">{validationErrors.emergency_contact_phone}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <label htmlFor="emergency_contact_relationship" className="text-sm font-medium">
                    Relationship
                  </label>
                  {isEditing ? (
                    <Input
                      id="emergency_contact_relationship"
                      value={formData.emergency_contact?.relationship || ''}
                      onChange={(e) => handleChange('emergency_contact.relationship', e.target.value)}
                      placeholder="e.g., Spouse, Parent, Sibling"
                      disabled={loading}
                    />
                  ) : (
                    <p className="py-2 text-sm">{patient.emergency_contact?.relationship || 'Not provided'}</p>
                  )}
                  {validationErrors.emergency_contact_relationship && (
                    <p className="text-sm text-red-600">{validationErrors.emergency_contact_relationship}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Account Information */}
            <div>
              <h3 className="text-lg font-medium mb-4">Account Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Profile Status</label>
                  <div className="py-2">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      patient.profile_completed 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-orange-100 text-orange-800'
                    }`}>
                      {patient.profile_completed ? 'Complete' : 'Incomplete'}
                    </span>
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Member Since</label>
                  <p className="py-2 text-sm">{formatDate(patient.user.created_at)}</p>
                </div>
              </div>
            </div>

            {isEditing && (
              <div className="flex gap-4 pt-4">
                <Button 
                  type="submit" 
                  disabled={loading}
                >
                  {loading ? 'Saving...' : 'Save Changes'}
                </Button>
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={handleCancel}
                  disabled={loading}
                >
                  Cancel
                </Button>
              </div>
            )}
          </form>
        </CardContent>
      </Card>
    </div>
  );
}