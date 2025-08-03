# How to Activate Your JSM Workflow

## Step-by-Step Guide to Publish/Activate Your Workflow

### 1. Access Workflow Management
1. Go to your JIRA Service Management project
2. Navigate to **Project Settings** (gear icon in left sidebar)
3. Click on **Workflows** in the left menu

### 2. Locate Your Workflow
1. You should see your "Autonomous SRE Incident Resolution Workflow" in the list
2. It will show status as "Inactive" or "Draft"
3. Click on your workflow name to open it

### 3. Publish the Workflow
1. In the workflow editor, look for a **"Publish"** button (usually top-right)
2. Click **"Publish"** or **"Publish Draft"**
3. JIRA will show a confirmation dialog with:
   - Summary of changes
   - Impact on existing issues
   - Backup information

### 4. Review and Confirm
1. Review the changes summary
2. **Important**: JIRA will ask how to handle existing issues:
   - **"Keep current status"** - Recommended for existing incidents
   - **"Map to new status"** - If you want to migrate existing issues
3. Click **"Publish"** to confirm

### 5. Associate with Issue Types
After publishing, you need to associate the workflow with your issue types:

1. Still in **Project Settings** → **Workflows**
2. Look for **"Workflow Schemes"** or **"Issue Type Workflow Scheme"**
3. Click **"Edit"** on your project's workflow scheme
4. For each relevant issue type (Incident, Service Request, etc.):
   - Click **"Edit"** next to the issue type
   - Select your new workflow: "Autonomous SRE Incident Resolution Workflow"
   - Click **"Update"**
5. Click **"Publish Scheme"** to activate the changes

## Alternative: Command Line Approach

If you have JIRA CLI tools installed, you can also activate via API:

```bash
# Check workflow status
curl -X GET \
  -H "Authorization: Basic $(echo -n 'your-email:your-api-token' | base64)" \
  -H "Content-Type: application/json" \
  "https://yourcompany.atlassian.net/rest/api/3/workflow/search?workflowName=Autonomous%20SRE%20Incident%20Resolution%20Workflow"

# Publish workflow (requires workflow ID)
curl -X POST \
  -H "Authorization: Basic $(echo -n 'your-email:your-api-token' | base64)" \
  -H "Content-Type: application/json" \
  "https://yourcompany.atlassian.net/rest/api/3/workflow/transitions/{workflow-id}/publish"
```

## Troubleshooting Common Issues

### Issue: "Publish" Button Not Visible
**Solution**: You may need administrator permissions
- Ensure you have "JIRA Administrators" or "Project Administrator" role
- Contact your JIRA admin if you don't have permissions

### Issue: "Workflow is already active" Error
**Solution**: Check if it's already published but not associated with issue types
- Go to Workflow Schemes and verify issue type associations

### Issue: Existing Issues Show Errors
**Solution**: Map old statuses to new ones during publish
- JIRA will prompt you to map incompatible statuses
- Choose appropriate mappings or keep existing statuses

### Issue: Workflow Changes Don't Apply to New Issues
**Solution**: Verify workflow scheme association
- Check that your issue types are using the new workflow
- Publish the workflow scheme after making changes

## Verification Steps

After activation, verify everything is working:

### 1. Create Test Issue
1. Create a new incident in your project
2. Verify it starts in "To Do" status
3. Check that all custom fields are visible

### 2. Test Transitions
1. Try transitioning through each status manually
2. Verify required fields are enforced
3. Check that comments are added automatically

### 3. Check API Access
```bash
# Test API access to your project
curl -X GET \
  -H "Authorization: Basic $(echo -n 'sre-bot-email:api-token' | base64)" \
  "https://yourcompany.atlassian.net/rest/api/3/project/YOUR_PROJECT_KEY/statuses"
```

### 4. Verify SRE Bot Integration
1. Test that your SRE bot can access the new statuses
2. Verify webhook notifications are working
3. Check that state transitions via API work correctly

## Next Steps After Activation

1. **Test the Full Workflow**: Create test incidents and run them through the complete lifecycle
2. **Update SRE Bot Configuration**: Point your bot to use the new workflow
3. **Train Your Team**: Brief stakeholders on the new simplified states
4. **Monitor Performance**: Watch SLA metrics and adjust if needed

Let me know if you encounter any specific errors during the publishing process!
