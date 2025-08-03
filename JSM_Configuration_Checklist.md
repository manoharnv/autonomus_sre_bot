# JSM Configuration Checklist
## Manual Setup Steps for Autonomous SRE Workflow

Use this checklist to manually configure your JSM project with the simplified 7-state workflow.

## Prerequisites ✅

- [ ] JIRA Service Management project access
- [ ] Project administrator permissions
- [ ] API token generated for automation user

## Phase 1: User Setup

### 1.1 Create SRE Bot User
- [ ] Go to **User Management** → **Users**
- [ ] Click **Create User**
- [ ] Fill in details:
  - Email: `sre-bot@yourcompany.com`
  - Display Name: `Autonomous SRE Bot`  
  - Username: `sre-bot`
- [ ] Grant permissions:
  - [ ] **Browse Projects**
  - [ ] **Create Issues**
  - [ ] **Edit Issues**
  - [ ] **Transition Issues**
  - [ ] **Add Comments**
  - [ ] **Manage Watchers**

### 1.2 Generate API Token
- [ ] Login as SRE bot user
- [ ] Go to **Account Settings** → **Security**
- [ ] Click **Create and manage API tokens**
- [ ] Create token: `Autonomous SRE Integration`
- [ ] Save token securely for bot configuration

## Phase 2: Custom Fields

### 2.1 Create Custom Fields
Navigate to **Project Settings** → **Custom Fields** and create:

#### Root Cause Analysis Field
- [ ] Click **Create Custom Field**
- [ ] Type: **Text Area (multi-line)**
- [ ] Name: `Root Cause Analysis`
- [ ] Description: `Detailed root cause analysis results from SRE bot`
- [ ] Context: Apply to incident issue types
- [ ] Required for: RCA Completed status

#### Pull Request URLs Field  
- [ ] Type: **Text Area (multi-line)**
- [ ] Name: `Pull Request URLs`
- [ ] Description: `Links to generated pull requests with fixes`
- [ ] Context: Apply to incident issue types
- [ ] Required for: Code Fix Completed status

#### Deployment Details Field
- [ ] Type: **Text Area (multi-line)**
- [ ] Name: `Deployment Details`
- [ ] Description: `Deployment execution details and results`
- [ ] Context: Apply to incident issue types
- [ ] Required for: Deployment Done status

#### Validation Results Field
- [ ] Type: **Text Area (multi-line)**
- [ ] Name: `Validation Results`
- [ ] Description: `Post-deployment validation and test results`
- [ ] Context: Apply to incident issue types
- [ ] Required for: Deployment Validated status

#### Automation Stage Field
- [ ] Type: **Select List (single choice)**
- [ ] Name: `Automation Stage`
- [ ] Description: `Current stage of SRE bot automation`
- [ ] Options: `Detection, Analysis, Fix Generation, Deployment, Validation, Complete, Failed`
- [ ] Default: `Detection`

#### SRE Bot Status Field
- [ ] Type: **Select List (single choice)**
- [ ] Name: `SRE Bot Status`
- [ ] Description: `Current status of SRE bot processing`
- [ ] Options: `Processing, Waiting, Error, Complete, Human Required`
- [ ] Default: `Processing`

#### Affected Systems Field
- [ ] Type: **Multi Select List**
- [ ] Name: `Affected Systems`
- [ ] Description: `Systems affected by this incident`
- [ ] Options: `Kubernetes Cluster, Database, API Gateway, Load Balancer, Monitoring, CI/CD Pipeline, Storage, Network`

## Phase 3: Workflow Statuses

### 3.1 Create Custom Statuses
Navigate to **Project Settings** → **Statuses** and create:

- [ ] **To Do** (Category: To Do)
  - Description: `New incidents waiting to be processed by SRE bot`
  
- [ ] **In Progress** (Category: In Progress)  
  - Description: `Incident is being actively processed by SRE bot`
  
- [ ] **RCA Completed** (Category: In Progress)
  - Description: `Root cause analysis has been completed`
  
- [ ] **Code Fix Completed** (Category: In Progress)
  - Description: `Code fixes have been generated and PR created`
  
- [ ] **Deployment Done** (Category: In Progress)
  - Description: `Fixes have been deployed to production`
  
- [ ] **Deployment Validated** (Category: In Progress)
  - Description: `Deployment has been validated and tested`
  
- [ ] **Done** (Category: Done)
  - Description: `Incident fully resolved and validated`
  
- [ ] **Needs Human Intervention** (Category: In Progress)
  - Description: `Automation failed, human intervention required`

## Phase 4: Workflow Configuration

### 4.1 Edit Incident Workflow
- [ ] Go to **Project Settings** → **Workflows**
- [ ] Find incident workflow and click **Edit**
- [ ] Add created statuses to workflow
- [ ] Configure transitions as per the workflow diagram

### 4.2 Configure Transitions

#### From "To Do":
- [ ] **Start Processing** → In Progress
  - Condition: None (allow SRE bot)
  - Post-function: Assign to sre-bot, Add comment
- [ ] **Escalate to Human** → Needs Human Intervention
  - Condition: None
  - Post-function: Unassign, Add comment

#### From "In Progress":
- [ ] **Complete RCA** → RCA Completed
  - Validator: Require "Root Cause Analysis" field
  - Post-function: Add comment
- [ ] **Escalate to Human** → Needs Human Intervention

#### From "RCA Completed":
- [ ] **Generate Fixes** → Code Fix Completed
  - Validator: Require "Pull Request URLs" field
  - Post-function: Add comment
- [ ] **Escalate to Human** → Needs Human Intervention

#### From "Code Fix Completed":
- [ ] **Deploy Fixes** → Deployment Done
  - Validator: Require "Deployment Details" field
  - Post-function: Add comment
- [ ] **Escalate to Human** → Needs Human Intervention

#### From "Deployment Done":
- [ ] **Validate Deployment** → Deployment Validated
  - Validator: Require "Validation Results" field
  - Post-function: Add comment
- [ ] **Escalate to Human** → Needs Human Intervention

#### From "Deployment Validated":
- [ ] **Resolve Incident** → Done
  - Post-function: Set resolution to "Fixed", Add comment

#### From "Needs Human Intervention":
- [ ] **Resume Automation** → In Progress
  - Post-function: Assign to sre-bot, Add comment
- [ ] **Manual Resolution** → Done
  - Post-function: Set resolution to "Fixed", Add comment

### 4.3 Publish Workflow
- [ ] Save workflow changes
- [ ] Publish workflow to make it active
- [ ] Test workflow transitions

## Phase 5: Screen Configuration

### 5.1 Configure Screens for Each Status
Create or modify screens to show relevant fields:

#### "To Do" Screen:
- [ ] Summary, Description, Priority, Components, Labels
- [ ] Automation Stage, SRE Bot Status

#### "In Progress" Screen:
- [ ] All above fields + Assignee, Progress comments
- [ ] Affected Systems

#### "RCA Completed" Screen:
- [ ] Root Cause Analysis field (required)
- [ ] Technical Details, Affected Systems

#### "Code Fix Completed" Screen:
- [ ] Pull Request URLs field (required)
- [ ] Fix Description, Code Changes Summary

#### "Deployment Done" Screen:
- [ ] Deployment Details field (required)
- [ ] Deployment Time, Environment

#### "Deployment Validated" Screen:
- [ ] Validation Results field (required)
- [ ] Test Results, Performance Impact

## Phase 6: Notifications

### 6.1 Configure Email Templates
- [ ] **Incident Started**: Notify stakeholders when automation begins
- [ ] **RCA Complete**: Share root cause analysis results
- [ ] **Fix Generated**: Notify about code fixes and PRs
- [ ] **Deployment Complete**: Confirm deployment success
- [ ] **Resolution Complete**: Final resolution notification
- [ ] **Human Intervention Required**: Escalation notification

### 6.2 Set Up Notification Schemes
For each transition, configure appropriate notifications to:
- [ ] Stakeholders group
- [ ] SRE team group
- [ ] Development team group
- [ ] Operations team group
- [ ] Reporter

## Phase 7: SLA Configuration

### 7.1 Create SLA Configuration
- [ ] Go to **Project Settings** → **SLA**
- [ ] Create new SLA: `Autonomous SRE Resolution Time`

#### SLA Targets:
- [ ] To Do → In Progress: **5 minutes** (Warning: 3 minutes)
- [ ] In Progress → RCA Completed: **15 minutes** (Warning: 10 minutes)
- [ ] RCA Completed → Code Fix Completed: **20 minutes** (Warning: 15 minutes)
- [ ] Code Fix Completed → Deployment Done: **10 minutes** (Warning: 7 minutes)
- [ ] Deployment Done → Deployment Validated: **10 minutes** (Warning: 7 minutes)
- [ ] Deployment Validated → Done: **5 minutes** (Warning: 3 minutes)

## Phase 8: Webhook Configuration

### 8.1 Set Up Webhooks
- [ ] Go to **System** → **WebHooks**
- [ ] Create webhook: `SRE Bot Notification`
- [ ] URL: `https://your-sre-bot.company.com/webhook/jsm`
- [ ] Events: Issue Created, Issue Updated, Issue Transitioned
- [ ] Filter by project: Your incident project

## Phase 9: Testing

### 9.1 Workflow Testing
- [ ] Create test incident
- [ ] Verify it starts in "To Do" status
- [ ] Test each transition manually:
  - [ ] To Do → In Progress
  - [ ] In Progress → RCA Completed (with required field)
  - [ ] RCA Completed → Code Fix Completed (with required field)
  - [ ] Code Fix Completed → Deployment Done (with required field)
  - [ ] Deployment Done → Deployment Validated (with required field)
  - [ ] Deployment Validated → Done
- [ ] Test escalation paths to "Needs Human Intervention"
- [ ] Test resume automation from human intervention

### 9.2 Automation Testing
- [ ] Test SRE bot API access with created user
- [ ] Verify webhook is receiving events
- [ ] Test automated transitions via API
- [ ] Verify field updates are working
- [ ] Check notification delivery

### 9.3 SLA Testing
- [ ] Create incidents and monitor SLA tracking
- [ ] Verify warning thresholds trigger correctly
- [ ] Test SLA reporting and dashboards

## Phase 10: Documentation

### 10.1 Create Documentation
- [ ] Workflow diagram with all states and transitions
- [ ] User guide for manual intervention scenarios
- [ ] Troubleshooting guide for common issues
- [ ] API documentation for SRE bot integration

### 10.2 Training
- [ ] Train SRE team on new workflow
- [ ] Train support team on escalation procedures
- [ ] Train stakeholders on status meanings

## Final Verification ✅

- [ ] All custom fields created and configured
- [ ] All workflow statuses created
- [ ] All transitions configured with proper conditions
- [ ] All screens configured with appropriate fields
- [ ] SRE bot user has necessary permissions
- [ ] Webhooks are configured and firing
- [ ] SLA tracking is active
- [ ] Notifications are being sent
- [ ] Test incidents flow through entire workflow
- [ ] Documentation is complete and accessible

## Troubleshooting Common Issues

### Field Not Showing on Screen
- Check field context configuration
- Verify screen scheme is applied to issue type
- Ensure field is added to appropriate screen tab

### Transition Not Available
- Check workflow permissions and conditions
- Verify user has appropriate role/permissions
- Check if validators are preventing transition

### Webhook Not Firing
- Verify webhook URL is accessible
- Check webhook event configuration
- Review JIRA webhook logs for errors

### SLA Not Tracking
- Ensure SLA is active and published
- Check SLA condition configuration
- Verify time-based conditions are correct

---

**Note**: This checklist covers manual configuration. For automated setup, use the provided Python script `configure_jsm_workflow.py` with your JIRA API credentials.
