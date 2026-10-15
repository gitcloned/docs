# Objective

## What this is

LEAD Analyst is an MCP server that gives Claude Desktop the ability to query LEAD School data using plain English.

Analysts and support teams can investigate school issues, triage escalations, and answer data questions without writing SQL.

## Who it's for

- **Support analysts** — investigating school-level issues (device errors, resource failures, SD card corruption)
- **Operations teams** — tracking dispatch orders, school onboarding status
- **Anyone who needs answers from LEAD data** — without needing direct database access or SQL knowledge

## Core problems it solves

- Querying ClickHouse/Postgres requires SQL + direct DB access — most analysts don't have either
- Investigations are slow: find the right table, write the query, interpret the result
- Knowledge about which tables/columns matter is locked in people's heads

With LEAD Analyst, Claude handles the SQL. The analyst just asks the question.

## What it is NOT

- Not a dashboard or visualisation tool
- Not a replacement for direct DB access when complex custom queries are needed
- Not a real-time alerting system

[← Back to index](lead-anlayst.md)
