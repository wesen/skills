---
name: odh-med-reorder
description: >
  Reorder medications through the Open Door Health (ODH) patient portal at odhpvd.org,
  powered by athenahealth. Use this skill whenever the user mentions refilling, reordering,
  or renewing their meds/medications/prescriptions at Open Door Health, ODH, or "pvd openhealth".
  Also trigger if they mention their athenahealth portal in the context of prescriptions.
---

# Open Door Health — Medication Reorder

This skill walks through requesting prescription renewals on the Open Door Health patient portal (athenahealth).

## Overview

Open Door Health (7 Central St, Providence, RI 02907) uses athenahealth for their patient portal at `https://20649.portal.athenahealth.com/`. The renewal flow sends a secure message to the provider requesting a refill. The portal says they reply within two business days.

## Prerequisites

- The user must have an existing Open Door Health patient account
- Browser automation tools (Claude in Chrome) must be available
- The user will need to log in themselves — never enter passwords on their behalf

## Defaults

- **Provider:** Antonio Reisopoulos, PA-C
- **Office location:** Open Door Health Main Office
- **Message:** "Hi, I would like to request a renewal for this medication. Thank you!"

These defaults can be overridden if the user asks, but use them unless told otherwise.

## Workflow

### 1. Navigate to the patient portal

Open a new browser tab and go to:
```
https://20649.portal.athenahealth.com/
```
If the user isn't logged in, tell them to log in and wait for confirmation.

### 2. Check login status and go to Medications

Once logged in, navigate to:
```
My Health → Health Summary → Medications
```
Direct URL: `https://20649.portal.athenahealth.com/?section=health&sub=health_summary#/medications`

The medications page lists all current prescriptions with "Request Renewal" buttons.

### 3. Ask which medications to renew

Show the user the list of their current medications and ask which ones they want to renew. Default behavior is to ask — don't assume "all" unless the user says so.

### 4. For each medication, submit a renewal request

Click "Request Renewal" for the medication. This opens the "Prescriptions and Renewals" message form.

**Important technical notes about this portal:**
- The form is a React/shadow DOM app. Standard DOM queries (`document.querySelectorAll('select')`) won't find the form elements directly.
- To interact with dropdowns and buttons, use this pattern to search through shadow DOM:

```javascript
// Finding elements in shadow DOM
function findInShadow(root, selector) {
  let results = [...root.querySelectorAll(selector)];
  root.querySelectorAll('*').forEach(el => {
    if (el.shadowRoot) {
      results = results.concat(findInShadow(el.shadowRoot, selector));
    }
  });
  return results;
}
```

#### Setting the Provider dropdown

The provider `<select>` element is inside a shadow DOM. Find it and set it programmatically:

```javascript
const selects = findInShadow(document, 'select');
// selects[0] = Provider/Care Team
// selects[1] = Office Location

// Antonio Reisopoulos, PA-C
selects[0].value = 'YS0yMDY0OS5Qcm92aWRlci0xM3w4dDUyWnpqNklFT3dhTXZBaGxoTDZYcHR3NkE9';
selects[0].dispatchEvent(new Event('change', {bubbles: true}));
```

**Note:** The provider option values are base64-encoded IDs. If they ever change (e.g., after a portal update), you'll need to enumerate the options and find the right one by text instead:

```javascript
for (const opt of selects[0].options) {
  if (opt.text.includes('Reisopoulos')) {
    selects[0].value = opt.value;
    selects[0].dispatchEvent(new Event('change', {bubbles: true}));
    break;
  }
}
```

#### Setting the Office Location dropdown

After setting the provider, wait briefly (the office dropdown populates dynamically), then set it:

```javascript
setTimeout(() => {
  const sels = findInShadow(document, 'select');
  if (sels[1] && sels[1].options.length > 1) {
    sels[1].value = sels[1].options[1].value; // "Open Door Health Main Office"
    sels[1].dispatchEvent(new Event('change', {bubbles: true}));
  }
}, 500);
```

#### Setting the Message textarea

The textarea is also in a shadow DOM. Use the native value setter to trigger React's change detection:

```javascript
const textareas = findInShadow(document, 'textarea');
const nativeSetter = Object.getOwnPropertyDescriptor(
  window.HTMLTextAreaElement.prototype, 'value'
).set;
nativeSetter.call(textareas[0],
  'Hi, I would like to request a renewal for this medication. Thank you!'
);
textareas[0].dispatchEvent(new Event('input', {bubbles: true}));
textareas[0].dispatchEvent(new Event('change', {bubbles: true}));
```

#### Clicking Send Message

The "Send Message" button is a `<span>` in a shadow DOM. Regular click coordinates often miss it. Use this approach:

```javascript
function searchShadow(root) {
  const els = root.querySelectorAll('*');
  for (const el of els) {
    if (el.shadowRoot) {
      const found = searchShadow(el.shadowRoot);
      if (found) return found;
    }
    if (el.textContent && el.textContent.trim() === 'Send Message'
        && el.children.length === 0) {
      const rect = el.getBoundingClientRect();
      if (rect.width > 0) return el;
    }
  }
  return null;
}

const sendSpan = searchShadow(document);
sendSpan.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
```

Wait for the page title to change to "Message sent success" to confirm.

### 5. Repeat for remaining medications

After each successful send, navigate back to the medications page and click "Request Renewal" for the next one:
```
https://20649.portal.athenahealth.com/?section=health&sub=health_summary#/medications
```

### 6. Summarize

After all renewals are submitted, tell the user:
- Which medications were renewed
- That the portal says they'll hear back within two business days
- Mention any other notable items from the dashboard (new messages, test results, health reminders) if you saw them during the process

## Troubleshooting

- **Dropdown won't open with clicks:** This portal's React components don't respond well to coordinate-based clicks. Always use the JavaScript/shadow DOM approach above.
- **"Provider is required" validation error:** The provider dropdown wasn't set properly. Re-run the JavaScript to set it.
- **Option values changed:** If the base64 provider IDs no longer work, enumerate options by text content instead of hardcoding values.
- **Login session expired:** If you get redirected to the login page mid-flow, ask the user to log in again.
