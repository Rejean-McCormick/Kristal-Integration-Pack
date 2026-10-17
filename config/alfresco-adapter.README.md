# Alfresco (optional — intentionally not active)

Do not add Alfresco to the core deployment. When an existing ACS repository is required:

1. Use a dedicated *read-only* ACS REST integration with its own principal.
2. Map `nodeId`, `versionId`, document SHA-256 and retrievable URI to **source references**,
   not to Kristal logical commitments.
3. Use explicit per-principal ACL filtering before adding items to a Kristal reading surface.
4. Snapshot the source/version metadata, document uncertainty and revalidation rules.
5. Never bypass ACS permissions by caching protected content in a public Context Pack.

This integration pack does **not** claim that an Alfresco connector is implemented.
