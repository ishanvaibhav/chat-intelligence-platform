# Studdy Buddy ERP Final Project Blueprint

## 1. Final Product Direction

Studdy Buddy ERP is a simple, role-based university management platform with smart attendance at its center.

It should feel easy to use, mobile-friendly, and fast to navigate.

The product will use `studdy_buddy_full` as the UI/UX reference for:

- clean card-based layout
- mobile-first dashboard patterns
- notifications
- schedule and planner inspiration
- simple action flows

It will **not** use `studdy_buddy_full` as the final backend or role model reference because that project is still closer to a student learning app than a complete ERP.

## 2. Final Product Goal

Build one platform that allows:

- students to track attendance, assignments, leaves, timetable, and fees
- teachers to mark attendance, upload assignments, and manage class activity
- HODs and mentors to monitor defaulters, approve leaves, manage timetable, and send warnings
- registrars to manage fee data and student records
- deans and directors to view summary reports
- admins to manage structure, roles, and system settings

## 3. Product Principles

This project must stay simple.

That means:

- every role gets one clear home dashboard
- important actions are reachable in one or two taps
- the main navigation stays short
- advanced controls are hidden inside detail pages, drawers, or modals
- the UI prioritizes summary first, detail second

## 4. Final Role Set

The product will support these six roles:

1. Admin
2. Student
3. Teacher
4. HOD or Mentor
5. Registrar
6. Dean or Director

## 5. Final Navigation System

The app should use the same shell for every role:

- web: left sidebar + topbar + main content
- mobile: bottom navigation + topbar + stacked cards

Main navigation should stay limited to these items:

- `Home`
- `Attendance`
- `Classes`
- `Requests`
- `Reports`
- `Profile`

Role-specific replacements:

- Registrar replaces `Classes` with `Finance`
- Admin replaces `Attendance` with `Users`
- Dean keeps `Reports` as the primary page

## 6. Final Role Dashboards

### Student

#### Main menu

- Home
- Attendance
- Classes
- Requests
- Fees
- Profile

#### Home dashboard cards

- attendance percentage
- classes today
- pending assignments
- leave request status
- fee due or paid status
- notification panel

#### Main features

- subject-wise attendance
- attendance warning if below 75%
- attendance simulator
- assignment list and submission status
- leave request form
- timetable view
- fee status and receipt download

### Teacher

#### Main menu

- Home
- Attendance
- Classes
- Requests
- Reports
- Profile

#### Home dashboard cards

- classes today
- pending attendance entries
- pending assignment reviews
- leave request status
- recent notices

#### Main features

- mark attendance by class session
- edit attendance within allowed window
- upload assignment
- add lecture summary
- view class attendance trend
- request leave

### HOD or Mentor

#### Main menu

- Home
- Attendance
- Classes
- Requests
- Reports
- Profile

#### Home dashboard cards

- total students
- defaulters
- pending leave approvals
- teachers free now
- timetable issues

#### Main features

- approve or reject leaves
- monitor students below attendance threshold
- send warning to student or teacher
- manage timetable
- view teacher availability
- basic department reports

### Registrar

#### Main menu

- Home
- Finance
- Requests
- Reports
- Users
- Profile

#### Home dashboard cards

- fees collected today
- students with pending dues
- pending record updates
- recent payments

#### Main features

- update fees
- manage fee status
- generate receipts
- export payment table
- add or update student records

### Dean or Director

#### Main menu

- Home
- Reports
- Requests
- Profile

#### Home dashboard cards

- department comparison
- attendance trend
- fee collection summary
- pending escalations

#### Main features

- view reports from HODs
- compare departments
- review performance trends
- view summary feedback

### Admin

#### Main menu

- Home
- Users
- Settings
- Reports
- Profile

#### Home dashboard cards

- total users
- active roles
- recent changes
- system sync status

#### Main features

- role management
- permissions management
- department and section structure setup
- system configuration
- university source integration configuration

## 7. Final MVP Modules

These are the modules that must be included in the first real product version:

- authentication and role-based access
- student dashboard
- teacher attendance marking
- subject-wise attendance tracking
- attendance simulator
- timetable
- assignments
- leave requests and approvals
- fee status
- notifications
- HOD defaulter tracking
- registrar fee management
- basic reports

## 8. Post-MVP Modules

These should be planned, but not built first:

- UTU or other university external sync
- AI attendance prediction
- advanced analytics
- feedback engine
- QR or OTP attendance
- hostel and transport management
- library management
- document workflows beyond receipts and leave proofs

## 9. Final Feature Matrix

| Module | Student | Teacher | HOD | Registrar | Dean | Admin |
| --- | --- | --- | --- | --- | --- | --- |
| Login and role access | View | View | View | View | View | Manage |
| Attendance | View | Manage | Review | Review | Review | Configure |
| Attendance simulator | View | - | - | - | - | - |
| Assignments | View | Manage | Review | - | - | Configure |
| Timetable | View | View | Manage | - | Review | Configure |
| Leave requests | Request | Request | Approve | - | Review | Configure |
| Fee status | View | - | Read only | Manage | Review | Configure |
| Student records | View own | View class | Manage | Manage | Review | Configure |
| Notifications | View | View | Manage | View | View | Configure |
| Reports | Personal | Class | Department | Finance | University | System |

## 10. Final Data Model

### Core tables

#### `users`

- id
- name
- email
- password_hash or auth_provider
- primary_role
- phone
- is_active
- created_at
- updated_at

#### `universities`

- id
- name
- code

#### `departments`

- id
- university_id
- name
- code

#### `programs`

- id
- department_id
- name
- degree_type

#### `sections`

- id
- program_id
- semester_no
- section_name
- mentor_user_id

#### `students`

- id
- user_id
- roll_no
- university_id
- department_id
- program_id
- section_id
- current_semester

#### `teachers`

- id
- user_id
- department_id
- designation

#### `subjects`

- id
- department_id
- program_id
- semester_no
- name
- code
- teacher_id

#### `subject_enrollments`

- id
- student_id
- subject_id

#### `class_sessions`

- id
- subject_id
- section_id
- teacher_id
- class_date
- start_time
- end_time
- topic
- status

#### `attendance_records`

- id
- class_session_id
- student_id
- status
- source
- marked_by
- marked_at

#### `assignments`

- id
- subject_id
- title
- description
- due_date
- created_by

#### `assignment_submissions`

- id
- assignment_id
- student_id
- submission_url
- status
- submitted_at

#### `leave_requests`

- id
- requester_user_id
- role_type
- start_date
- end_date
- reason
- attachment_url
- status
- approved_by
- approved_at
- comments

#### `fees`

- id
- student_id
- semester_no
- total_amount
- paid_amount
- due_amount
- status
- updated_by
- updated_at

#### `timetable_slots`

- id
- section_id
- day_of_week
- start_time
- end_time
- subject_id
- teacher_id
- room_no

#### `notifications`

- id
- user_id
- title
- message
- type
- is_read
- created_at

#### `warnings`

- id
- student_id
- subject_id
- issued_by
- reason
- message
- created_at

#### `audit_logs`

- id
- actor_user_id
- entity_type
- entity_id
- action
- old_value_json
- new_value_json
- created_at

## 11. Key Business Rules

- attendance below 75 percent is marked as risk
- students can view only their own data
- teachers can manage only assigned subjects and sections
- HODs can view department-wide data
- registrars can manage finance but not academic attendance editing
- admins manage structure and access, not regular operations
- every approval or update must be traceable in `audit_logs`

## 12. Final Student Attendance Logic

For each subject:

- total classes
- attended classes
- attendance percentage
- classes needed to reach 75 percent

Formula:

```text
required_classes = ceil((0.75 * total_classes - attended_classes) / 0.25)
```

If the result is less than or equal to zero, the student is safe.

## 13. Final Screen List

### Student

- login
- home dashboard
- attendance page
- subject detail
- assignments page
- leave request page
- timetable page
- fees page
- notifications page

### Teacher

- home dashboard
- mark attendance page
- assignment manager
- lecture summary form
- class report page
- leave request page

### HOD

- home dashboard
- defaulter page
- leave approval page
- timetable manager
- warning modal
- department report page

### Registrar

- home dashboard
- fee management table
- payment detail page
- receipt view
- student record management
- export page

### Dean

- home dashboard
- reports page
- department comparison page

### Admin

- home dashboard
- role management
- permissions settings
- structure management
- sync configuration

## 14. Final Reusable UI Components

Build these once and reuse them everywhere:

- app shell
- sidebar
- mobile bottom navigation
- topbar
- stat card
- table with filter
- search bar
- progress bar
- status badge
- modal
- side drawer
- empty state
- notification item
- approval card

## 15. Final Design Language

Use a cleaner version of the `studdy_buddy_full` feel.

### Colors

- primary: `#1E3A8A`
- secondary: `#3B82F6`
- success: `#10B981`
- warning: `#F59E0B`
- danger: `#EF4444`
- background: `#F8FAFC`
- card: `#FFFFFF`
- text primary: `#0F172A`
- text secondary: `#64748B`

### Layout

- sidebar width: `260px`
- topbar height: `64px`
- card radius: `12px`
- content padding: `24px`

### Typography

- heading font: `Poppins` or `Inter`
- body font: `Inter`

## 16. Final Tech Stack

### Recommended build

- frontend web: Next.js
- mobile app: React Native later, or responsive web first
- styling: Tailwind CSS
- backend: NestJS or Express
- database: PostgreSQL
- auth: JWT with refresh tokens
- file storage: S3 or Cloudinary
- notifications: Firebase Cloud Messaging

### Simpler alternative

If the project must be built faster:

- frontend: Next.js
- backend: Next.js API routes or Express
- database: PostgreSQL
- auth: NextAuth or JWT

## 17. Final Build Order

### Phase 1

- auth
- role-based routing
- student dashboard
- teacher attendance
- attendance tables
- timetable

### Phase 2

- leave workflow
- assignments
- HOD dashboard
- warnings

### Phase 3

- registrar finance module
- receipts
- reports

### Phase 4

- dean dashboard
- admin management
- external university integration

## 18. Final Decision Summary

The final version of this project should be:

- simple in navigation
- role-based in access
- attendance-first in value
- mobile-friendly for students and teachers
- table-driven for HODs and registrars
- scalable in database design

The product should not try to become a huge all-in-one ERP in the first version.

It should first become an excellent attendance, timetable, leave, assignment, and fee platform for universities.
