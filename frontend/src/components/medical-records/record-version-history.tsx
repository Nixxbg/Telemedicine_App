"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { MedicalRecord, MedicalRecordVersion } from "@/types";

interface RecordVersionHistoryProps {
  record: MedicalRecord;
  versions: MedicalRecordVersion[];
  currentUserId: string;
  onRevertToVersion?: (versionId: string) => Promise<void>;
  onClose: () => void;
  canRevert?: boolean;
  loading?: boolean;
}

export function RecordVersionHistory({
  record,
  versions,
  currentUserId,
  onRevertToVersion,
  onClose,
  canRevert = false,
  loading = false
}: RecordVersionHistoryProps) {
  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null);
  const [showDiff, setShowDiff] = useState(false);

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getUserType = (createdBy: string) => {
    // In a real implementation, you would have user data to determine this
    // For now, we'll make a simple assumption based on current user
    return createdBy === currentUserId ? 'You' : 'Healthcare Provider';
  };

  const getVersionChangeIcon = (versionNumber: number) => {
    if (versionNumber === 1) return '🆕'; // New record
    return '✏️'; // Edit
  };

  const getDataFieldValue = (data: Record<string, any>, field: string) => {
    const value = data[field];
    if (value === null || value === undefined) return 'Not specified';
    if (Array.isArray(value)) return value.join(', ');
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
  };

  const getCommonDataFields = () => {
    const allFields = new Set<string>();
    versions.forEach(version => {
      Object.keys(version.data).forEach(field => allFields.add(field));
    });
    return Array.from(allFields).sort();
  };

  const getDifferences = (version1: MedicalRecordVersion, version2: MedicalRecordVersion) => {
    const fields = getCommonDataFields();
    const differences: Array<{
      field: string;
      oldValue: string;
      newValue: string;
      changed: boolean;
    }> = [];

    fields.forEach(field => {
      const oldValue = getDataFieldValue(version1.data, field);
      const newValue = getDataFieldValue(version2.data, field);
      differences.push({
        field,
        oldValue,
        newValue,
        changed: oldValue !== newValue
      });
    });

    return differences;
  };

  const selectedVersion = selectedVersionId 
    ? versions.find(v => v.id === selectedVersionId)
    : null;

  const currentVersion = versions.find(v => v.version_number === record.current_version);

  const sortedVersions = [...versions].sort((a, b) => b.version_number - a.version_number);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Version History</CardTitle>
              <CardDescription>
                {record.title} - {versions.length} version{versions.length !== 1 ? 's' : ''}
              </CardDescription>
            </div>
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          </div>
        </CardHeader>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Version List */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">All Versions</CardTitle>
            <CardDescription>
              Click on a version to view details
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {sortedVersions.map((version) => {
                const isCurrentVersion = version.version_number === record.current_version;
                const isSelected = selectedVersionId === version.id;
                
                return (
                  <div
                    key={version.id}
                    onClick={() => setSelectedVersionId(version.id)}
                    className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                      isSelected 
                        ? 'border-blue-500 bg-blue-50' 
                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-3">
                        <span className="text-lg">
                          {getVersionChangeIcon(version.version_number)}
                        </span>
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="font-medium">
                              Version {version.version_number}
                            </span>
                            {isCurrentVersion && (
                              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                                Current
                              </span>
                            )}
                          </div>
                          <div className="text-sm text-gray-600">
                            {formatDateTime(version.created_at)}
                          </div>
                          <div className="text-sm text-gray-500">
                            by {getUserType(version.created_by)}
                          </div>
                        </div>
                      </div>

                      {canRevert && !isCurrentVersion && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            onRevertToVersion?.(version.id);
                          }}
                          disabled={loading}
                        >
                          Revert
                        </Button>
                      )}
                    </div>

                    {version.change_summary && (
                      <div className="mt-2 p-2 bg-gray-100 rounded text-sm">
                        <span className="font-medium">Summary:</span> {version.change_summary}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Version Details */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg">
                  {selectedVersion ? `Version ${selectedVersion.version_number} Details` : 'Select a Version'}
                </CardTitle>
                <CardDescription>
                  {selectedVersion && formatDateTime(selectedVersion.created_at)}
                </CardDescription>
              </div>
              {selectedVersion && versions.length > 1 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowDiff(!showDiff)}
                >
                  {showDiff ? 'Hide' : 'Show'} Changes
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {!selectedVersion ? (
              <div className="text-center py-8 text-gray-500">
                Select a version from the list to view its details
              </div>
            ) : (
              <div className="space-y-4">
                {/* Version metadata */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium">Version:</span> {selectedVersion.version_number}
                    </div>
                    <div>
                      <span className="font-medium">Created:</span> {formatDateTime(selectedVersion.created_at)}
                    </div>
                    <div>
                      <span className="font-medium">Created by:</span> {getUserType(selectedVersion.created_by)}
                    </div>
                    <div>
                      <span className="font-medium">Record ID:</span> {selectedVersion.record_id.slice(-8)}
                    </div>
                  </div>
                  
                  {selectedVersion.change_summary && (
                    <div className="mt-3">
                      <span className="font-medium">Change Summary:</span>
                      <p className="mt-1">{selectedVersion.change_summary}</p>
                    </div>
                  )}
                </div>

                {/* Version data */}
                {showDiff && currentVersion && selectedVersion.id !== currentVersion.id ? (
                  // Show differences
                  <div>
                    <h4 className="font-medium mb-3">Changes from Current Version</h4>
                    <div className="space-y-3">
                      {getDifferences(currentVersion, selectedVersion).map(({ field, oldValue, newValue, changed }) => (
                        <div key={field} className={`p-3 rounded-lg border ${
                          changed ? 'bg-yellow-50 border-yellow-200' : 'bg-gray-50 border-gray-200'
                        }`}>
                          <div className="font-medium capitalize mb-2">
                            {field.replace(/_/g, ' ')}
                            {changed && <span className="ml-2 text-yellow-600">• Changed</span>}
                          </div>
                          
                          {changed ? (
                            <div className="space-y-2">
                              <div className="p-2 bg-red-50 border-l-4 border-red-400 rounded">
                                <div className="text-sm text-red-700 font-medium">Current:</div>
                                <div className="text-sm">{oldValue}</div>
                              </div>
                              <div className="p-2 bg-green-50 border-l-4 border-green-400 rounded">
                                <div className="text-sm text-green-700 font-medium">This Version:</div>
                                <div className="text-sm">{newValue}</div>
                              </div>
                            </div>
                          ) : (
                            <div className="text-sm text-gray-600">
                              {newValue}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  // Show raw data  
                  <div>
                    <h4 className="font-medium mb-3">Version Data</h4>
                    <div className="space-y-3">
                      {Object.entries(selectedVersion.data).map(([field, value]) => (
                        <div key={field} className="p-3 bg-gray-50 rounded-lg">
                          <div className="font-medium capitalize mb-1">
                            {field.replace(/_/g, ' ')}
                          </div>
                          <div className="text-sm text-gray-600">
                            {getDataFieldValue(selectedVersion.data, field)}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* HIPAA Audit Notice */}
      <Card>
        <CardContent className="pt-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex">
              <div className="text-blue-600 mr-3">📋</div>
              <div className="text-sm text-blue-800">
                <p className="font-medium mb-1">Audit Trail</p>
                <p>
                  All medical record changes are permanently logged for compliance and audit purposes. 
                  Each version preserves the complete state of the record at that time. 
                  {canRevert && ' As a patient, you can revert to any previous version of your own records.'}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}