"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

interface TimeSlot {
  start: string;
  end: string;
}

interface DayAvailability {
  day: string;
  available: boolean;
  slots: TimeSlot[];
}

interface WeeklyAvailability {
  monday: DayAvailability;
  tuesday: DayAvailability;
  wednesday: DayAvailability;
  thursday: DayAvailability;
  friday: DayAvailability;
  saturday: DayAvailability;
  sunday: DayAvailability;
}

interface BlockedDate {
  date: string;
  reason: string;
  allDay: boolean;
  startTime?: string;
  endTime?: string;
}

interface AvailabilityManagerProps {
  doctorId: string;
  currentAvailability?: WeeklyAvailability;
  blockedDates?: BlockedDate[];
  onSaveAvailability: (availability: WeeklyAvailability) => Promise<void>;
  onBlockDate: (blockedDate: BlockedDate) => Promise<void>;
  onUnblockDate: (date: string) => Promise<void>;
  loading?: boolean;
}

export function AvailabilityManager({
  doctorId,
  currentAvailability,
  blockedDates = [],
  onSaveAvailability,
  onBlockDate,
  onUnblockDate,
  loading = false
}: AvailabilityManagerProps) {
  const defaultDayAvailability: DayAvailability = {
    day: '',
    available: false,
    slots: []
  };

  const [availability, setAvailability] = useState<WeeklyAvailability>(
    currentAvailability || {
      monday: { ...defaultDayAvailability, day: 'monday' },
      tuesday: { ...defaultDayAvailability, day: 'tuesday' },
      wednesday: { ...defaultDayAvailability, day: 'wednesday' },
      thursday: { ...defaultDayAvailability, day: 'thursday' },
      friday: { ...defaultDayAvailability, day: 'friday' },
      saturday: { ...defaultDayAvailability, day: 'saturday' },
      sunday: { ...defaultDayAvailability, day: 'sunday' }
    }
  );

  const [newBlockedDate, setNewBlockedDate] = useState<Partial<BlockedDate>>({
    date: '',
    reason: '',
    allDay: true
  });

  const daysOfWeek = [
    { key: 'monday', label: 'Monday' },
    { key: 'tuesday', label: 'Tuesday' },
    { key: 'wednesday', label: 'Wednesday' },
    { key: 'thursday', label: 'Thursday' },
    { key: 'friday', label: 'Friday' },
    { key: 'saturday', label: 'Saturday' },
    { key: 'sunday', label: 'Sunday' }
  ];

  const updateDayAvailability = (day: keyof WeeklyAvailability, field: keyof DayAvailability, value: any) => {
    setAvailability(prev => ({
      ...prev,
      [day]: {
        ...prev[day],
        [field]: value
      }
    }));
  };

  const addTimeSlot = (day: keyof WeeklyAvailability) => {
    const newSlot: TimeSlot = { start: '09:00', end: '10:00' };
    setAvailability(prev => ({
      ...prev,
      [day]: {
        ...prev[day],
        slots: [...prev[day].slots, newSlot]
      }
    }));
  };

  const removeTimeSlot = (day: keyof WeeklyAvailability, slotIndex: number) => {
    setAvailability(prev => ({
      ...prev,
      [day]: {
        ...prev[day],
        slots: prev[day].slots.filter((_, index) => index !== slotIndex)
      }
    }));
  };

  const updateTimeSlot = (day: keyof WeeklyAvailability, slotIndex: number, field: keyof TimeSlot, value: string) => {
    setAvailability(prev => ({
      ...prev,
      [day]: {
        ...prev[day],
        slots: prev[day].slots.map((slot, index) => 
          index === slotIndex ? { ...slot, [field]: value } : slot
        )
      }
    }));
  };

  const handleSaveAvailability = async () => {
    await onSaveAvailability(availability);
  };

  const handleBlockDate = async () => {
    if (newBlockedDate.date && newBlockedDate.reason) {
      const blockedDate: BlockedDate = {
        date: newBlockedDate.date,
        reason: newBlockedDate.reason,
        allDay: newBlockedDate.allDay || true,
        startTime: newBlockedDate.startTime,
        endTime: newBlockedDate.endTime
      };
      
      await onBlockDate(blockedDate);
      setNewBlockedDate({ date: '', reason: '', allDay: true });
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const isTimeSlotValid = (start: string, end: string) => {
    return start < end;
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Weekly Availability Schedule</CardTitle>
          <CardDescription>
            Set your regular weekly schedule for patient appointments
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {daysOfWeek.map(({ key, label }) => {
              const dayAvailability = availability[key as keyof WeeklyAvailability];
              
              return (
                <div key={key} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-medium">{label}</h3>
                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id={`${key}-available`}
                        checked={dayAvailability.available}
                        onChange={(e) => updateDayAvailability(key as keyof WeeklyAvailability, 'available', e.target.checked)}
                        disabled={loading}
                      />
                      <label htmlFor={`${key}-available`} className="text-sm">
                        Available
                      </label>
                    </div>
                  </div>

                  {dayAvailability.available && (
                    <div className="space-y-3">
                      <div className="text-sm text-gray-600 mb-2">
                        Time Slots:
                      </div>
                      
                      {dayAvailability.slots.map((slot, slotIndex) => (
                        <div key={slotIndex} className="flex items-center space-x-3">
                          <Input
                            type="time"
                            value={slot.start}
                            onChange={(e) => updateTimeSlot(key as keyof WeeklyAvailability, slotIndex, 'start', e.target.value)}
                            disabled={loading}
                            className="w-32"
                          />
                          <span className="text-gray-500">to</span>
                          <Input
                            type="time"
                            value={slot.end}
                            onChange={(e) => updateTimeSlot(key as keyof WeeklyAvailability, slotIndex, 'end', e.target.value)}
                            disabled={loading}
                            className="w-32"
                          />
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => removeTimeSlot(key as keyof WeeklyAvailability, slotIndex)}
                            disabled={loading}
                          >
                            Remove
                          </Button>
                          {!isTimeSlotValid(slot.start, slot.end) && (
                            <span className="text-sm text-red-600">
                              Invalid time range
                            </span>
                          )}
                        </div>
                      ))}

                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => addTimeSlot(key as keyof WeeklyAvailability)}
                        disabled={loading}
                      >
                        Add Time Slot
                      </Button>
                    </div>
                  )}
                </div>
              );
            })}

            <div className="flex justify-end">
              <Button onClick={handleSaveAvailability} disabled={loading}>
                {loading ? 'Saving...' : 'Save Availability'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Block Specific Dates</CardTitle>
          <CardDescription>
            Block dates when you won&apos;t be available for appointments
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Add New Blocked Date */}
            <div className="border rounded-lg p-4">
              <h3 className="font-medium mb-4">Block New Date</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">Date</label>
                  <Input
                    type="date"
                    value={newBlockedDate.date}
                    onChange={(e) => setNewBlockedDate(prev => ({ ...prev, date: e.target.value }))}
                    disabled={loading}
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">Reason</label>
                  <Input
                    value={newBlockedDate.reason}
                    onChange={(e) => setNewBlockedDate(prev => ({ ...prev, reason: e.target.value }))}
                    placeholder="Vacation, Conference, Personal, etc."
                    disabled={loading}
                  />
                </div>
              </div>

              <div className="mt-4">
                <div className="flex items-center space-x-3 mb-3">
                  <input
                    type="checkbox"
                    id="all-day"
                    checked={newBlockedDate.allDay}
                    onChange={(e) => setNewBlockedDate(prev => ({ ...prev, allDay: e.target.checked }))}
                    disabled={loading}
                  />
                  <label htmlFor="all-day" className="text-sm">
                    All day
                  </label>
                </div>

                {!newBlockedDate.allDay && (
                  <div className="flex items-center space-x-3">
                    <Input
                      type="time"
                      value={newBlockedDate.startTime || ''}
                      onChange={(e) => setNewBlockedDate(prev => ({ ...prev, startTime: e.target.value }))}
                      disabled={loading}
                      className="w-32"
                    />
                    <span className="text-gray-500">to</span>
                    <Input
                      type="time"
                      value={newBlockedDate.endTime || ''}
                      onChange={(e) => setNewBlockedDate(prev => ({ ...prev, endTime: e.target.value }))}
                      disabled={loading}
                      className="w-32"
                    />
                  </div>
                )}
              </div>

              <div className="mt-4">
                <Button
                  onClick={handleBlockDate}
                  disabled={loading || !newBlockedDate.date || !newBlockedDate.reason}
                >
                  {loading ? 'Blocking...' : 'Block Date'}
                </Button>
              </div>
            </div>

            {/* Existing Blocked Dates */}
            <div>
              <h3 className="font-medium mb-4">Currently Blocked Dates</h3>
              {blockedDates.length === 0 ? (
                <p className="text-gray-500 text-center py-4">
                  No blocked dates
                </p>
              ) : (
                <div className="space-y-3">
                  {blockedDates.map((blockedDate, index) => (
                    <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <p className="font-medium">
                          {formatDate(blockedDate.date)}
                        </p>
                        <p className="text-sm text-gray-600">
                          {blockedDate.reason}
                        </p>
                        {!blockedDate.allDay && (
                          <p className="text-sm text-gray-500">
                            {blockedDate.startTime} - {blockedDate.endTime}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center space-x-2">
                        {blockedDate.allDay ? (
                          <span className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full">
                            All Day
                          </span>
                        ) : (
                          <span className="px-2 py-1 bg-orange-100 text-orange-800 text-xs rounded-full">
                            Partial
                          </span>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onUnblockDate(blockedDate.date)}
                          disabled={loading}
                        >
                          Unblock
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Availability Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Availability Summary</CardTitle>
          <CardDescription>
            Overview of your weekly schedule
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {daysOfWeek.map(({ key, label }) => {
              const dayAvailability = availability[key as keyof WeeklyAvailability];
              
              return (
                <div key={key} className="p-3 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">{label}</span>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      dayAvailability.available 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {dayAvailability.available ? 'Available' : 'Unavailable'}
                    </span>
                  </div>
                  {dayAvailability.available && dayAvailability.slots.length > 0 && (
                    <div className="space-y-1">
                      {dayAvailability.slots.map((slot, index) => (
                        <div key={index} className="text-sm text-gray-600">
                          {slot.start} - {slot.end}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}