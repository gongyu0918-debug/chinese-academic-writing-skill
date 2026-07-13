# H06 writer-b first attempt

- Candidate: `717e32db49c4b9ef8978da339b192a8ae4c285ec`
- Initial result: the old deterministic literal gate required the entire phrase `未编码材料不进入本次分析`; the output also omitted an explicit reference to unencoded material.
- Reproduction: three independent outputs across both writer cohorts preserved the exclusion by using natural variants such as `不纳入`, showing that the whole-phrase literal was overconstrained.
- Decision: retain this raw failed attempt, leave the runtime Prompt unchanged, and narrow the fixture invariant to `未编码材料` plus the existing fact and citation literals.
