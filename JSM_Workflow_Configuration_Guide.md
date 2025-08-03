# JSM Workflow Configuration Guide
## Simplified 7-State Autonomous SRE Workflow

This guide will help you configure the simplified workflow states in JIRA Service Management (JSM) to support the autonomous SRE bot's incident resolution process.

## Overview

The simplified workflow follows this linear progression:
```
TODO → In Progress → RCA Completed → Code Fix Completed → Deployment Done → Deployment Validated → Resolved
```

## JSM Workflow Configuration Steps

### 1. Access Workflow Configuration

1. Go to your JSM project
2. Navigate to **Project Settings** → **Workflows**
3. Find your incident workflow (usually the default Service Management workflow)
4. Click **Edit** to modify the workflow

### 2. Create Required Statuses

You need to create these custom statuses in JSM:

#### Status Configurations:

| Status Name | Status Category | Description |
|-------------|----------------|-------------|
| **To Do** | To Do | New incidents waiting to be processed |
| **In Progress** | In Progress | Incident is being actively worked on |
| **RCA Completed** | In Progress | Root cause analysis has been completed |
| **Code Fix Completed** | In Progress | Code fixes have been generated and PR created |
| **Deployment Done** | In Progress | Fixes have been deployed to production |
| **Deployment Validated** | In Progress | Deployment has been validated and tested |
| **Done** | Done | Incident fully resolved and validated |

#### Steps to Create Statuses:

1. In workflow editor, click **Add Status**
2. For each status above:
   - Enter the **Status Name**
   - Select the appropriate **Status Category**
   - Add the **Description**
   - Click **Add**

### 3. Configure Status Transitions

Set up these transitions between statuses:

#### From "To Do":
- → **In Progress** (when SRE bot starts processing)
- → **Needs Human Intervention** (if automation fails)

#### From "In Progress":
- → **RCA Completed** (when root cause analysis is done)
- → **Needs Human Intervention** (if analysis fails)

#### From "RCA Completed":
- → **Code Fix Completed** (when fixes are generated)
- → **Needs Human Intervention** (if fix generation fails)

#### From "Code Fix Completed":
- → **Deployment Done** (when deployment completes)
- → **Needs Human Intervention** (if deployment fails)

#### From "Deployment Done":
- → **Deployment Validated** (when validation passes)
- → **Needs Human Intervention** (if validation fails)

#### From "Deployment Validated":
- → **Done** (incident fully resolved)

#### From "Needs Human Intervention":
- → **In Progress** (when human fixes issue and resumes automation)
- → **Done** (when human resolves manually)

### 4. Transition Configuration Steps

For each transition:
1. Click **Add Transition**
2. Set **From Status** and **To Status**
3. Name the transition appropriately:
   - "Start Processing"
   - "Complete RCA"
   - "Generate Fixes"
   - "Deploy Fixes"
   - "Validate Deployment"
   - "Resolve Incident"
   - "Escalate to Human"
   - "Resume Automation"

### 5. Workflow Properties

Configure these workflow properties:

#### Transition Conditions:
- Most transitions should be **unrestricted** for the SRE bot
- Add **permission conditions** if you want to restrict who can perform certain transitions

#### Post Functions:
- **Assign Issue** (to SRE bot user for automated transitions)
- **Update Issue** (to add comments about automation progress)
- **Fire Event** (to trigger notifications)

### 6. Configure Automation User

Create a dedicated user for the SRE bot:

1. Go to **User Management**
2. Create user: `sre-bot@yourcompany.com`
3. Assign to project with appropriate permissions:
   - **Browse Projects**
   - **Create Issues**
   - **Edit Issues**
   - **Transition Issues**
   - **Add Comments**

### 7. Screen Configuration

Configure screens for each status to show relevant fields:

#### "To Do" Screen:
- Summary
- Description
- Priority
- Components
- Labels

#### "In Progress" Screen:
- All above fields
- Assignee
- Progress comments

#### "RCA Completed" Screen:
- Root Cause Analysis field
- Technical Details
- Affected Systems

#### "Code Fix Completed" Screen:
- Pull Request Links
- Fix Description
- Code Changes Summary

#### "Deployment Done" Screen:
- Deployment Details
- Deployment Time
- Environment

#### "Deployment Validated" Screen:
- Validation Results
- Test Results
- Performance Impact

### 8. Field Configuration

Create custom fields for automation tracking:

#### Custom Fields to Add:

1. **Root Cause Analysis** (Multi-line text)
   - Description: "Detailed root cause analysis results"
   - Required for: RCA Completed status

2. **Pull Request URLs** (Multi-line text)
   - Description: "Links to generated pull requests"
   - Required for: Code Fix Completed status

3. **Deployment Details** (Multi-line text)
   - Description: "Deployment execution details"
   - Required for: Deployment Done status

4. **Validation Results** (Multi-line text)
   - Description: "Post-deployment validation results"
   - Required for: Deployment Validated status

5. **Automation Stage** (Select List)
   - Options: "Detection", "Analysis", "Fix Generation", "Deployment", "Validation", "Complete"
   - Default: "Detection"

6. **SRE Bot Status** (Select List)
   - Options: "Processing", "Waiting", "Error", "Complete", "Human Required"
   - Default: "Processing"

### 9. Notification Configuration

Set up notifications for each transition:

#### Email Templates:
- **Incident Started**: Notify stakeholders when automation begins
- **RCA Complete**: Share root cause analysis results
- **Fix Generated**: Notify about code fixes and PRs
- **Deployment Complete**: Confirm deployment success
- **Resolution Complete**: Final resolution notification
- **Human Intervention Required**: Escalation notification

### 10. SLA Configuration

Configure SLAs for each state:

| Status | Target Time | Warning Time |
|--------|-------------|--------------|
| To Do → In Progress | 5 minutes | 3 minutes |
| In Progress → RCA Completed | 15 minutes | 10 minutes |
| RCA Completed → Code Fix Completed | 20 minutes | 15 minutes |
| Code Fix Completed → Deployment Done | 10 minutes | 7 minutes |
| Deployment Done → Deployment Validated | 10 minutes | 7 minutes |
| Deployment Validated → Done | 5 minutes | 3 minutes |

## JSM API Configuration

### Webhook Configuration

Set up webhooks to notify the SRE bot of state changes:

1. Go to **System** → **WebHooks**
2. Create webhook: "SRE Bot Notification"
3. URL: `https://your-sre-bot.company.com/webhook/jsm`
4. Events: 
   - Issue Created
   - Issue Updated
   - Issue Transitioned

### REST API Permissions

Ensure the SRE bot user has API access:
1. Grant **REST API access**
2. Configure **API token** for authentication
3. Test API connectivity

## Validation Checklist

After configuration, verify:

- [ ] All 7 workflow states are created
- [ ] Transitions flow correctly in sequence
- [ ] SRE bot user can perform all transitions
- [ ] Custom fields are visible in appropriate screens
- [ ] Notifications are configured and working
- [ ] SLAs are set up and tracking
- [ ] Webhooks are firing correctly
- [ ] API access is working

## Troubleshooting

### Common Issues:

1. **Missing Status**: Check if all custom statuses are created and published
2. **Transition Blocked**: Verify permissions and workflow conditions
3. **API Errors**: Check user permissions and API token validity
4. **Notifications Not Sending**: Verify email templates and recipient configuration

### Testing the Workflow:

1. Create a test incident
2. Verify it starts in "To Do" status
3. Use the SRE bot to transition through each state
4. Confirm all fields, notifications, and SLAs work correctly

## Configuration Export/Import

### Export Current Workflow:
```bash
# Use JSM backup or workflow export feature
# Save configuration for version control
```

### Import to Other Projects:
```bash
# Use JSM workflow import feature
# Adapt field mappings as needed
```

This configuration will enable your JSM project to work seamlessly with the simplified autonomous SRE bot workflow!
