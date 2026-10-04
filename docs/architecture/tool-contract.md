# Tool validation contract

Business tools belong to Core and do not inherit from PydanticAI Tool. Parameters
are a Pydantic BaseModel subclass; the adapter owns upstream schema conversion.

The PydanticAI 2.54.0 adapter does not rely on `Tool.from_schema` to validate our
business parameter model. The implemented bridge executes this before any business side effect:

```python
validated = parameters.model_validate(raw_args)
```

Only then may it call the business tool with context and the validated object.
Choose strict validation and `extra="forbid"` on the business parameter model when
required; the bridge must respect that model rather than inventing a parallel DSL.
Catch parameter ValidationError and translate it to a safe retry signal without
disclosing raw sensitive inputs. Do not invoke the tool first. Do not translate all
ordinary business exceptions into parameter retries or repeat side effects blindly.

Phase 1B uses a positional-only injected RunContext and passes the original ctx.deps
to invoke; the injected argument does not appear in the business parameter schema.
Strict types and extra="forbid" are enforced when specified by the parameter model.
ValidationError becomes a generic ModelRetry; the business invocation sits outside
that exception handler, so ordinary business failures propagate.

Offline regression tests migrate Phase 0's invalid -> retry -> valid scenario and
verify exactly one side effect for that corrected call, zero calls on invalid input,
JSON-compatible tool results, and heterogeneous parameter models. This is not a
general exactly-once guarantee. The JSON return contract remains a typed obligation
of business tools, not a new adapter coercion/serialization policy.

Historical Phase 0 source: [Tool.from_schema at the original 2.48.0 baseline](https://github.com/pydantic/pydantic-ai/blob/06be8e7a0056d6c6c72d2868f6b26ee8e7364c77/pydantic_ai_slim/pydantic_ai/tools.py).
