# JSM Workflow Activation - Troubleshooting Guide

## When You Can't Find the Publish Button

### Current Situation
- Workflow created: ✅ SRE_bot_workflow 
- Status: INACTIVE ❌
- Issue: Publish button not visible

### Solution Steps

#### Step 1: Check Current View Options
In your current workflow designer view, look for:

1. **Top-right corner**: 
   - "Publish Draft" button
   - "Actions" dropdown
   - "..." (three dots) menu

2. **Top menu bar**:
   - "Workflow" menu
   - "Tools" menu
   - Any "Publish" option in menus

3. **Right-click context menu**:
   - Right-click anywhere on the workflow diagram
   - Look for "Publish" or "Activate" options

#### Step 2: Navigate to Workflow List
1. Click **"Workflows"** in the left sidebar
2. Find `SRE_bot_workflow` in the list
3. Look for action buttons next to the workflow name:
   - "Publish" button
   - "Activate" button  
   - Dropdown menu with publish options

#### Step 3: Use Workflow Schemes (Recommended)
This is often the most reliable method:

1. **Go to Workflow Schemes**:
   - Left sidebar → "Workflow schemes"
   - Find your project's workflow scheme

2. **Edit the Scheme**:
   - Click "Edit" next to your project's scheme
   - You'll see issue types and their workflows

3. **Associate Your Workflow**:
   - For "Incident" issue type: Click "Edit"
   - Change workflow to "SRE_bot_workflow"
   - Click "Update"

4. **Publish the Scheme**:
   - Click "Publish Scheme" 
   - This activates your workflow

#### Step 4: Alternative - Copy Active Workflow
If publish still doesn't work:

1. **Create from Active Workflow**:
   - Go to Workflows list
   - Find an active workflow (like the default)
   - Click "Copy" 
   - Name it "SRE_bot_workflow_v2"
   - Edit the copy to add your statuses and transitions
   - This new workflow should be publishable

### Verification Steps

After activation:

1. **Check Status**: Workflow should show "ACTIVE" instead of "INACTIVE"

2. **Test with New Issue**:
   - Create a new incident
   - Verify it uses your new workflow states
   - Check that "To Do" is the initial status

3. **Verify Transitions**:
   - Try transitioning through: To Do → In Progress → RCA Completed
   - Confirm all your custom statuses are available

### Common Issues & Solutions

#### Issue: "Workflow in use" Error
**Solution**: 
- JIRA might say the workflow is in use even if inactive
- Use the workflow scheme method (Step 3) instead

#### Issue: No Publish Option Anywhere
**Solution**:
- Check your permissions - you need "JIRA Administrators" role
- Contact your JIRA admin if you don't have sufficient permissions

#### Issue: Publish Succeeds but Workflow Still Inactive
**Solution**:
- The workflow might be published but not associated with issue types
- Go to Workflow Schemes and associate it with your issue types

### Permission Requirements

To publish workflows, you need:
- **JIRA Administrators** global permission, OR
- **Project Administrator** permission for the specific project
- **Browse Projects** permission

### Next Steps After Activation

1. **Update Project Settings**: Ensure all relevant issue types use the new workflow
2. **Test SRE Bot Integration**: Verify API access to new statuses  
3. **Configure Notifications**: Set up alerts for status transitions
4. **Train Team**: Brief stakeholders on new simplified states

### Still Having Issues?

If you still can't find the publish option:

1. **Check JIRA Version**: Some older versions have different UI
2. **Contact JIRA Admin**: They might need to publish it for you
3. **Use JIRA Support**: Check Atlassian documentation for your specific version

The workflow scheme method (Step 3) is usually the most reliable approach when the direct publish button isn't visible.
