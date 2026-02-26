from __future__ import annotations

from typing import Literal


# Strict enum types — values fixed by Wealthbox, not configurable per account
RecordTypeOptions = Literal["Person", "Household", "Organization", "Trust"]
GenderOptions = Literal["Female", "Male", "Non-binary", "Unknown"]
MaritalStatusOptions = Literal["Married", "Single", "Divorced", "Widowed", "Life Partner", "Separated", "Unknown"]
TaskFrameOptions = Literal[ "today", "tomorrow", "this_week", "next_week", "future", "specific" ]
DocumentTypeOptions = Literal[ "Contact", "Opportunity", "Project", "Task", "Event", "ManualInvestmentAccount", "DataFile" ]
HouseholdTitleOptions = Literal[ "Head", "Spouse", "Parent", "Other Dependent", "Child", "Sibling", "Partner", "Grandchild", "Grandparent" ]


ContactsOrderOptions = Literal[ "asc", "desc", "recent", "created", "updated" ]
EventsOrderOptions = Literal[ "asc", "desc", "recent", "created" ]


## SWA Specific
ContactTypeOptions = Literal[ "401(k) Participant", "Center of Influence", "Client", "External (Non-Client)", "Flourish Only", "Lead", "Prospect"]
ContactSourceOptions = Literal["Call In", "Client Referral", "COI Referral", "Conference", "Events/Seminars", "Friend/Family of Advisor", "Lead Gen Service", "Merger/Acquisition", "Other Digital Media", "Person or Spouse is an Employee", "Squire Referral", "Website"]
EmailKindOptions = Literal[ "No Longer Used", "Other", "Personal", "Work" ]
PhoneKindOptions = Literal[ "Fax", "Home", "Mobile", "Other", "Work" ]
AddressKindOptions = Literal[ "Home", "Other", "Place of Business", "PO Box", "Second Home" ]