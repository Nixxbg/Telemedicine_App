"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PatientLogin, DoctorLogin } from "@/types";

interface LoginFormProps {
  userType: 'patient' | 'doctor';
  onSubmit: (data: PatientLogin | DoctorLogin) => Promise<void>;
  loading?: boolean;
  error?: string;
}

export function LoginForm({ userType, onSubmit, loading = false, error }: LoginFormProps) {
  const [formData, setFormData] = useState<PatientLogin | DoctorLogin>(() => {
    if (userType === 'patient') {
      return { email: '', password: '' };
    } else {
      return { email: '', doctor_id: '', password: '' };
    }
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit(formData);
  };

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle className="text-2xl font-bold text-center">
          {userType === 'patient' ? 'Patient Login' : 'Doctor Login'}
        </CardTitle>
        <CardDescription className="text-center">
          Sign in to your {userType} account
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="email" className="text-sm font-medium">
              Email Address
            </label>
            <Input
              id="email"
              type="email"
              value={formData.email}
              onChange={(e) => handleChange('email', e.target.value)}
              placeholder="Enter your email"
              required
              disabled={loading}
            />
          </div>

          {userType === 'doctor' && (
            <div className="space-y-2">
              <label htmlFor="doctor_id" className="text-sm font-medium">
                Doctor ID
              </label>
              <Input
                id="doctor_id"
                type="text"
                value={(formData as DoctorLogin).doctor_id}
                onChange={(e) => handleChange('doctor_id', e.target.value)}
                placeholder="Enter your doctor ID (e.g., DOC001)"
                required
                disabled={loading}
              />
            </div>
          )}

          <div className="space-y-2">
            <label htmlFor="password" className="text-sm font-medium">
              Password
            </label>
            <Input
              id="password"
              type="password"
              value={formData.password}
              onChange={(e) => handleChange('password', e.target.value)}
              placeholder="Enter your password"
              required
              disabled={loading}
            />
          </div>

          {error && (
            <div className="text-sm text-red-600 bg-red-50 p-3 rounded-md">
              {error}
            </div>
          )}

          <Button 
            type="submit" 
            className="w-full" 
            disabled={loading}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}