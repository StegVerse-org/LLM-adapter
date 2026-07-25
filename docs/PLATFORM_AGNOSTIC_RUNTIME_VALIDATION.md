# Platform-Agnostic Runtime Validation

This branch exists to execute the repository's provider-neutral OCI validation workflow against the current `main` runtime contract.

The workflow must build the same image, start it with only documented environment variables and a durable volume, verify HIL readiness and fixed provenance hashes, replace the container, and prove state survives replacement.

This validation does not select or endorse a hosting provider and grants no execution, publication, or Master Record authority.
