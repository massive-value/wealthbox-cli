# firm/workflows.md — Example

## Common Templates
- New Client Onboarding: template ID 500
- Annual Review Prep: template ID 501
- Account Transfer: template ID 502

## Named Workflows

### Onboarding
When the advisor says to "onboard" a client:
1. Create person contact with required fields
2. Create household if married — add both spouses
3. Add intake note with meeting summary (ask advisor)
4. Create tasks from templates: Welcome call, Collect documents, Open accounts, Schedule review
5. Create opportunity linked to contact with firm defaults
6. Start workflow using template 500, linked to contact

### Meeting Followup
After a client meeting:
1. Add note with meeting summary, linked to contact
2. Create tasks for action items (ask advisor to list them)
3. Update opportunity if pipeline status changed

### Annual Review
1. Create event for review meeting
2. Start workflow using template 501
3. Add note with review agenda or outcomes

## Other Conventions
(populated during first-run bootstrap Step 3)
