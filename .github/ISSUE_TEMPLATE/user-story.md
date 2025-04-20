---
name: 🧑‍💻 User Story
about: Describe a new functionality from a user perspective
title: "[User Story] Filter search results by category"
labels: user-story
assignees: ''
---

**As a** logged-in user  
**I need** to be able to filter search results by category  
**So that** I can quickly find relevant content without scrolling through everything  

---

### Details and Assumptions
- Categories are retrieved dynamically from an API
- A user can select one or more categories
- The filter must apply in real-time without a full page reload

---

### Acceptance Criteria

```gherkin
Given I am on the search page and logged in  
When I select one or more categories from the filter options  
Then only the results matching the selected categories should be displayed  
