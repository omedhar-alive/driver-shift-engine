# Architecture

## 1. System Purpose

## 2. Core Principles

### Multi-Client Platform Principle
The backend must be designed as one central platform that can serve multiple frontends and connected applications, not just one web interface.

This means:
- the backend remains frontend-agnostic
- business logic lives in the backend, not in any frontend
- the database remains the single source of truth
- all clients must interact through clear API contracts
- Google Sheets remains an integration, reporting, and monitoring layer only
- the architecture must remain open for future driver apps, supervisor dashboards, manager dashboards, admin panels, mobile apps, and external system integrations

## 3. High-Level Components

## 4. Main Operational Flow

## 5. Source of Truth

## 6. Async OCR Principle

## 7. Google Sheets Role

## 8. Exception Handling Principle

## 9. Initial Technical Stack