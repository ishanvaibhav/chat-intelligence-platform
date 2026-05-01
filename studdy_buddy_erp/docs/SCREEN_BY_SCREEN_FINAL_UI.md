# Studdy Buddy ERP Screen-by-Screen Final UI

This document converts the final product blueprint into concrete screens.

UI direction:

- use `studdy_buddy_full` as the visual reference for card rhythm, spacing, hero sections, and mobile usability
- use a cleaner academic color system instead of the current purple-heavy style
- keep every major task reachable in one or two taps

## 1. Global UI Rules

### Layout

- desktop: sidebar on the left, topbar on the top, content area on the right
- mobile: topbar plus bottom navigation
- page header always includes title, short description, and quick actions

### Reusable blocks

- hero summary card
- stat card
- status badge
- progress bar
- filter bar
- data table
- approval modal
- side drawer
- empty state
- notification list

### Status colors

- safe or success: green
- warning or pending: amber
- risk or rejected: red
- informational: blue

## 2. Authentication

### Login Screen

#### Purpose

Single login screen for all users.

#### Sections

- logo and product name
- email field
- password field
- role-aware sign in
- forgot password link
- support contact link

#### UX notes

- keep the form centered
- use a clean institutional tone
- after login, redirect based on role

## 3. Student Screens

### Student Home

#### Top cards

- current attendance
- classes today
- pending assignments
- leave status
- fee due summary

#### Main sections

- hero card with name, roll number, branch, and quick attendance health
- today's timetable list
- pending assignments list
- recent notifications
- quick actions:
  - apply leave
  - view fees
  - open attendance

#### Mobile notes

- keep all cards full-width
- convert the timetable list into stacked cards

### Student Attendance

#### Sections

- overall attendance card
- subject-wise attendance grid
- attendance simulator card
- warning banner if below 75 percent

#### Each subject card shows

- subject name
- attendance percentage
- total classes
- attended classes
- classes needed to become safe

#### Main action

- open subject detail

### Student Subject Detail

#### Sections

- subject header with teacher and section
- progress bar
- attendance history table
- class session list
- warnings received

### Student Classes

#### Tabs

- timetable
- assignments
- lecture summaries

#### Timetable block

- weekly class cards
- current class highlight

#### Assignment block

- subject
- deadline
- status
- submit action or view status

### Student Requests

#### Sections

- leave request form
- uploaded proof field
- request history
- status filter

#### Main action

- submit leave request

### Student Fees

#### Sections

- total due
- amount paid
- due date
- payment history
- receipt list

#### Main actions

- download receipt
- view ledger details

### Student Profile

#### Sections

- basic info
- course info
- contact info
- password change
- notification preferences

## 4. Teacher Screens

### Teacher Home

#### Top cards

- classes today
- pending attendance
- pending reviews
- leave status

#### Main sections

- today's class list
- recent assignment activity
- notices panel
- quick actions:
  - mark attendance
  - upload assignment
  - add lecture summary

### Teacher Attendance

#### Sections

- class selector
- session selector
- student attendance table
- mark all present shortcut
- save and submit actions

#### Table columns

- student name
- roll number
- attendance status
- remark

### Teacher Classes

#### Tabs

- timetable
- assignments
- lecture summary

#### Assignment manager

- assignment title
- due date
- publish status
- submission count

#### Lecture summary form

- topic taught
- summary
- classroom environment notes

### Teacher Requests

#### Sections

- leave form
- request history
- approval status

### Teacher Reports

#### Sections

- average attendance by class
- weak students list
- monthly trend chart
- absent streak panel

## 5. HOD Screens

### HOD Home

#### Top cards

- total students
- defaulters
- pending approvals
- free teachers now

#### Main sections

- defaulter table
- leave approval queue
- timetable conflicts
- teacher availability list
- quick actions:
  - send warning
  - approve leave
  - edit timetable

### HOD Attendance

#### Sections

- department attendance trend
- defaulters table
- section filter
- subject filter
- warning action drawer

#### Defaulter table columns

- student
- section
- subject
- percentage
- risk level
- action

### HOD Classes

#### Sections

- timetable manager
- drag-and-drop schedule view
- free teacher panel
- room usage panel

### HOD Requests

#### Sections

- leave approval table
- request details drawer
- approve or reject modal

#### Each row shows

- requester
- role
- dates
- reason
- current status

### HOD Reports

#### Sections

- department attendance summary
- faculty performance summary
- leave trends
- downloadable reports

## 6. Registrar Screens

### Registrar Home

#### Top cards

- fee collected today
- total pending dues
- pending record updates
- recent successful payments

#### Main sections

- dues table
- recent payment feed
- student search
- quick actions:
  - update fee
  - generate receipt
  - open student record

### Registrar Finance

#### Sections

- fee ledger table
- filters for semester, program, section, and fee status
- payment detail side drawer
- receipt generation modal

#### Table columns

- student
- roll number
- semester
- total amount
- paid amount
- due amount
- status
- action

### Registrar Requests

#### Sections

- correction requests
- record update requests
- payment issue list

### Registrar Reports

#### Sections

- fee collection trends
- overdue students
- export panel

### Registrar Users

#### Sections

- student directory
- add student action
- update student record action
- search and filter bar

## 7. Dean Screens

### Dean Home

#### Top cards

- departments compared
- attendance trend
- fee collection overview
- escalations pending

#### Main sections

- executive summary hero card
- department ranking cards
- trend graphs
- escalation inbox

### Dean Reports

#### Sections

- department comparison chart
- attendance performance chart
- finance summary chart
- export summary panel

### Dean Requests

#### Sections

- escalated items only
- request detail drawer
- final decision action

## 8. Admin Screens

### Admin Home

#### Top cards

- total users
- active roles
- recent changes
- sync health

#### Main sections

- recent access changes
- integration status
- quick actions:
  - add role
  - edit permissions
  - configure structure

### Admin Users

#### Sections

- user list
- role chips
- permission drawer
- add or edit user modal

### Admin Settings

#### Sections

- university setup
- department setup
- section setup
- integration source setup

### Admin Reports

#### Sections

- audit log summary
- system usage cards
- sync run history

## 9. Mobile Behavior

### Student and Teacher

- bottom navigation instead of sidebar
- cards stacked vertically
- quick actions visible above fold
- tables converted into card lists where possible

### HOD, Registrar, Dean, Admin

- use responsive tables with horizontal scroll
- preserve filter bar as sticky top action area
- replace side drawer with full-screen modal on small screens

## 10. Final UI Priority Order

Build these screens first:

1. Login
2. Student Home
3. Student Attendance
4. Teacher Attendance
5. HOD Home
6. HOD Requests
7. Registrar Finance
8. Dean Reports
9. Admin Users

These screens define almost the whole product experience and can be used to build the design system quickly.
