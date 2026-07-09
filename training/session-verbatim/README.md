# Session Verbatim

This directory preserves selected verbatim or near-verbatim interaction material from work sessions.

These files are training artifacts. They capture what was said, how it was interpreted, how it was recorded, and what changed in the project as a result.

This is the rawest layer of the training record.

## Purpose

Session verbatim files help future work understand:

- the user's exact language
- the assistant's interpretation
- mistakes and corrections
- decisions made during the session
- how raw interaction became structured project material

## Relationship to other training records

```text
session-verbatim
  raw or near-raw interaction material

language
  extracted terms, phrasing, and user intent

observations
  structured readings of screenshots or game state

corrections
  mistakes, fixes, and recognition rules

project-notes
  polished handoff material for future threads
```

## What belongs here

Use this directory when the exact wording matters.

Good candidates include:

- user explanations of game mechanics
- assistant interpretations that were later corrected
- exchanges that produced new recognition rules
- project framing language
- decisions about how the workbench should behave

## What does not belong here

Do not use this directory as an automatic dump of every chat transcript.

Before committing verbatim material, remove anything that should not become public project history, including private paths, unrelated personal details, credentials, account identifiers, or operationally sensitive information.

## Core rule

Preserve enough raw interaction for future training, but keep the public repository intentional.
