"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { DoctorProfile, Appointment, Message } from "@/types";

interface DoctorDashboardProps {
  doctor: DoctorProfile;
  todayAppointments?: Appointment[];
  upcomingAppointments?: Appointment[];
  recentMessages?: Message[];
  onViewSchedule: () => void;
  onViewPatients: () => void;
  onViewMessages: () => void;
  onToggleAvailability: () => void;
}

export function DoctorDashboard({
  doctor,
  todayAppointments = [],
  upcomingAppointments = [],
  recentMessages = [],
  onViewSchedule,
  onViewPatients,
  onViewMessages,
  onToggleAvailability
}: DoctorDashboardProps) {
  const getAppointmentStatusColor = (status: string) => {
    switch (status) {
      case 'scheduled':
        return 'text-blue-600 bg-blue-50';
      case 'confirmed':
        return 'text-green-600 bg-green-50';
      case 'in_progress':
        return 'text-orange-600 bg-orange-50';
      case 'completed':
        return 'text-gray-600 bg-gray-50';
      case 'cancelled':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getTimeUntilAppointment = (scheduledStart: string) => {
    const now = new Date();
    const appointmentTime = new Date(scheduledStart);
    const diffMs = appointmentTime.getTime() - now.getTime();
    const diffMinutes = Math.round(diffMs / (1000 * 60));
    
    if (diffMinutes < 0) return 'Started';
    if (diffMinutes < 60) return `${diffMinutes}m`;
    const hours = Math.floor(diffMinutes / 60);
    const minutes = diffMinutes % 60;
    return `${hours}h ${minutes}m`;
  };

  const unreadMessagesCount = recentMessages.filter(msg => !msg.is_read).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-600 to-blue-600 text-white p-6 rounded-lg">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold mb-2">
              Welcome, Dr. {doctor.last_name}
            </h1>
            <p className="text-green-100">
              {doctor.specialization} • {doctor.years_experience} years experience
            </p>
          </div>
          <div className="text-right">
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-sm">Status:</span>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                doctor.is_available 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {doctor.is_available ? 'Available' : 'Unavailable'}
              </span>
            </div>
            <Button
              onClick={onToggleAvailability}
              variant="outline"
              size="sm"
              className="bg-white/10 border-white/20 text-white hover:bg-white/20"
            >
              {doctor.is_available ? 'Set Unavailable' : 'Set Available'}
            </Button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Quick Stats */}
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Today&apos;s Appointments</CardDescription>
            <CardTitle className="text-3xl">
              {todayAppointments.length}
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <p className="text-sm text-gray-600">
              {todayAppointments.filter(apt => apt.status === 'completed').length} completed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Upcoming This Week</CardDescription>
            <CardTitle className="text-3xl">
              {upcomingAppointments.length}
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <p className="text-sm text-gray-600">
              {upcomingAppointments.filter(apt => apt.status === 'confirmed').length} confirmed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Unread Messages</CardDescription>
            <CardTitle className="text-3xl">
              {unreadMessagesCount}
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <Button
              variant="ghost"
              size="sm"
              onClick={onViewMessages}
              className="text-blue-600 hover:text-blue-800 p-0 h-auto"
            >
              View Messages
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>License Status</CardDescription>
            <CardTitle className="text-sm">
              {doctor.license_number}
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <span className="inline-block px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
              Active
            </span>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Today's Schedule */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Today&apos;s Schedule</CardTitle>
                <CardDescription>
                  {formatDate(new Date().toISOString())}
                </CardDescription>
              </div>
              <Button onClick={onViewSchedule} variant="outline" size="sm">
                Full Schedule
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {todayAppointments.length === 0 ? (
              <p className="text-gray-500 text-center py-8">
                No appointments scheduled for today
              </p>
            ) : (
              <div className="space-y-3">
                {todayAppointments.slice(0, 5).map((appointment) => {
                  const timeUntil = getTimeUntilAppointment(appointment.scheduled_start);
                  const isNext = timeUntil !== 'Started' && 
                    todayAppointments.findIndex(apt => 
                      getTimeUntilAppointment(apt.scheduled_start) !== 'Started'
                    ) === todayAppointments.indexOf(appointment);

                  return (
                    <div 
                      key={appointment.id} 
                      className={`p-4 rounded-lg border ${
                        isNext ? 'border-blue-200 bg-blue-50' : 'border-gray-200 bg-gray-50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="font-medium">
                              {formatTime(appointment.scheduled_start)} - {formatTime(appointment.scheduled_end)}
                            </span>
                            {isNext && (
                              <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                                Next
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-600 capitalize">
                            {appointment.consultation_type} consultation
                          </p>
                          {appointment.notes && (
                            <p className="text-sm text-gray-500 mt-1">
                              {appointment.notes}
                            </p>
                          )}
                        </div>
                        <div className="text-right">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getAppointmentStatusColor(appointment.status)}`}>
                            {appointment.status.replace('_', ' ')}
                          </span>
                          <p className="text-xs text-gray-500 mt-1">
                            {timeUntil === 'Started' ? 'Now' : `in ${timeUntil}`}
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                })}
                {todayAppointments.length > 5 && (
                  <Button variant="ghost" size="sm" className="w-full" onClick={onViewSchedule}>
                    View {todayAppointments.length - 5} more appointments
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Messages */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Recent Messages</CardTitle>
                <CardDescription>
                  Patient communications
                </CardDescription>
              </div>
              <Button onClick={onViewMessages} variant="outline" size="sm">
                All Messages
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {recentMessages.length === 0 ? (
              <p className="text-gray-500 text-center py-8">
                No recent messages
              </p>
            ) : (
              <div className="space-y-4">
                {recentMessages.slice(0, 4).map((message) => (
                  <div 
                    key={message.id} 
                    className={`p-3 rounded-lg ${
                      !message.is_read ? 'bg-blue-50 border-l-4 border-blue-400' : 'bg-gray-50'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <span className="font-medium text-sm">
                            Patient ID: {message.sender_id.slice(-8)}
                          </span>
                          {!message.is_read && (
                            <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                          )}
                        </div>
                        <p className="text-sm text-gray-700 line-clamp-2">
                          {message.content}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          {formatDate(message.created_at)}
                        </p>
                      </div>
                      {message.message_type !== 'text' && (
                        <span className="px-2 py-1 bg-gray-200 text-gray-700 text-xs rounded-full">
                          {message.message_type}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
                {recentMessages.length > 4 && (
                  <Button variant="ghost" size="sm" className="w-full" onClick={onViewMessages}>
                    View {recentMessages.length - 4} more messages
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>
            Common tasks and tools
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button onClick={onViewSchedule} variant="outline" className="justify-start">
              📅 Manage Schedule
            </Button>
            <Button onClick={onViewPatients} variant="outline" className="justify-start">
              👥 View Patients
            </Button>
            <Button onClick={onViewMessages} variant="outline" className="justify-start">
              💬 Messages {unreadMessagesCount > 0 && `(${unreadMessagesCount})`}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}