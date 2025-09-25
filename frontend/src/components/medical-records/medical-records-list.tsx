"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { MedicalRecord, MedicalRecordVersion } from "@/types";

interface MedicalRecordsListProps {
  records: MedicalRecord[];
  userType: 'patient' | 'doctor';
  canEdit: boolean;
  onViewVersions: (recordId: string) => void;
  onEditRecord: (record: MedicalRecord) => void;
  onCreateRecord: () => void;
  onDeleteRecord: (recordId: string) => Promise<void>;
  loading?: boolean;
}

export function MedicalRecordsList({
  records,
  userType,
  canEdit,
  onViewVersions,
  onEditRecord,
  onCreateRecord,
  onDeleteRecord,
  loading = false
}: MedicalRecordsListProps) {
  const [filter, setFilter] = useState<'all' | 'medication' | 'allergy' | 'procedure' | 'condition' | 'vaccine'>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'date' | 'type' | 'title'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const getRecordTypeColor = (type: string) => {
    switch (type) {
      case 'medication':
        return 'bg-blue-100 text-blue-800';
      case 'allergy':
        return 'bg-red-100 text-red-800';
      case 'procedure':
        return 'bg-green-100 text-green-800';
      case 'condition':
        return 'bg-orange-100 text-orange-800';
      case 'vaccine':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getRecordTypeIcon = (type: string) => {
    switch (type) {
      case 'medication':
        return '💊';
      case 'allergy':
        return '⚠️';
      case 'procedure':
        return '🏥';
      case 'condition':
        return '🩺';
      case 'vaccine':
        return '💉';
      default:
        return '📋';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getRetentionStatus = (record: MedicalRecord) => {
    const createdDate = new Date(record.created_at);
    const retentionEndDate = new Date(createdDate.getTime() + (record.retention_weeks * 7 * 24 * 60 * 60 * 1000));
    const now = new Date();
    const weeksLeft = Math.ceil((retentionEndDate.getTime() - now.getTime()) / (7 * 24 * 60 * 60 * 1000));

    if (weeksLeft <= 0) {
      return { status: 'expired', text: 'Retention expired', color: 'text-red-600' };
    } else if (weeksLeft <= 4) {
      return { status: 'expiring', text: `${weeksLeft} weeks left`, color: 'text-orange-600' };
    } else {
      return { status: 'active', text: `${weeksLeft} weeks left`, color: 'text-green-600' };
    }
  };

  const filteredRecords = records
    .filter(record => {
      // Type filter  
      if (filter !== 'all' && record.record_type !== filter) {
        return false;
      }

      // Search filter
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase();
        return (
          record.title.toLowerCase().includes(searchLower) ||
          record.description?.toLowerCase().includes(searchLower) ||
          record.record_type.toLowerCase().includes(searchLower)
        );
      }

      return true;
    })
    .sort((a, b) => {
      let comparison = 0;

      switch (sortBy) {
        case 'date':
          comparison = new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime();
          break;
        case 'type':
          comparison = a.record_type.localeCompare(b.record_type);
          break;
        case 'title':
          comparison = a.title.localeCompare(b.title);
          break;
      }

      return sortOrder === 'asc' ? comparison : -comparison;
    });

  const recordsByType = records.reduce((acc, record) => {
    acc[record.record_type] = (acc[record.record_type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Medical Records</CardTitle>
              <CardDescription>
                Your health information and medical history
              </CardDescription>
            </div>
            {canEdit && (
              <Button onClick={onCreateRecord} disabled={loading}>
                Add Record
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {/* Summary Stats */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            {[
              { type: 'medication', label: 'Medications', icon: '💊' },
              { type: 'allergy', label: 'Allergies', icon: '⚠️' },
              { type: 'procedure', label: 'Procedures', icon: '🏥' },
              { type: 'condition', label: 'Conditions', icon: '🩺' },
              { type: 'vaccine', label: 'Vaccines', icon: '💉' }
            ].map(({ type, label, icon }) => (
              <div key={type} className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-2xl mb-1">{icon}</div>
                <div className="text-lg font-semibold">
                  {recordsByType[type] || 0}
                </div>
                <div className="text-sm text-gray-600">{label}</div>
              </div>
            ))}
          </div>

          {/* Filters and Search */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Filter by Type</label>
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value as any)}
                className="w-full px-3 py-2 border border-input rounded-md"
              >
                <option value="all">All Types</option>
                <option value="medication">Medications</option>
                <option value="allergy">Allergies</option>
                <option value="procedure">Procedures</option>
                <option value="condition">Conditions</option>
                <option value="vaccine">Vaccines</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Search</label>
              <Input
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search records..."
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Sort by</label>
              <div className="flex space-x-2">
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  className="flex-1 px-3 py-2 border border-input rounded-md"
                >
                  <option value="date">Date</option>
                  <option value="type">Type</option>
                  <option value="title">Title</option>
                </select>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                >
                  {sortOrder === 'asc' ? '↑' : '↓'}
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Records List */}
      {filteredRecords.length === 0 ? (
        <Card>
          <CardContent className="text-center py-8">
            <p className="text-gray-500 mb-4">
              {records.length === 0 
                ? 'No medical records found' 
                : 'No records match your search criteria'
              }
            </p>
            {canEdit && records.length === 0 && (
              <Button onClick={onCreateRecord}>
                Add Your First Record
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredRecords.map((record) => {
            const retention = getRetentionStatus(record);
            
            return (
              <Card key={record.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <span className="text-xl">
                          {getRecordTypeIcon(record.record_type)}
                        </span>
                        <h3 className="font-semibold text-lg">{record.title}</h3>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRecordTypeColor(record.record_type)}`}>
                          {record.record_type}
                        </span>
                        <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded-full">
                          v{record.current_version}
                        </span>
                      </div>

                      {record.description && (
                        <p className="text-gray-600 mb-3">
                          {record.description}
                        </p>
                      )}

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-500">
                        <div>
                          <span className="font-medium">Created:</span>{' '}
                          {formatDate(record.created_at)}
                        </div>
                        <div>
                          <span className="font-medium">Last Updated:</span>{' '}
                          {formatDateTime(record.updated_at)}
                        </div>
                        <div>
                          <span className="font-medium">Retention:</span>{' '}
                          <span className={retention.color}>
                            {retention.text}
                          </span>
                        </div>
                      </div>

                      {!record.is_active && (
                        <div className="mt-2">
                          <span className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full">
                            Inactive
                          </span>
                        </div>
                      )}
                    </div>

                    <div className="flex flex-col space-y-2 ml-4">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onViewVersions(record.id)}
                      >
                        View History
                      </Button>

                      {canEdit && (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => onEditRecord(record)}
                            disabled={loading}
                          >
                            Edit
                          </Button>

                          {userType === 'patient' && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => onDeleteRecord(record.id)}
                              disabled={loading}
                              className="text-red-600 hover:text-red-700 hover:bg-red-50"
                            >
                              Delete
                            </Button>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* HIPAA Notice */}
      <Card>
        <CardContent className="pt-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex">
              <div className="text-blue-600 mr-3">🔒</div>
              <div className="text-sm text-blue-800">
                <p className="font-medium mb-1">Medical Record Privacy</p>
                <p>
                  Your medical records are protected under HIPAA regulations. 
                  All changes are tracked with timestamps and user attribution. 
                  Records are automatically retained according to your configured retention policy.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}