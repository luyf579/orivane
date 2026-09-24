# Tool validation contract

Business tools belong to Core and do not inherit from PydanticAI Tool. Parameters
are a Pydantic BaseModel subclass; the adapter owns upstream schema conversion.

PydanticAI 2.48.0 `Tool.from_schema` does not perform strong validation using our
business parameter model. A future bridge must execute this before any side effect:

```python
validated = parameters.model_validate(raw_args)
```

Only then may it call the business tool with context and the validated object.
Choose strict validation and `extra="forbid"` on the business parameter model when
required; the bridge must respect that model rather than inventing a parallel DSL.
Catch parameter ValidationError and translate it to a safe retry signal without
disclosing raw sensitive inputs. Do not invoke the tool first. Do not translate all
ordinary business exceptions into parameter retries or repeat side effects blindly.

Phase 1A stores the definition; it does not implement this bridge. Phase 0 used a
FunctionModel probe to verify invalid arguments -> retry -> valid arguments -> one
business side effect. The production bridge must retain an equivalent regression test.

Source: [Tool.from_schema at the tested baseline](https://github.com/pydantic/pydantic-ai/blob/06be8e7a0056d6c6c72d2868f6b26ee8e7364c77/pydantic_ai_slim/pydantic_ai/tools.py).
