# firm/contacts.md — Example

This is an illustrative template. Replace every value below with your firm's
real conventions. Valid category values (contact types, sources, roles, etc.)
come from your workspace — list them with `wbox contacts categories <type>`.

## Required Fields
- contact-type: one of your workspace's contact types (`wbox contacts categories contact-types`)
- contact-source: one of your workspace's sources (`wbox contacts categories contact-sources`)

## Defaults
- assigned-to: <your default user id> (`wbox me user-id`)
- active: true

## Advisor / Contact Roles
- If your firm assigns advisors via contact roles (e.g. "Associate Advisor",
  "Partner"), set them with `--advisor-role "Role:User"` on add/update.
- List the configured roles and their assignable users with
  `wbox contacts categories contact-roles`.
- Example: a prospect's primary advisor is `--assigned-to`, and the second
  advisor is `--advisor-role "Associate Advisor:<user>"`.

## Person Contacts
- Always collect: email, phone, birth-date
- Preferred email-type: Personal
- Preferred phone-type: Mobile

## Household Contacts
- Always create a household when onboarding a married couple
- Naming convention: e.g. "{Last}, {Head First} & {Spouse First}"
- Add members one at a time (sequential) — see references/households.md

## Organization / Trust Contacts
- Require EIN in --more-fields for Trusts
