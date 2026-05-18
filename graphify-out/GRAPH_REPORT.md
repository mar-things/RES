# Graph Report - .  (2026-05-18)

## Corpus Check
- Corpus is ~30,444 words - fits in a single context window. You may not need a graph.

## Summary
- 665 nodes · 883 edges · 71 communities (60 shown, 11 thin omitted)
- Extraction: 78% EXTRACTED · 21% INFERRED · 1% AMBIGUOUS · INFERRED: 184 edges (avg confidence: 0.73)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Repr Models Repair|Repr Models Repair]]
- [[_COMMUNITY_Minutes Time Card|Minutes Time Card]]
- [[_COMMUNITY_Build Section Insurance|Build Section Insurance]]
- [[_COMMUNITY_Seed Create Database|Seed Create Database]]
- [[_COMMUNITY_Send Notification Message|Send Notification Message]]
- [[_COMMUNITY_Task Feature Request|Task Feature Request]]
- [[_COMMUNITY_Cost Estimator Engineer|Cost Estimator Engineer]]
- [[_COMMUNITY_Bay Capacity Occupancy|Bay Capacity Occupancy]]
- [[_COMMUNITY_Kanban Build Column|Kanban Build Column]]
- [[_COMMUNITY_Navigation Sidebar Login|Navigation Sidebar Login]]
- [[_COMMUNITY_Python Testing Build|Python Testing Build]]
- [[_COMMUNITY_Password Login Bcrypt|Password Login Bcrypt]]
- [[_COMMUNITY_Folder Architecture Accepted|Folder Architecture Accepted]]
- [[_COMMUNITY_Front Rear Bumper|Front Rear Bumper]]
- [[_COMMUNITY_Record Company Insurance|Record Company Insurance]]
- [[_COMMUNITY_Customer Notify About|Customer Notify About]]
- [[_COMMUNITY_Front Inspection Body|Front Inspection Body]]
- [[_COMMUNITY_Damage Report Acknowledge|Damage Report Acknowledge]]
- [[_COMMUNITY_Active Get All|Active Get All]]
- [[_COMMUNITY_User Current Role|User Current Role]]
- [[_COMMUNITY_Check Orm Rollback|Check Orm Rollback]]
- [[_COMMUNITY_Orm Customer Get|Orm Customer Get]]
- [[_COMMUNITY_Insurance Pending Ack|Insurance Pending Ack]]
- [[_COMMUNITY_Rear Back Body|Rear Back Body]]
- [[_COMMUNITY_Services Auth Autherror|Services Auth Autherror]]
- [[_COMMUNITY_List Return Active|List Return Active]]
- [[_COMMUNITY_Dashboardwidget Refresh Vehiclecardwidget|Dashboardwidget Refresh Vehiclecardwidget]]
- [[_COMMUNITY_Right Ambiguous Baseline|Right Ambiguous Baseline]]
- [[_COMMUNITY_Pending Insurer Test|Pending Insurer Test]]
- [[_COMMUNITY_Login Screen Build|Login Screen Build]]
- [[_COMMUNITY_Adapter Contract Send|Adapter Contract Send]]
- [[_COMMUNITY_User Bcrypt Password|User Bcrypt Password]]
- [[_COMMUNITY_Insurer List Pending|Insurer List Pending]]
- [[_COMMUNITY_Acknowledge Approve Args|Acknowledge Approve Args]]
- [[_COMMUNITY_Orange Top Areas|Orange Top Areas]]
- [[_COMMUNITY_Cost Api Classifier|Cost Api Classifier]]
- [[_COMMUNITY_Centralized Contract Cost|Centralized Contract Cost]]
- [[_COMMUNITY_Engineer Agent Analytics|Engineer Agent Analytics]]
- [[_COMMUNITY_Postgres Bcrypt Compose|Postgres Bcrypt Compose]]
- [[_COMMUNITY_Role Based Mainwindow|Role Based Mainwindow]]
- [[_COMMUNITY_Seed Default Load|Seed Default Load]]
- [[_COMMUNITY_Reporting Access Application|Reporting Access Application]]
- [[_COMMUNITY_Boundary Offline Api|Boundary Offline Api]]
- [[_COMMUNITY_Findingsdialog Card Clicked|Findingsdialog Card Clicked]]
- [[_COMMUNITY_Login Mainwindow Loginscreen|Login Mainwindow Loginscreen]]
- [[_COMMUNITY_Registervehicledialog Companies Crash|Registervehicledialog Companies Crash]]
- [[_COMMUNITY_Rollback Back Business|Rollback Back Business]]
- [[_COMMUNITY_Mainwindow Object Retranslateui|Mainwindow Object Retranslateui]]
- [[_COMMUNITY_Report Behavior Bug|Report Behavior Bug]]
- [[_COMMUNITY_Audit Bias Governance|Audit Bias Governance]]
- [[_COMMUNITY_Action Callbacks Insurance|Action Callbacks Insurance]]
- [[_COMMUNITY_Agent Automation Checklist|Agent Automation Checklist]]
- [[_COMMUNITY_Calculation Minutes Active|Calculation Minutes Active]]
- [[_COMMUNITY_Applicable Processes Register|Applicable Processes Register]]
- [[_COMMUNITY_Main Window Application|Main Window Application]]
- [[_COMMUNITY_Functional Init Mainwindow|Functional Init Mainwindow]]
- [[_COMMUNITY_Archived Bootstrap Generated|Archived Bootstrap Generated]]
- [[_COMMUNITY_Dependencies Mainwindow Pyside6|Dependencies Mainwindow Pyside6]]
- [[_COMMUNITY_Init Dialogs Package|Init Dialogs Package]]
- [[_COMMUNITY_Cards Display Kiosk|Cards Display Kiosk]]
- [[_COMMUNITY_Convert Display Label|Convert Display Label]]
- [[_COMMUNITY_Color Hex Inline|Color Hex Inline]]
- [[_COMMUNITY_Inventory Models Parts|Inventory Models Parts]]
- [[_COMMUNITY_Calculation Time Variance|Calculation Time Variance]]
- [[_COMMUNITY_Get|Get]]

## God Nodes (most connected - your core abstractions)
1. `get_session()` - 29 edges
2. `Base` - 17 edges
3. `CapacityTracker` - 16 edges
4. `DashboardWidget` - 16 edges
5. `MainWindow` - 16 edges
6. `AI Cost Estimator` - 13 edges
7. `InsuranceDashboard` - 12 edges
8. `RegisterVehicleDialog` - 12 edges
9. `Orange Sedan Left-Side Profile Image` - 12 edges
10. `Process` - 11 edges

## Surprising Connections (you probably didn't know these)
- `Role Based Access Enforcement` --semantically_similar_to--> `Role Based Navigation`  [INFERRED] [semantically similar]
  .github/agents/05-security-release-engineer.md → ui/main_window.py
- `Archived pywhatkit WhatsApp demo` --semantically_similar_to--> `Send WhatsApp via configured provider`  [INFERRED] [semantically similar]
  Archive/Whatsapp.py → services/notification_service.py
- `Reporting and Analytics Engineer` --conceptually_related_to--> `Pending Findings KPI`  [INFERRED]
  .github/agents/04-reporting-analytics-engineer.md → ui/insurance_dashboard.py
- `AI Cost Estimator Placeholder` --conceptually_related_to--> `RES AI Agent Team`  [INFERRED]
  ui/dialogs/findings_dialog.py → .github/agents/00-team-overview.md
- `Findings service pending insurer wrapper` --calls--> `List pending findings for insurer`  [AMBIGUOUS]
  services/findings_service.py → core/findings_manager.py

## Hyperedges (group relationships)
- **Repair Pipeline State Flow** — vehicle_service_register_vehicle, process_engine_checkin, process_engine_checkout, models_processlog, models_processtransition, time_tracker_elapsed_minutes [EXTRACTED 0.92]
- **Finding Approval Workflow** — findings_manager_report_finding, findings_manager_acknowledge_finding, findings_manager_approve_finding, findings_service_report_finding, notification_service_notify_finding, models_finding [EXTRACTED 0.94]
- **Role-Based Access and Audit Trail** — auth_service_login, auth_service_require_role, models_user, models_processrollback, models_notificationlog, models_soft_delete_audit_trail [INFERRED 0.78]
- **Desktop UI Workflow Shell** — login_screen_LoginScreen, main_window_MainWindow, dashboard_widget_DashboardWidget, insurance_dashboard_InsuranceDashboard [EXTRACTED 1.00]
- **Finding Lifecycle Flow** — dashboard_widget_DashboardWidget__on_card_clicked, findings_dialog_FindingsDialog, insurance_dashboard_InsuranceDashboard, insurance_dashboard_Finding_Action_Callbacks, agents_reporting_Findings_SLA_Metrics [INFERRED 0.84]
- **RES Agent Ownership Model** — agents_product_Product_Domain_Lead, agents_backend_Core_Backend_Engineer, agents_ui_Desktop_UI_Engineer, agents_reporting_Reporting_Analytics_Engineer, agents_security_Security_Release_Engineer, agents_qa_QA_Test_Automation_Engineer [EXTRACTED 1.00]
- **Architecture Boundaries and Contracts** — 0001_initial_architecture_monorepo_boundaries, contracts_folder_ownership, contracts_service_layer_contract, contracts_data_layer_contract, contracts_integrations_contract, contracts_reporting_contract, contracts_ai_module_contract [INFERRED 0.90]
- **AI Cost Estimator Integration Flow** — 07_ai_cost_estimator_engineer_smartphone_photos, 07_ai_cost_estimator_engineer_ai_engine, 07_ai_cost_estimator_engineer_severity_classifier, 07_ai_cost_estimator_engineer_cost_model, 07_ai_cost_estimator_engineer_db_writer, 07_ai_cost_estimator_engineer_findings_cost_estimator_ref, contracts_estimate_cost [INFERRED 0.86]
- **Quality Control Workflow** — bug_bug_report_template, feature_feature_request_template, task_task_template, ci_ci_workflow, ci_ruff_lint_format, ci_mypy_typecheck, ci_pytest_headless [INFERRED 0.82]
- **Back View Visible Rear Components** — back_png_rear_bumper, back_png_tail_lights, back_png_rear_window, back_png_side_mirrors, back_png_exhaust_pipe, back_png_rear_wheels [EXTRACTED 1.00]
- **Rear Inspection Cost Estimator Context** — back_png_cost_estimator_back_reference, back_png_rear_vehicle_view, back_png_rear_bumper, back_png_tail_lights, back_png_no_visible_damage_state [INFERRED 0.72]
- **Visible Front Exterior Parts** — front_vehicle_front_body_panel, front_grille, front_headlights, front_fog_lamps, front_windshield, front_side_mirrors, front_front_wheels [EXTRACTED 1.00]
- **Left-Side Vehicle Inspection Regions** — left_image_front_bumper_headlight_region, left_image_front_fender, left_image_front_door, left_image_rear_door, left_image_rear_quarter_panel, left_image_rear_bumper_trunk_region, left_image_rocker_panel, left_image_two_visible_wheels, left_image_side_windows [INFERRED 0.84]
- **Right.png Vehicle Inspection Features** — right_png_orange_sedan_side_view, right_png_intact_body_panels, right_png_visible_wheels, right_png_side_doors_windows, right_png_damage_absence_visual_baseline [INFERRED 0.82]
- **Visible Vehicle Parts** — top_png_orange_body_panels, top_png_dark_glass_areas, top_png_central_black_panel, top_png_side_mirrors [EXTRACTED 1.00]
- **Cost Estimation Visual Inputs** — top_png_vehicle_top_projection, top_png_visual_part_segmentation_reference, top_png_cost_estimator_vehicle_surface_context [INFERRED 0.70]

## Communities (71 total, 11 thin omitted)

### Community 0 - "Repr Models Repair"
Cohesion: 0.05
Nodes (48): Base, Base, Declarative base class for all ORM models.      All models in models.py inheri, Customer, Finding, InsuranceCompany, NotificationLog, _now() (+40 more)

### Community 1 - "Minutes Time Card"
Cohesion: 0.08
Nodes (26): compute_transit_minutes(), elapsed_minutes(), format_duration(), RES — core/time_tracker.py ============================ Time tracking calculat, Estimate the total remaining repair time for a vehicle.      Sums remaining ti, Compute the transit time in minutes between checkout of one process     and che, Format a duration in minutes as a human-readable string.      Args:         m, Return a color code for a process log based on its remaining time.      Used b (+18 more)

### Community 2 - "Build Section Insurance"
Cohesion: 0.09
Nodes (15): FindingsDialog, RES — ui/dialogs/findings_dialog.py ==================================== Dialo, Validate the form and call the service to record the finding., Dialog used by workshop staff to log a new finding.      Attributes:, RES — ui/dialogs/register_vehicle_dialog.py ===================================, Build the Customer Information section., Build the Vehicle Information section., Build the Insurance (optional) section. (+7 more)

### Community 3 - "Seed Create Database"
Cohesion: 0.11
Nodes (19): _create_engine(), init_db(), RES — core/database.py ======================== Database connection and sessio, Create all tables defined in models.py if they do not already exist.      This, Create and configure the SQLAlchemy engine from AppConfig.      For SQLite, en, RES — core/seeds.py ===================== Database seed data.  Populates the, Insert the default repair pipeline processes if not already present.      Exis, Create a default admin user if no users exist yet.      IMPORTANT: Change the (+11 more)

### Community 4 - "Send Notification Message"
Cohesion: 0.15
Nodes (21): _checkin_message(), _checkout_message(), _finding_message(), _log_notification(), notify_checkin(), notify_checkout(), notify_finding(), notify_ready_for_pickup() (+13 more)

### Community 5 - "Task Feature Request"
Cohesion: 0.11
Nodes (19): CI Workflow, Main Branch Push Trigger, Mypy Typecheck, Pull Request Trigger, Python 3.11, Ruff Lint and Format Check, CI Test Job, ubuntu-latest Runner (+11 more)

### Community 6 - "Cost Estimator Engineer"
Cohesion: 0.13
Nodes (18): AI Cost Estimator, AI Cost Estimator Engineer, Core Backend, cost_estimator README, Severity Class Cost Range Confidence Outputs, Evaluation Harness, Human Override Workflow, Main RES DB (+10 more)

### Community 7 - "Bay Capacity Occupancy"
Cohesion: 0.12
Nodes (10): CapacityTracker, RES — core/capacity_tracker.py ================================ Bay capacity t, Return occupancy info for all tracked process bays.          Returns:, Determine why a vehicle is not moving to the next process.          Used when, Tracks current bay occupancy for each repair process.      Usage:         tra, Initialise the tracker.          Call refresh() after construction to load cur, Reload current occupancy counts from the database.          Call this every ti, Return occupancy information for a single process bay.          Args: (+2 more)

### Community 8 - "Kanban Build Column"
Cohesion: 0.17
Nodes (10): QWidget, DashboardWidget, RES — ui/dashboard_widget.py ============================== Workshop Kanban da, Reload all data from the database and rebuild the Kanban board.          Calle, Build a single Kanban column for a repair process.          Args:, Open the Register Vehicle dialog and refresh the dashboard         if registrat, Handle a vehicle card click by showing a context menu.          The menu offer, The main workshop Kanban dashboard.      Shows one scrollable column per repai (+2 more)

### Community 9 - "Navigation Sidebar Login"
Cohesion: 0.16
Nodes (9): MainWindow, Build the left navigation sidebar.          Returns:             A QWidget co, Create a sidebar navigation button.          Args:             label:      Bu, Switch the main content area to the specified page index.          Args:, Highlight the active navigation button.          Args:             active_ind, Log out the current user and return to the login screen., The application shell window.      Contains a sidebar for navigation and a pag, Initialise the main window and show the login screen. (+1 more)

### Community 10 - "Python Testing Build"
Cohesion: 0.12
Nodes (15): build, context, dockerfile, customizations, vscode, name, postCreateCommand, remoteUser (+7 more)

### Community 11 - "Password Login Bcrypt"
Cohesion: 0.14
Nodes (14): AuthUser, hash_password(), is_logged_in(), login(), logout(), RES — services/auth_service.py ================================ Authentication, Clear the current in-memory session., Return True if a user is currently logged in. (+6 more)

### Community 12 - "Folder Architecture Accepted"
Cohesion: 0.15
Nodes (14): Accepted Architecture Status, ADR 0001 Initial Architecture, Monorepo Module Boundaries, PySide6 Qt Widgets, Headless Pytest, Qt System Dependencies, ai Folder, app Folder (+6 more)

### Community 13 - "Front Rear Bumper"
Cohesion: 0.19
Nodes (14): Ambiguous Exact Vehicle Make or Model, Front Bumper and Headlight Region, Front Door, Front Fender, No Obvious Visible Damage, Orange Sedan Left-Side Profile Image, Rear Bumper and Trunk Region, Rear Door (+6 more)

### Community 14 - "Record Company Insurance"
Cohesion: 0.19
Nodes (13): get_session(), Provide a transactional database session as a context manager.      Automatica, acknowledge_finding(), approve_finding(), get_findings_for_vehicle(), RES — core/findings_manager.py ================================ Business logic, Record that an insurance company rejected the finding., Retrieve all findings for a specific vehicle. (+5 more)

### Community 15 - "Customer Notify About"
Cohesion: 0.15
Nodes (13): AppConfig, Environment-backed configuration single source of truth, Create configured SQLAlchemy engine, SQLite WAL and foreign key setup, NotificationLog ORM model, Client-only notification policy, Persist notification audit log, Notify customer about process check-in (+5 more)

### Community 16 - "Front Inspection Body"
Cohesion: 0.21
Nodes (12): Stylized Render Rather Than Real Inspection Photo, Cost Estimator Front Inspection Input, Fog Lamps, Front Wheels, Front Grille, Headlights, Front Vehicle Image, Orange Car Front View (+4 more)

### Community 17 - "Damage Report Acknowledge"
Cohesion: 0.21
Nodes (12): AI Cost Estimator Phase 7 placeholder, PySide6 Dev Container Environment, Acknowledge damage finding, Approve damage finding, Finding approval updates vehicle approved budget, Reject damage finding, Report damage finding, Findings service report and notify workflow (+4 more)

### Community 18 - "Active Get All"
Cohesion: 0.17
Nodes (11): get_active_log(), get_active_processes(), get_all_active_vehicle_logs(), get_last_completed_log(), get_process_by_id(), RES — core/process_engine.py ============================== Core business logi, Find an open (not yet checked-out) ProcessLog for a vehicle and process., Return the most recently completed ProcessLog for a vehicle.      Used to reco (+3 more)

### Community 19 - "User Current Role"
Cohesion: 0.18
Nodes (9): get_current_user(), has_role(), Return the currently logged-in user.      Returns:         The current AuthUs, Check whether the current user has one of the specified roles.      Args:, Raise PermissionError if the current user does not have the required role., require_role(), Show or hide nav items based on the current user's role.          insurance-vi, Called when the user logs in successfully.          Replaces the login screen (+1 more)

### Community 20 - "Check Orm Rollback"
Cohesion: 0.24
Nodes (11): Determine transition delay reason, Transactional database session context manager, ProcessRollback ORM model, ProcessTransition ORM model, Capacity enforcement before check-in, Vehicle process check-in, Vehicle process check-out, Transit time recording on check-in (+3 more)

### Community 21 - "Orm Customer Get"
Cohesion: 0.24
Nodes (11): CapacityTracker, Refresh bay occupancy, SQLAlchemy Declarative Base, Customer ORM model, Process ORM model, ProcessLog ORM model, Table-driven repair process pipeline, Get applicable processes by crash severity (+3 more)

### Community 22 - "Insurance Pending Ack"
Cohesion: 0.27
Nodes (4): InsuranceDashboard, RES — ui/insurance_dashboard.py ================================= Widget shown, Insurance company dashboard for tracking pending findings., Reload pending findings from the database and update the table.

### Community 23 - "Rear Back Body"
Cohesion: 0.22
Nodes (10): Cost Estimator Back View Reference, Visible Exhaust Pipe, No Visible Rear Damage State, Orange Car Body, Rear Bumper, Rear Vehicle View Illustration, Rear Wheels, Dark Rear Window (+2 more)

### Community 24 - "Services Auth Autherror"
Cohesion: 0.20
Nodes (10): AuthError, core/services/auth.py, ConflictError, NotFoundError, core/services/process.py, Service Layer Contract, Services Do Not Import UI Code, Typed Service Exceptions (+2 more)

### Community 25 - "List Return Active"
Cohesion: 0.20
Nodes (9): get_or_create_customer(), get_vehicle_by_plate(), list_active_vehicles(), list_insurance_companies(), RES — services/vehicle_service.py ==================================== Busines, Search for a vehicle by exact license plate (case-insensitive).      Args:, Return all non-deleted, non-delivered vehicles.      Returns:         List of, Return an existing customer matching phone_whatsapp, or create a new one. (+1 more)

### Community 26 - "Dashboardwidget Refresh Vehiclecardwidget"
Cohesion: 0.22
Nodes (9): DashboardWidget, DashboardWidget._build_process_column, DashboardWidget.refresh, Dashboard Auto Refresh Interval, Workshop Kanban Dashboard, Vehicle Time Status Color Coding, VehicleCardWidget, VehicleCardWidget.update_data (+1 more)

### Community 27 - "Right Ambiguous Baseline"
Cohesion: 0.25
Nodes (9): Cost Estimator Vehicle Example, No Obvious Exterior Damage Baseline, Vehicle Direction or Side Naming Ambiguous, Right.png Image, Intact Body Panels, Orange Sedan Side View, Right Side Reference View, Side Doors and Windows (+1 more)

### Community 28 - "Pending Insurer Test"
Cohesion: 0.22
Nodes (6): list_pending_findings_for_insurer(), Return all currently pending findings for a given insurer.      The returned F, list_pending_for_insurer(), Return pending findings belonging to a particular insurance company., Unit tests for the findings manager and service.  These tests exercise the cor, test_pending_list_returns_empty_for_no_insurer()

### Community 29 - "Login Screen Build"
Cohesion: 0.25
Nodes (6): QFrame, LoginScreen, RES — ui/login_screen.py ========================== Login screen widget.  Sh, Full-window login form.      Signals:         login_successful: Emitted when, Build the login screen UI., Centre a card-style login form on the screen.

### Community 30 - "Adapter Contract Send"
Cohesion: 0.25
Nodes (8): Contract Update Rule, Integrations Contract, KPI Definitions, RES Contracts, send_email Adapter, send_sms Adapter, Vendor SDK Isolation, PythonDev Agent File

### Community 31 - "User Bcrypt Password"
Cohesion: 0.29
Nodes (8): AuthUser session snapshot, In-memory current user session, Hash password with bcrypt, Authenticate user login, Require role authorization check, Verify password with bcrypt, User ORM model, Seed default admin user

### Community 32 - "Insurer List Pending"
Cohesion: 0.25
Nodes (8): List pending findings for insurer, Findings service pending insurer wrapper, Missing list_pending_findings_for_insurer import risk, InsuranceCompany ORM model, Soft delete and audit trail design, Vehicle ORM model, Get vehicle by license plate, List active vehicles

### Community 33 - "Acknowledge Approve Args"
Cohesion: 0.25
Nodes (3): RES — services/findings_service.py ==================================== Higher, Create a new finding and notify the customer.      Args mirror those of :func:, report_finding()

### Community 34 - "Orange Top Areas"
Cohesion: 0.36
Nodes (8): Central Black Panel, Cost Estimator Vehicle Surface Context, Dark Glass Areas, Orange Body Panels, Side Mirrors, Top View Orange Car, Vehicle Top Projection, Visual Part Segmentation Reference

### Community 35 - "Cost Api Classifier"
Cohesion: 0.29
Nodes (7): ai_engine, cost_estimator Modules, cost_model, OpenAI Vision API, photo_handler, severity_classifier, YOLOv8

### Community 36 - "Centralized Contract Cost"
Cohesion: 0.29
Nodes (7): Postgres Migration Path, SQLite Local First Deployment, db_writer, findings.cost_estimator_ref, Centralized DB Session Factory, Data Layer Contract, SQLAlchemy Models

### Community 37 - "Engineer Agent Analytics"
Cohesion: 0.43
Nodes (7): Core Backend Engineer, RES AI Agent Team, Product and Domain Lead, Reporting and Analytics Engineer, Desktop UI Engineer, AI Cost Estimator Placeholder, SQLAlchemy Dependency

### Community 38 - "Postgres Bcrypt Compose"
Cohesion: 0.33
Nodes (7): Security and Release Engineer, Optional Postgres Service, Optional pgAdmin Service, Postgres Docker Compose Profile, bcrypt Dependency, python-dotenv Dependency, Dev Container Workflow

### Community 39 - "Role Based Mainwindow"
Cohesion: 0.33
Nodes (7): Role Based Access Enforcement, InsuranceDashboard, Insurer Scoped Findings, MainWindow._apply_role_visibility, MainWindow._build_main_ui, PlaceholderWidget, Role Based Navigation

### Community 40 - "Seed Default Load"
Cohesion: 0.29
Nodes (7): Initialize database schema, Load Qt dark theme stylesheet, Load Qt translation, Application bootstrap main, Default repair pipeline seed data, Run all seed functions, Seed default processes

### Community 41 - "Reporting Access Application"
Cohesion: 0.33
Nodes (6): Dashboards and Reporting, RES Desktop First Application, Role Based Access, build_kpi_snapshot, Report Exports, Reporting Contract

### Community 42 - "Boundary Offline Api"
Cohesion: 0.33
Nodes (6): Service Boundary Discipline, Offline Capability, Service Layer Architecture, MVP Vision API Estimator, Offline Safe Fallback, Service Boundary Owns Transactions

### Community 43 - "Findingsdialog Card Clicked"
Cohesion: 0.33
Nodes (6): PyWhatKit WhatsApp Message Log, DashboardWidget._on_card_clicked, Finding Report Form, FindingsDialog, FindingsDialog._on_submit, VehicleCardWidget.mousePressEvent

### Community 44 - "Login Mainwindow Loginscreen"
Cohesion: 0.33
Nodes (6): Authentication Gate, LoginScreen, LoginScreen._attempt_login, MainWindow._build_login_ui, MainWindow._on_login_success, MainWindow._on_logout

### Community 45 - "Registervehicledialog Companies Crash"
Cohesion: 0.33
Nodes (6): DashboardWidget._on_new_vehicle, Crash Severity Routing, RegisterVehicleDialog, RegisterVehicleDialog._load_insurance_companies, RegisterVehicleDialog._on_submit, Vehicle Registration Form

### Community 46 - "Rollback Back Business"
Cohesion: 0.33
Nodes (5): checkout(), Record a vehicle checking out of a repair process.      Updates the open Proce, RES — core/rollback_manager.py ================================ Business logic, Roll back a vehicle from its current process to a prior process.      This ope, rollback_vehicle()

### Community 48 - "Report Behavior Bug"
Cohesion: 0.40
Nodes (5): Bug Report Template, Defect Report, Expected Behavior, Logs and Screenshots, Steps to Reproduce

### Community 49 - "Audit Bias Governance"
Cohesion: 0.50
Nodes (4): Prompt and Result Version Audit, Bias and Uncertainty Messaging, Photo Data Retention Rules, Safety and Governance

### Community 50 - "Action Callbacks Insurance"
Cohesion: 0.50
Nodes (4): Findings SLA Metrics, Insurance Finding Action Callbacks, InsuranceDashboard.refresh, Pending Findings KPI

### Community 51 - "Agent Automation Checklist"
Cohesion: 0.67
Nodes (4): Agent Coordination Rules, QA and Test Automation Engineer, Pull Request Quality Checklist, Local Quick Start

### Community 52 - "Calculation Minutes Active"
Cohesion: 0.83
Nodes (4): Dashboard active vehicle log snapshot, Elapsed minutes calculation, Remaining minutes estimate, Status color calculation

### Community 53 - "Applicable Processes Register"
Cohesion: 0.50
Nodes (4): get_applicable_processes(), Return the repair processes applicable to a vehicle based on crash severity., Register a new vehicle and immediately check it into Vehicle Reception.      T, register_vehicle()

### Community 54 - "Main Window Application"
Cohesion: 0.50
Nodes (3): PlaceholderWidget, RES — ui/main_window.py ========================= Application main window and, A simple centered message for features still under development.

## Ambiguous Edges - Review These
- `List pending findings for insurer` → `Findings service pending insurer wrapper`  [AMBIGUOUS]
  services/findings_service.py · relation: calls
- `PythonDev Agent File` → `Contract Update Rule`  [AMBIGUOUS]
  .github/agents/PythonDev.agent.md · relation: conceptually_related_to
- `Rear Vehicle View Illustration` → `No Visible Rear Damage State`  [AMBIGUOUS]
  cost_estimator/db_example/Back.png · relation: conceptually_related_to
- `No Obvious Front Exterior Damage Visible` → `Stylized Render Rather Than Real Inspection Photo`  [AMBIGUOUS]
  cost_estimator/db_example/Front.png · relation: conceptually_related_to
- `Cost Estimator Front Inspection Input` → `Stylized Render Rather Than Real Inspection Photo`  [AMBIGUOUS]
  cost_estimator/db_example/Front.png · relation: conceptually_related_to
- `Orange Sedan Left-Side Profile Image` → `Ambiguous Exact Vehicle Make or Model`  [AMBIGUOUS]
  cost_estimator/db_example/Left.png · relation: conceptually_related_to
- `No Obvious Visible Damage` → `Stylized Render Limits Fine Damage Inspection`  [AMBIGUOUS]
  cost_estimator/db_example/Left.png · relation: conceptually_related_to
- `Right Side Reference View` → `Vehicle Direction or Side Naming Ambiguous`  [AMBIGUOUS]
  cost_estimator/db_example/Right.png · relation: conceptually_related_to
- `Dark Glass Areas` → `Central Black Panel`  [AMBIGUOUS]
  cost_estimator/db_example/Top.png · relation: conceptually_related_to

## Knowledge Gaps
- **87 isolated node(s):** `name`, `dockerfile`, `context`, `python.defaultInterpreterPath`, `python.testing.pytestEnabled` (+82 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `List pending findings for insurer` and `Findings service pending insurer wrapper`?**
  _Edge tagged AMBIGUOUS (relation: calls) - confidence is low._
- **What is the exact relationship between `PythonDev Agent File` and `Contract Update Rule`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Rear Vehicle View Illustration` and `No Visible Rear Damage State`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `No Obvious Front Exterior Damage Visible` and `Stylized Render Rather Than Real Inspection Photo`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Cost Estimator Front Inspection Input` and `Stylized Render Rather Than Real Inspection Photo`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Orange Sedan Left-Side Profile Image` and `Ambiguous Exact Vehicle Make or Model`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `No Obvious Visible Damage` and `Stylized Render Limits Fine Damage Inspection`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._