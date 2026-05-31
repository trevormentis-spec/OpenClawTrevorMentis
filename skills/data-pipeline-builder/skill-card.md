## Description: <br>
Build, schedule, and monitor ETL pipelines to extract, transform, and load data across databases, APIs, and file systems with error handling and validation. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[sky-lv](https://clawhub.ai/user/sky-lv) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Developers and data engineers use this skill to plan and operate ETL workflows across databases, APIs, object storage, and files, including transformation, scheduling, validation, monitoring, and incremental sync tasks. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Pipeline guidance may affect live data sources, destinations, or scheduled jobs if applied without review. <br>
Mitigation: Confirm sources and destinations, use least-privilege credentials, test with dry runs or non-production data first, and require explicit approval before writes or scheduling. <br>
Risk: Transformations or sync settings could produce incorrect data movement or reporting results. <br>
Mitigation: Review transformation logic, schema validation, data quality checks, and incremental sync behavior before running against production data. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/sky-lv/data-pipeline-builder) <br>
- [Source skill instructions](artifact/SKILL.md) <br>


## Skill Output: <br>
**Output Type(s):** [Text, Markdown, Shell commands, Configuration, Guidance] <br>
**Output Format:** [Markdown with command examples and configuration guidance] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [May include pipeline plans, connector choices, transformation steps, scheduling guidance, validation checks, and monitoring commands.] <br>

## Skill Version(s): <br>
1.0.0 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
