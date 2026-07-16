# Insulating Glove Test Data Pipeline

**MAIDA 211 — AI and Analytics Special Topics — Milestone 1**

## Project and Model

Field electrical crews wear rubber insulating gloves as primary protection against electric shock. Regulations (ASTM F496 / OSHA) require these gloves to be periodically dielectric-tested; a glove that leaks more than 3.00 mA under test fails and must be pulled from service. Today, test results are exported from the test-bench system into a spreadsheet and reviewed manually — there is no model and no automated pipeline. The eventual model (built in later milestones) will predict whether a glove is likely to Pass or Fail its next test from its usage history (age, number of usage cycles, number of owners, brand/material), so the safety team can proactively flag and replace high-risk gloves before they fail a live test, instead of only finding out at test time. This repository implements Milestone 1: the data pipeline that reads the raw test-result extract, enforces a data-quality contract, and writes a clean, versioned artifact for the modeling work in Milestone 2.

## Repository Structure
