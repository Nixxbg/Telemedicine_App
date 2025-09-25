"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PatientProfile, Appointment, MedicalRecord } from "@/types";

interface PatientDashboardProps {
  patient: PatientProfile;
  recentAppointments?: Appointment[];
  medicalRecords?: MedicalRecord[];
  onViewMedicalRecords: () => void;
  onBookAppointment: () => void;
  onViewMessages: () => void;
}

export function PatientDashboard({
  patient,
  recentAppointments = [],
  medicalRecords = [],
  onViewMedicalRecords,
  onBookAppointment,
  onViewMessages
}: PatientDashboardProps) {
  const getAppointmentStatusColor = (status: string) => {
    switch (status) {
      case 'scheduled':
        return 'text-blue-600 bg-blue-50';
      case 'confirmed':
        return 'text-green-600 bg-green-50';
      case 'completed':
        return 'text-gray-600 bg-gray-50';
      case 'cancelled':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-6 rounded-lg">
        <h1 className="text-2xl font-bold mb-2">
          Welcome, {patient.first_name} {patient.last_name}
        </h1>
        <p className="text-blue-100">
          Manage your health records, appointments, and communications with your healthcare providers
        </p>
      </div>

      {/* Profile Completion Alert */}
      {!patient.profile_completed && (
        <Card className="border-orange-200 bg-orange-50">
          <CardHeader>
            <CardTitle className="text-orange-800">Complete Your Profile</CardTitle>
            <CardDescription className="text-orange-700">
              Complete your medical history to help your doctors provide better care
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button 
              variant="outline" 
              className="border-orange-300 text-orange-800 hover:bg-orange-100"
            >
              Complete Medical Questionnaire
            </Button>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>
              Common tasks and services
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button 
              onClick={onBookAppointment}
              className="w-full justify-start"
              variant="outline"
            >
              📅 Book Appointment
            </Button>
            <Button 
              onClick={onViewMedicalRecords}
              className="w-full justify-start"
              variant="outline"
            >
              📋 View Medical Records
            </Button>
            <Button 
              onClick={onViewMessages}
              className="w-full justify-start"
              variant="outline"
            >
              💬 Messages
            </Button>
          </CardContent>
        </Card>

        {/* Upcoming Appointments */}
        <Card>
          <CardHeader>
            <CardTitle>Upcoming Appointments</CardTitle>
            <CardDescription>
              Your scheduled consultations
            </CardDescription>
          </CardHeader>
          <CardContent>
            {recentAppointments.length === 0 ? (
              <p className="text-gray-500 text-sm">No upcoming appointments</p>
            ) : (
              <div className="space-y-3">
                {recentAppointments.slice(0, 3).map((appointment) => (
                  <div key={appointment.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                    <div>
                      <p className="font-medium text-sm">
                        {formatDate(appointment.scheduled_start)}
                      </p>
                      <p className="text-xs text-gray-600">
                        {appointment.consultation_type}
                      </p>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getAppointmentStatusColor(appointment.status)}`}>
                      {appointment.status}
                    </span>
                  </div>
                ))}
                {recentAppointments.length > 3 && (
                  <Button variant="ghost" size="sm" className="w-full">
                    View All Appointments
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Medical Records Summary */}
        <Card>
          <CardHeader>
            <CardTitle>Medical Records</CardTitle>
            <CardDescription>
              Recent updates to your health records
            </CardDescription>
          </CardHeader>
          <CardContent>
            {medicalRecords.length === 0 ? (
              <p className="text-gray-500 text-sm">No medical records yet</p>
            ) : (
              <div className="space-y-3">
                {medicalRecords.slice(0, 3).map((record) => (
                  <div key={record.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                    <div>
                      <p className="font-medium text-sm">{record.title}</p>
                      <p className="text-xs text-gray-600 capitalize">
                        {record.record_type}
                      </p>
                    </div>
                    <div className="text-xs text-gray-500">
                      v{record.current_version}
                    </div>
                  </div>
                ))}
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="w-full"
                  onClick={onViewMedicalRecords}
                >
                  View All Records
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Health Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Health Overview</CardTitle>
            <CardDescription>
              Quick summary of your health status
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center py-2 border-b">
                <span className="text-sm font-medium">Allergies</span>
                <span className="text-sm text-gray-600">
                  {medicalRecords.filter(r => r.record_type === 'allergy').length} recorded
                </span>
              </div>
              <div className="flex justify-between items-center py-2 border-b">
                <span className="text-sm font-medium">Medications</span>
                <span className="text-sm text-gray-600">
                  {medicalRecords.filter(r => r.record_type === 'medication').length} active
                </span>
              </div>
              <div className="flex justify-between items-center py-2 border-b">
                <span className="text-sm font-medium">Conditions</span>
                <span className="text-sm text-gray-600">
                  {medicalRecords.filter(r => r.record_type === 'condition').length} managed
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Account Information</CardTitle>
            <CardDescription>
              Your profile and account settings
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium text-gray-500">Username</label>
                <p className="text-sm">{patient.username}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Email</label>
                <p className="text-sm">{patient.user.email}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Phone</label>
                <p className="text-sm">{patient.phone_number || 'Not provided'}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Member Since</label>
                <p className="text-sm">
                  {formatDate(patient.user.created_at)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}