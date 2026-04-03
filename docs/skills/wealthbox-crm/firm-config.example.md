# Firm Configuration — [Your Firm Name]

<!--
This file customizes the /wealthbox-crm skill for your firm's conventions.
Copy this template and fill in your firm's requirements.
Delete any sections that don't apply.
-->

## Contacts

### Required Fields
<!-- Fields that MUST be provided when creating any contact -->
- contact-type: [e.g., always one of: Client, Prospect, Center of Influence, Vendor]
- contact-source: [e.g., always one of: Referral, Website, Event, Cold Call]

### Defaults
<!-- Auto-applied unless overridden -->
- assigned-to: [user ID — e.g., 12345]
- active: true

### Person Contacts
<!-- Additional requirements for person contacts -->
- Always collect: [e.g., email, phone, birth-date]
- Preferred email-type: [e.g., Personal]
- Preferred phone-type: [e.g., Mobile]

### Household Contacts
<!-- When to create households -->
- [e.g., Always create a household when onboarding a married couple]
- Naming convention: [e.g., "The {LastName} Family" or "{Spouse1} & {Spouse2} {LastName}"]

### Organization / Trust Contacts
<!-- Firm-specific conventions -->

## Tasks

### Required Fields
- priority: [e.g., always set — default to Medium if not specified]

### Defaults
- assigned-to: [user ID or rule — e.g., "same as the linked contact's assigned-to"]
- frame: [e.g., default to "this-week" if no due date given]

### Common Task Templates
<!-- Named tasks your firm creates repeatedly -->
- "Welcome call": priority High, frame today, description "Call new client to welcome them"
- "Collect documents": priority Medium, frame this-week, description "Request IPS, tax returns, account statements"
- "Open accounts": priority Medium, frame next-week
- "Schedule review": priority Low, frame next-month

## Notes

### Conventions
- [e.g., Always prefix meeting notes with "Meeting Note — YYYY-MM-DD:"]
- [e.g., Always link notes to a contact, never create unlinked notes]

## Events

### Defaults
- state: [e.g., confirmed]
- [e.g., Default meeting duration: 1 hour]

### Conventions
- Naming: [e.g., "{Meeting Type} — {Contact Name}"]
- [e.g., Always link events to the primary contact]

## Opportunities

### Required Fields
- [e.g., stage, probability, and target-close are always required]

### Defaults
- currency: USD
- [e.g., Default probability: 50 for new prospects]

### Pipeline Conventions
- [e.g., Use pipeline "New Business" (ID: XXX) for prospects]
- [e.g., Stage IDs: Discovery=1, Proposal=2, Commitment=3, Onboarding=4]

## Workflows

### Common Templates
<!-- Workflow templates your firm uses, with their IDs -->
- New Client Onboarding: template ID [XXX]
- Annual Review Prep: template ID [XXX]
- Account Transfer: template ID [XXX]

## Named Workflows

### Onboarding
<!-- Multi-step workflow executed when the user says "onboard" a client -->
When onboarding a new client:
1. **Create contact** (person) with all required fields above
2. **Create household** if married — add both spouses, naming per convention above
3. **Add intake note** with meeting summary (ask user for details)
4. **Create tasks** from templates: "Welcome call", "Collect documents", "Open accounts", "Schedule review" — all linked to the new contact
5. **Create opportunity** linked to contact with firm defaults
6. **Start workflow** using "New Client Onboarding" template, linked to contact

### Meeting Followup
<!-- Executed when the user says they had a meeting with a client -->
After a client meeting:
1. **Add note** with meeting summary, linked to the contact
2. **Create tasks** for any action items discussed (ask user to list them)
3. **Update opportunity** if pipeline status changed

### Annual Review
<!-- Executed when the user says to prep or log an annual review -->
1. **Create event** for the review meeting
2. **Start workflow** using "Annual Review Prep" template
3. **Add note** with review agenda or outcomes
