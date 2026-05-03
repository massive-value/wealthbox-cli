# firm/contacts.md — Example

## Required Fields
- contact-type: always one of: Client, Prospect, Center of Influence, Vendor
- contact-source: always one of: Referral, Website, Event, Cold Call

## Defaults
- assigned-to: 12345
- active: true

## Person Contacts
- Always collect: email, phone, birth-date
- Preferred email-type: Personal
- Preferred phone-type: Mobile

## Household Contacts
- Always create a household when onboarding a married couple
- Naming convention: "The {LastName} Family"

## Organization / Trust Contacts
- Require EIN in more-fields for Trusts
