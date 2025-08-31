# Copilot Agent Instructions for Telemedicine App

This document provides instructions for the GitHub Copilot agent to understand and assist with the development of the Telemedicine App.

## 1. Project Overview

The project is a **Telemedicine App** that connects patients with healthcare providers for remote consultations. The platform facilitates appointment booking, secure video calls, medical records management, digital prescriptions, and payments. The system must be secure, reliable, and compliant with healthcare regulations like HIPAA.

## 2. User Roles

The system has three primary user roles:

-   **Patient**: Registers, books appointments, attends video consultations, manages their medical records, sends messages to providers, and makes payments.
-   **Healthcare Provider**: Registers (with admin approval), manages their availability, conducts video consultations, updates patient medical records, issues digital prescriptions, and communicates with patients.
-   **Admin**: Manages user accounts, oversees system configuration, generates audit and compliance reports, and monitors system health.

## 3. Core Features & Functionality

The application is divided into the following core modules. When generating code, refer to the detailed functional requirements and BDD scenarios.

-   **User Management**: Registration, multi-factor authentication (MFA), profile management, and role-based access control (RBAC).
-   **Appointment Management**: Providers set availability, patients book/reschedule/cancel appointments, and a waitlist system is available.
-   **Video Consultation**: Secure WebRTC-based video calls with features like screen sharing, call recording (with consent), and adaptive quality management.
-   **Medical Records Management (MRM)**: Secure storage, retrieval, sharing, and exporting of patient medical history (PHI). All access must be audited.
-   **Prescription Management**: Providers create and transmit digital prescriptions to pharmacies. Includes drug interaction checks and prescription history.
-   **Secure Communication**: End-to-end encrypted messaging between patients and providers, with support for file sharing and emergency escalations.
-   **Payment and Billing**: Integration with payment gateways to process consultation fees, generate bills, and manage insurance claims.
-   **Administrative Functions**: Dashboards for admins to manage users, configure the system, and monitor health and compliance.

## 4. Critical Non-Functional Requirements

Adherence to these requirements is critical. Generated code must respect these constraints.

-   **Security (CRITICAL)**:
    -   **HIPAA Compliance**: All handling of Protected Health Information (PHI) must be HIPAA compliant. This includes strict access controls, audit trails for all PHI access, and data privacy.
    -   **Encryption**: All sensitive data must be encrypted with **AES-256 at rest** and **TLS 1.3 in transit**. Video calls must be **end-to-end encrypted**.
    -   **Authentication**: **Multi-factor authentication (MFA)** is mandatory for all users. Use JWTs with short expiration times (≤ 15 minutes).

-   **Performance**:
    -   **Response Time**: Aim for page loads ≤ 3 seconds and video call initiation ≤ 5 seconds.
    -   **Video Quality**: Minimum 720p resolution at 24 fps with low latency (≤ 200ms).

-   **Reliability**:
    -   **Availability**: The system must have **99.9% uptime**.
    -   **Fault Tolerance**: Implement redundancy to avoid single points of failure. Use circuit breakers for external services.

-   **Maintainability**:
    -   **Code Quality**: Target **≥ 80% test coverage**, cyclomatic complexity ≤ 10, and code duplication ≤ 3%.
    -   **Monitoring**: Implement comprehensive logging and monitoring for all critical paths.

## 5. Development & Testing Strategy

-   **Behavior-Driven Development (BDD)**: Development follows BDD principles. New features or changes should be accompanied by Gherkin scenarios (`.feature` files) that describe the behavior from a user's perspective. Refer to `BDD.md` for examples.
-   **Testing**:
    -   Write unit, integration, and end-to-end tests.
    -   UI tests should follow the **Page Object Pattern**.
    -   Include tests for security, performance, and accessibility (WCAG 2.1 AA).
-   **Recommended Tech Stack** (from `BDD.md`):
    -   **Frontend**: Typescript/Nextjs (with Jest + Cucumber-js for testing)
    -   **Backend**: Python (with Behave or Pytest-bdd)
    -   **API Testing**: Use tools like Rest-assured.
    -   **Mobile**: Flutter
    -   **Database**: PostgreSQL

## 6. APIs and Integrations

The system will integrate with several external services. When working on these areas, assume the need for resilient and secure API clients.

-   **EMR Systems**: Must support integration with major Electronic Medical Record systems via the **HL7 FHIR R4** standard.
-   **Payment Gateways**: For processing credit card payments.
-   **Pharmacy Networks**: For electronically transmitting prescriptions.
-   **Insurance Providers**: For verifying eligibility and submitting claims.
-   **Notification Services**: For sending SMS and email alerts.
