
## Wealthbox Docs
`https://www.wealthbox.com/api/`

`https://dev.wealthbox.com`

`https://dev.wealthbox.com/?_gl=1*u407x6*_gcl_aw*R0NMLjE3NzE5NjQwODEuQ2owS0NRaUF0ZlhNQmhEekFSSXNBSjBqcDNEVDA3QVBmOGd2Q205N01VZXQ4MXMtZ0o2ZlRrdDgtUlF6OUhwSHRtekJWOUhVcnU0WkduY2FBdDdTRUFMd193Y0I.*_gcl_au*OTk4NDQyNDQzLjE3NzEwMDU2ODE.`


## Examples

### Health
    wbox me
    wbox users
    wbox activity

### Contacts
    wbox contacts list

### Households
    wbox households add-member <household_id> --member-id <person_contact_id> --title "[Head|Spouse|Parent|Other Dependent|Child|Sibling|Partner|Grandchild|Grandparent]"
    wbox households remove-member <household_id> --member-id <person_contact_id>

### Tasks
    wbox tasks categories

    wbox tasks create '{"name": "Test Task 2", "frame": "today", "linked_to": [{"id": 30776510, "type": "Contact"}]}'
    wbox tasks get 79960846
    wbox tasks update 79960846 '{"name": "Test Task 2", "frame": "tomorrow", "description": "Testing adding a description"}'
    wbox tasks delete 79960846

#### wbox tasks list 
    ```
    --resource-id
    --resource-type
    --assigned-to
    --assigned-to-team
    --created-by
    --completed
    --task-type
    --updated-since
    --updated-before
    ```

    wbox tasks create
    wbox tasks update
    wbox tasks delete

### Events
wbox events categories

#### wbox events list
--resource-id
--resource-type
--start-date-min
--start-date-max
--order [asc|desc|recent|created]
--updated-since
--updated-before

wbox events create '{"title": "Test Event", "starts_at": "2026-02-27 11:00 AM -0700", "ends_at": "2026-02-27 12:00 PM -0700", "linked_to": [{"id": 30776510, "type": "Contact"}], "invitees": [{"id": 152760, "type": "User"}]}'
wbox events get 89801882
wbox events update 89801882 '{"state": "confirmed", "location": "test location"}'
wbox events delete 89801882



### Notes
    wbox notes create '{"content": "Test note", "linked_to": [{"id": 30776510, "type": "Contact"}]}'
    wbox notes get 240034639
    wbox notes update 240034639 '{"content": "Updated test note"}'
    Deleting notes is not supported via v1 API


#### wbox notes list
    --resource-id
    --resource-type
    --order
    --updated-since
    --updated-before


### Categories
    wbox categories [tags|file-categories|opportunity-stages|opportunity-pipelines|investment-objectives|financial-account-types]


### Custom Fields
    wbox categories custom-fields
    wbox categories custom-fields --document-type [Contact|Opportunity|Project|Task|Event|ManualInvestmentAccount|DataFile]