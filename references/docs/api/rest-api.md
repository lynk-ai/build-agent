---
description: HTTP endpoints for validating the semantic layer and inspecting the data catalog — full documentation in progress.
icon: globe
---

# REST API

The Lynk REST API provides HTTP endpoints for working with your semantic layer programmatically — validating a build and inspecting the data catalog (the warehouse tables and columns the layer points at) without using the Lynk UI. Schemas themselves are authored in the `.lynk/` git repository and deployed through the [build](../concepts/project.md), not edited over the API.

{% hint style="info" %}
Full REST API documentation is in progress. For current API access and endpoint details, contact your Lynk account team or visit [app.getlynk.ai](https://app.getlynk.ai).
{% endhint %}

---

## Related reference

- [Lynk SQL](./lynk-sql.md) — the query syntax the agent uses, which you can also use directly
- [Project](../concepts/project.md) — how a build is validated and deployed before it serves queries
