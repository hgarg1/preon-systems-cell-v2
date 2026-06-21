# BI Exports Removed

The BI export pipeline was removed in the organism runtime reset.

Runtime observability now comes from `runtime_events`, `proteins`, `contracts`, and `structure_requests`. External analytics consumers should read those tables or the organism detail API instead of legacy run artifact bundles.
