# GOPELIA Intake Automation Blueprint (n8n & Gmail)

## Overview

This document outlines a practical automation blueprint for your new intake process using **n8n** and **Gmail**. It assumes you have set up the inboxes `estimates@gopelia.com` (for receiving all ITBs) and `intake@gopelia.com` (for qualification). The goal is to automate triage as far as possible so that the VA can focus on scoring and communication rather than manual sorting.

## Pre-requisites

1. **Gmail OAuth credentials** for n8n: you’ll need to connect n8n to the Gmail accounts for `estimates@` and `intake@`. When first invoked, the `Gmail Trigger` node will prompt for OAuth authorisation; ensure you are logged in and authorise n8n to access email and send on your behalf.
2. **Top GC list** stored in Google Sheets: create a simple sheet with GC domains in column `A` and labels (e.g., `Tier1`, `Tier2`) in column `B`. This will allow the workflow to cross-reference incoming senders.
3. **n8n credentials** for Google Sheets (if you plan to cross-reference) and Gmail.

## Workflow components

Here is a high-level outline of the nodes and logic you should create in n8n:

1. **Gmail Trigger (estimates@)**
   - Set to watch for new emails arriving in `estimates@gopelia.com`.
   - Filter: use Gmail search syntax in the trigger settings to only pull messages with subjects containing keywords like `ITB`, `Invitation to Bid`, `Bid Request`, or `RFP`.
   - Include attachments if needed (e.g., PDF plans for later extraction).

2. **Extract Sender & Subject (Code or Set node)**
   - Access the metadata returned by the trigger to get the sender’s email address, domain (`sender.split('@')[1]`), subject line, and snippet.

3. **Determine Category (Function node)**
   - **Check Small Works**: if the subject or body includes keywords such as `rail`, `handrail`, `punch list`, set `category = "Small Works"` and mark for auto-decline.
   - **Cross-reference Top GC List**: use a Google Sheets node to look up the sender’s domain. If found in the sheet, assign `category = "Top GC"`. If not found but the sender domain is from a known general contractor, assign `category = "Tier2"`. Otherwise, mark as `Cold`.
   - Store the result in a field `metadata.category`.

4. **Apply Labels & Forward (Gmail node)**
   - Use a Gmail node to apply a label based on `metadata.category` to the original email in `estimates@`. Example: label `ITB - Top GC`.
   - Forward the email to `intake@gopelia.com` with the same label. Include a short note in the forwarding message if desired (e.g., "Auto-forwarded for qualification").

5. **Optional: Auto-decline Small Works (Gmail node)**
   - If `category` is `Small Works` and the estimated scope is clearly under $100 k, send a polite decline email directly from `estimates@` (or `intake@`) thanking the sender and explaining that the scope does not align with current requirements. BCC your team for tracking.

6. **Log Entry (Google Sheets or Database node)**
   - Append a new row to a "Intake Log" sheet with columns such as `Received Date`, `Sender`, `Project`, `Category`, `Status`, `Score` (to be filled in by the VA later), and `Notes`. This provides visibility into pipeline composition and feed your KPIs.

7. **Notification (Slack, Trello, or Email)**
   - For `Top GC` and `Priority` categories, send a notification to the estimator or create a Trello card with the relevant details. Use n8n’s Slack, Trello, or internal email nodes to integrate with your tools.

## Implementation Steps in n8n

1. **Create a new workflow** in n8n and give it a descriptive name (e.g., `GOPELIA - Intake Automation`).
2. **Add the Gmail Trigger** node and authenticate with the `estimates@` account.
3. **Add a Function** node to parse the sender and subject and attach the domain.
4. **Add a Google Sheets Look-up** node pointing to your Top GC sheet. Configure it to search for the domain and return the GC tier.
5. **Add an IF** node (or multiple) to evaluate the category and branch accordingly (Small Works vs Top GC vs Tier2 vs Cold).
6. **On the appropriate branches**, add Gmail nodes to label and forward the email to `intake@` and/or send decline messages.
7. **Add logging** via Sheets or another datastore.
8. **Add notifications** for Top GC and Priority branches.
9. **Test the workflow** with sample emails before activating it.

## Notes & Best Practices

- **Fallback**: If the GC domain is not found in your list, treat it as `Cold` by default and have the VA manually review it.
- **Privacy & Security**: Ensure credentials are stored securely in n8n’s credential manager. Do not hard-code API keys or secrets in Function nodes.
- **Error Handling**: Use n8n’s built-in "Error Trigger" or catch nodes to handle failures gracefully (e.g., logging any unprocessed emails).
- **Iterate**: Start with a basic workflow and gradually add more filters or categories as you observe patterns in your ITB volume.

## Next Steps

Once you connect your Gmail account to the connector, I can run queries to analyse historical ITB volume and sender domains. Please authorise the Gmail connector when prompted. After that, we can refine the scoring thresholds and top GC list based on actual data.
