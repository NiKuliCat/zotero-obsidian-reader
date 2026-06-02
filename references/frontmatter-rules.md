# Frontmatter Rules

When generating analytical frontmatter, the agent must extract and compress. Do not paste long fragments from the abstract.

Global rules:

- Every analytical frontmatter field must be one sentence only.
- Preferred length: 10-30 Chinese characters when possible.
- Do not repeat the same statement across `theme`, `methodology`, and `key_finding`.
- If evidence is insufficient, use a short conservative placeholder instead of inventing details.

## `theme`

- Meaning: one-sentence summary of the core research problem.
- Must be distilled, not copied.
- Bad: copying the opening of the abstract.
- Good: `探讨城市创新空间生态位适宜性的评价指标与空间格局。`

## `study_area`

- Meaning: real study area, sample range, or research object.
- Must be strictly grounded in title and abstract.
- Never hallucinate familiar cities or common regions.
- Bad: `北京、上海等`
- Good: `江苏省南京市。`

## `data_source`

- Meaning: data provider, database name, or time span.
- Only include the true source or temporal coverage.
- Never include author affiliation, postal code, or abstract preamble.
- Bad: `作者单位...摘要...`
- Good: `南京市统计局数据及地理空间矢量数据，年份为2020年。`

## `methodology`

- Meaning: concrete model, framework, or analysis tool.
- Must name the actual method.
- Must not duplicate `theme`.
- Bad: `基于生态位视角探讨...`
- Good: `构建三维评价指标体系，并结合GIS空间分析方法。`

## `core_variable`

- Meaning: actual variables, indicators, or evaluation dimensions.
- Extract concrete variables or dimensions.
- Do not dump the paper keywords.
- Bad: `创新经济地理、创新生态系统`
- Good: `资源生态位、环境生态位、技术生态位适宜度。`

## `key_finding`

- Meaning: the single most important conclusion.
- Remove filler such as `结果表明` or `研究发现`.
- Keep only the conclusion itself.

## `relevance`

- Meaning: the paper's concrete value for the user's topic.
- Must name a specific point of value: benchmark case, measurable indicator, methodological reference, comparison baseline, etc.
- Reject vague filler such as `可用于补充文献脉络`.

## Required behavior

- Generate these fields only after understanding enough evidence to separate them cleanly.
- Use title, abstract, notes, annotations, and fulltext when needed.
- Never treat frontmatter as a metadata dump.
