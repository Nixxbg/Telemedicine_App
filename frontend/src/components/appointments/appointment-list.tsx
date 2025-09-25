"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Appointment, PatientProfile, DoctorProfile } from "@/types";

interface AppointmentListProps {
  appointments: Appointment[];
  patients?: Record<string, PatientProfile>;
  doctors?: Record<string, DoctorProfile>;
  userType: 'patient' | 'doctor';
  onViewDetails: (appointment: Appointment) => void;
  onCancel: (appointmentId: string) => Promise<void>;
  onReschedule: (appointmentId: string) => void;
  loading?: boolean;
}

export function AppointmentList({
  appointments,
  patients = {},
  doctors = {},
  userType,
  onViewDetails,
  onCancel,
  onReschedule,
  loading = false
}: AppointmentListProps) {
  const [filter, setFilter] = useState<'all' | 'upcoming' | 'completed' | 'cancelled'>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'date' | 'status' | 'type'>('date');

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'scheduled':
        return 'bg-blue-100 text-blue-800';
      case 'confirmed':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
        return 'bg-orange-100 text-orange-800';
      case 'completed':
        return 'bg-gray-100 text-gray-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      case 'no_show':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getTimeUntilAppointment = (scheduledStart: string) => {
    const now = new Date();
    const appointmentTime = new Date(scheduledStart);
    const diffMs = appointmentTime.getTime() - now.getTime();
    const diffMinutes = Math.round(diffMs / (1000 * 60));
    
    if (diffMinutes < 0) return 'Past';
    if (diffMinutes < 60) return `${diffMinutes}m`;
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}h`;
    return `${Math.floor(diffMinutes / 1440)}d`;
  };

  const isUpcoming = (scheduledStart: string) => {
    return new Date(scheduledStart) > new Date();
  };

  const canCancel = (appointment: Appointment) => {
    const isUpcomingAppointment = isUpcoming(appointment.scheduled_start);
    const cancelableStatuses = ['scheduled', 'confirmed'];
    return isUpcomingAppointment && cancelableStatuses.includes(appointment.status);
  };

  const canReschedule = (appointment: Appointment) => {
    const isUpcomingAppointment = isUpcoming(appointment.scheduled_start);
    const rescheduleableStatuses = ['scheduled', 'confirmed'];
    return isUpcomingAppointment && rescheduleableStatuses.includes(appointment.status);
  };

  const filteredAppointments = appointments
    .filter(appointment => {
      // Status filter
      if (filter !== 'all') {
        if (filter === 'upcoming') {
          return isUpcoming(appointment.scheduled_start) && 
                 !['completed', 'cancelled', 'no_show'].includes(appointment.status);
        } else if (filter === 'completed') {
          return appointment.status === 'completed';
        } else if (filter === 'cancelled') {
          return ['cancelled', 'no_show'].includes(appointment.status);
        }
      }

      return true;
    })
    .filter(appointment => {
      // Search filter
      if (!searchTerm) return true;

      const searchLower = searchTerm.toLowerCase();
      
      if (userType === 'patient') {
        const doctor = doctors[appointment.doctor_id];
        return doctor && (
          `${doctor.first_name} ${doctor.last_name}`.toLowerCase().includes(searchLower) ||
          doctor.specialization.toLowerCase().includes(searchLower)
        );
      } else {
        const patient = patients[appointment.patient_id];
        return patient && (
          `${patient.first_name} ${patient.last_name}`.toLowerCase().includes(searchLower) ||
          patient.username.toLowerCase().includes(searchLower)
        );
      }
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'date':
          return new Date(a.scheduled_start).getTime() - new Date(b.scheduled_start).getTime();
        case 'status':
          return a.status.localeCompare(b.status);
        case 'type':
          return a.consultation_type.localeCompare(b.consultation_type);
        default:
          return 0;
      }
    });

  const groupedAppointments = filteredAppointments.reduce((groups, appointment) => {
    const date = appointment.scheduled_start.split('T')[0];
    if (!groups[date]) {
      groups[date] = [];
    }
    groups[date].push(appointment);
    return groups;
  }, {} as Record<string, Appointment[]>);

  return (
    <div className="space-y-6">
      {/* Filters and Search */}
      <Card>
        <CardHeader>
          <CardTitle>Appointments</CardTitle>
          <CardDescription>
            Manage your {userType === 'patient' ? 'medical' : 'patient'} appointments
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4">
            {/* Status Filter */}
            <div className="flex-1">
              <label className="text-sm font-medium mb-2 block">Filter by Status</label>
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value as any)}
                className="w-full px-3 py-2 border border-input rounded-md"
              >
                <option value="all">All Appointments</option>
                <option value="upcoming">Upcoming</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>

            {/* Search */}
            <div className="flex-1">
              <label className="text-sm font-medium mb-2 block">
                Search {userType === 'patient' ? 'Doctors' : 'Patients'}
              </label>
              <Input
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder={`Search by ${userType === 'patient' ? 'doctor name or specialization' : 'patient name'}`}
              />
            </div>

            {/* Sort */}
            <div className="flex-1">
              <label className="text-sm font-medium mb-2 block">Sort by</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="w-full px-3 py-2 border border-input rounded-md"
              >
                <option value="date">Date</option>
                <option value="status">Status</option>
                <option value="type">Type</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Appointments List */}
      {Object.keys(groupedAppointments).length === 0 ? (
        <Card>
          <CardContent className="text-center py-8">
            <p className="text-gray-500">No appointments found matching your criteria.</p>
          </CardContent>
        </Card>
      ) : (
        Object.entries(groupedAppointments).map(([date, dayAppointments]) => (
          <Card key={date}>
            <CardHeader>
              <CardTitle className="text-lg">
                {formatDate(date)}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {dayAppointments.map((appointment) => {
                  const otherPerson = userType === 'patient' 
                    ? doctors[appointment.doctor_id]
                    : patients[appointment.patient_id];

                  return (
                    <div
                      key={appointment.id}
                      className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <span className="font-medium">
                              {formatTime(appointment.scheduled_start)} - {formatTime(appointment.scheduled_end)}
                            </span>
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(appointment.status)}`}>
                              {appointment.status.replace('_', ' ')}
                            </span>
                            <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded-full capitalize">
                              {appointment.consultation_type.replace('_', ' ')}
                            </span>
                          </div>

                          <div className="text-sm text-gray-600 mb-2">
                            {userType === 'patient' && otherPerson ? (
                              <span>
                                Dr. {otherPerson.first_name} {otherPerson.last_name} - {(otherPerson as DoctorProfile).specialization}
                              </span>
                            ) : userType === 'doctor' && otherPerson ? (
                              <span>
                                {otherPerson.first_name} {otherPerson.last_name} (@{(otherPerson as PatientProfile).username})
                              </span>
                            ) : (
                              <span>Loading...</span>
                            )}
                          </div>

                          {appointment.notes && (
                            <div className="text-sm text-gray-600 mb-2">
                              <span className="font-medium">Notes:</span> {appointment.notes}
                            </div>
                          )}

                          <div className="text-xs text-gray-500">
                            {isUpcoming(appointment.scheduled_start) ? (
                              <span>In {getTimeUntilAppointment(appointment.scheduled_start)}</span>
                            ) : (
                              <span>Completed on {formatDateTime(appointment.updated_at)}</span>
                            )}
                          </div>
                        </div>

                        <div className="flex flex-col space-y-2 ml-4">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => onViewDetails(appointment)}
                          >
                            View Details
                          </Button>

                          {canReschedule(appointment) && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => onReschedule(appointment.id)}
                              disabled={loading}
                            >
                              Reschedule
                            </Button>
                          )}

                          {canCancel(appointment) && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => onCancel(appointment.id)}
                              disabled={loading}
                              className="text-red-600 hover:text-red-700 hover:bg-red-50"
                            >
                              Cancel
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        ))
      )}

      {/* Summary Stats */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-blue-600">
                {appointments.filter(apt => isUpcoming(apt.scheduled_start) && 
                  !['completed', 'cancelled', 'no_show'].includes(apt.status)).length}
              </div>
              <div className="text-sm text-gray-600">Upcoming</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">
                {appointments.filter(apt => apt.status === 'completed').length}
              </div>
              <div className="text-sm text-gray-600">Completed</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-red-600">
                {appointments.filter(apt => ['cancelled', 'no_show'].includes(apt.status)).length}
              </div>
              <div className="text-sm text-gray-600">Cancelled</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-600">
                {appointments.length}
              </div>
              <div className="text-sm text-gray-600">Total</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}