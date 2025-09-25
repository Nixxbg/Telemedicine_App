"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { DoctorProfile } from "@/types";

interface TimeSlot {
  start: string;
  end: string;
  available: boolean;
}

interface DaySchedule {
  date: string;
  slots: TimeSlot[];
}

interface AppointmentBookingData {
  doctor_id: string;
  scheduled_start: string;
  scheduled_end: string;
  consultation_type: 'initial' | 'follow_up' | 'urgent';
  notes?: string;
}

interface AppointmentBookingProps {
  doctors: DoctorProfile[];
  availability: Record<string, DaySchedule>;
  onBook: (appointmentData: AppointmentBookingData) => Promise<void>;
  loading?: boolean;
}

export function AppointmentBooking({
  doctors,
  availability,
  onBook,
  loading = false
}: AppointmentBookingProps) {
  const [selectedDoctor, setSelectedDoctor] = useState<DoctorProfile | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [selectedSlot, setSelectedSlot] = useState<TimeSlot | null>(null);
  const [consultationType, setConsultationType] = useState<'initial' | 'follow_up' | 'urgent'>('initial');
  const [notes, setNotes] = useState('');
  const [step, setStep] = useState<'doctor' | 'date' | 'time' | 'details' | 'confirmation'>('doctor');

  const getNextSevenDays = () => {
    const days = [];
    for (let i = 0; i < 7; i++) {
      const date = new Date();
      date.setDate(date.getDate() + i);
      days.push(date.toISOString().split('T')[0]);
    }
    return days;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const formatTime = (timeString: string) => {
    return new Date(`2000-01-01T${timeString}`).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getAvailableSlots = (doctorId: string, date: string): TimeSlot[] => {
    const daySchedule = availability[`${doctorId}-${date}`];
    return daySchedule?.slots.filter(slot => slot.available) || [];
  };

  const handleBookAppointment = async () => {
    if (!selectedDoctor || !selectedSlot || !selectedDate) return;

    const appointmentData: AppointmentBookingData = {
      doctor_id: selectedDoctor.user_id,
      scheduled_start: `${selectedDate}T${selectedSlot.start}`,
      scheduled_end: `${selectedDate}T${selectedSlot.end}`,
      consultation_type: consultationType,
      notes: notes.trim() || undefined
    };

    await onBook(appointmentData);
  };

  const resetBooking = () => {
    setSelectedDoctor(null);
    setSelectedDate('');
    setSelectedSlot(null);
    setConsultationType('initial');
    setNotes('');
    setStep('doctor');
  };

  const canProceedToNextStep = () => {
    switch (step) {
      case 'doctor':
        return selectedDoctor !== null;
      case 'date':
        return selectedDate !== '';
      case 'time':
        return selectedSlot !== null;
      case 'details':
        return true;
      default:
        return false;
    }
  };

  const nextStep = () => {
    const steps: Array<'doctor' | 'date' | 'time' | 'details' | 'confirmation'> = 
      ['doctor', 'date', 'time', 'details', 'confirmation'];
    const currentIndex = steps.indexOf(step);
    if (currentIndex < steps.length - 1) {
      setStep(steps[currentIndex + 1]);
    }
  };

  const previousStep = () => {
    const steps: Array<'doctor' | 'date' | 'time' | 'details' | 'confirmation'> = 
      ['doctor', 'date', 'time', 'details', 'confirmation'];
    const currentIndex = steps.indexOf(step);
    if (currentIndex > 0) {
      setStep(steps[currentIndex - 1]);
    }
  };

  const getStepTitle = () => {
    switch (step) {
      case 'doctor': return 'Select Doctor';
      case 'date': return 'Choose Date';
      case 'time': return 'Select Time';
      case 'details': return 'Appointment Details';
      case 'confirmation': return 'Confirm Booking';
      default: return 'Book Appointment';
    }
  };

  const renderStepContent = () => {
    switch (step) {
      case 'doctor':
        return (
          <div className="space-y-4">
            <p className="text-gray-600">Choose a healthcare provider for your appointment</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {doctors.filter(doctor => doctor.is_available).map((doctor) => (
                <Card 
                  key={doctor.user_id}
                  className={`cursor-pointer transition-colors ${
                    selectedDoctor?.user_id === doctor.user_id 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'hover:border-gray-300'
                  }`}
                  onClick={() => setSelectedDoctor(doctor)}
                >
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">
                      Dr. {doctor.first_name} {doctor.last_name}
                    </CardTitle>
                    <CardDescription>
                      {doctor.specialization}
                      {doctor.years_experience && ` • ${doctor.years_experience} years experience`}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">
                        License: {doctor.license_number}
                      </span>
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                        Available
                      </span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
            {doctors.filter(doctor => doctor.is_available).length === 0 && (
              <p className="text-center text-gray-500 py-8">
                No doctors are currently available for appointments
              </p>
            )}
          </div>
        );

      case 'date':
        return (
          <div className="space-y-4">
            <p className="text-gray-600">
              Select a date for your appointment with Dr. {selectedDoctor?.last_name}
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {getNextSevenDays().map((date) => {
                const availableSlots = getAvailableSlots(selectedDoctor!.user_id, date);
                const hasSlots = availableSlots.length > 0;
                
                return (
                  <Card
                    key={date}
                    className={`cursor-pointer transition-colors ${
                      !hasSlots 
                        ? 'opacity-50 cursor-not-allowed' 
                        : selectedDate === date 
                        ? 'border-blue-500 bg-blue-50' 
                        : 'hover:border-gray-300'
                    }`}
                    onClick={() => hasSlots && setSelectedDate(date)}
                  >
                    <CardContent className="p-4 text-center">
                      <div className="font-medium">
                        {formatDate(date)}
                      </div>
                      <div className="text-sm text-gray-600 mt-2">
                        {hasSlots ? `${availableSlots.length} slots available` : 'No slots available'}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        );

      case 'time':
        const availableSlots = getAvailableSlots(selectedDoctor!.user_id, selectedDate);
        return (
          <div className="space-y-4">
            <p className="text-gray-600">
              Choose a time slot for {formatDate(selectedDate)}
            </p>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {availableSlots.map((slot, index) => (
                <Button
                  key={index}
                  variant={selectedSlot === slot ? "default" : "outline"}
                  onClick={() => setSelectedSlot(slot)}
                  className="h-auto py-3"
                >
                  <div className="text-center">
                    <div className="font-medium">
                      {formatTime(slot.start)}
                    </div>
                    <div className="text-xs opacity-75">
                      {formatTime(slot.end)}
                    </div>
                  </div>
                </Button>
              ))}
            </div>
            {availableSlots.length === 0 && (
              <p className="text-center text-gray-500 py-8">
                No time slots available for this date
              </p>
            )}
          </div>
        );

      case 'details':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="font-medium mb-4">Appointment Type</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  { value: 'initial', label: 'Initial Consultation', description: 'First-time visit or new concern' },
                  { value: 'follow_up', label: 'Follow-up', description: 'Follow-up on previous treatment' },
                  { value: 'urgent', label: 'Urgent Care', description: 'Urgent medical concern' }
                ].map((type) => (
                  <Card
                    key={type.value}
                    className={`cursor-pointer transition-colors ${
                      consultationType === type.value 
                        ? 'border-blue-500 bg-blue-50' 
                        : 'hover:border-gray-300'
                    }`}
                    onClick={() => setConsultationType(type.value as any)}
                  >
                    <CardContent className="p-4">
                      <div className="font-medium">{type.label}</div>
                      <div className="text-sm text-gray-600 mt-1">
                        {type.description}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">
                Additional Notes (Optional)
              </label>
              <Textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Describe your symptoms, concerns, or any information that might help your doctor prepare for the appointment..."
                rows={4}
                disabled={loading}
              />
            </div>
          </div>
        );

      case 'confirmation':
        return (
          <div className="space-y-6">
            <div className="bg-gray-50 rounded-lg p-6">
              <h3 className="font-medium mb-4">Appointment Summary</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Doctor:</span>
                  <span className="font-medium">
                    Dr. {selectedDoctor?.first_name} {selectedDoctor?.last_name}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Specialization:</span>
                  <span>{selectedDoctor?.specialization}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Date:</span>
                  <span>{formatDate(selectedDate)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Time:</span>
                  <span>
                    {selectedSlot && `${formatTime(selectedSlot.start)} - ${formatTime(selectedSlot.end)}`}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Type:</span>
                  <span className="capitalize">{consultationType.replace('_', ' ')}</span>
                </div>
                {notes && (
                  <div>
                    <span className="text-gray-600">Notes:</span>
                    <p className="mt-1 text-sm bg-white p-3 rounded border">
                      {notes}
                    </p>
                  </div>
                )}
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex">
                <div className="text-blue-600 mr-3">ℹ️</div>
                <div className="text-sm text-blue-800">
                  <p className="font-medium mb-1">Before your appointment:</p>
                  <ul className="list-disc list-inside space-y-1">
                    <li>You&apos;ll receive a confirmation email with appointment details</li>
                    <li>Please arrive 10 minutes early for check-in</li>
                    <li>Bring your insurance card and a valid ID</li>
                    <li>Complete any required pre-appointment forms</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle>Book an Appointment</CardTitle>
        <CardDescription>
          {getStepTitle()} - Step {['doctor', 'date', 'time', 'details', 'confirmation'].indexOf(step) + 1} of 5
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="mb-8">
          {renderStepContent()}
        </div>

        <div className="flex justify-between">
          <Button
            variant="outline"
            onClick={step === 'doctor' ? resetBooking : previousStep}
            disabled={loading}
          >
            {step === 'doctor' ? 'Cancel' : 'Previous'}
          </Button>

          <div className="space-x-2">
            {step !== 'confirmation' ? (
              <Button
                onClick={nextStep}
                disabled={!canProceedToNextStep() || loading}
              >
                Next
              </Button>
            ) : (
              <Button
                onClick={handleBookAppointment}
                disabled={loading}
              >
                {loading ? 'Booking...' : 'Confirm Appointment'}
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}