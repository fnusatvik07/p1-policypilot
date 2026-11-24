# P1-POLICYPILOT walkthrough: narration script

Generic on purpose (no dates), so it can be reused for every cohort.

## Hook

A customer calls their bank. “I never made this purchase.” ... From that second, a federal clock starts ticking. Ten business days to give provisional credit. Forty-five days to finish the investigation. Miss it... and the regulator notices.

## Why this happens

And banks do miss it. Not because nobody knows the rule... but because the right answer is buried in the wrong version of the wrong document. A memo quietly changed a threshold. An old wiki page is still linked. Two documents disagree. Every year, the CFPB orders banks and fintechs to pay millions for exactly this.

## Welcome

Welcome to Project One. PolicyPilot! You are joining the card and payment disputes team at Harborline Bank... and your job is to build the assistant every analyst wishes they had.

## Problem statement

Here's the problem. Analysts ask two questions all day. What is the rule? And was it followed? The answer depends on Regulation E for debit cards and transfers, Regulation Z for credit cards, and hundreds of internal documents that keep changing. And every question has a date.

## What we are looking for

So what are we looking for? An assistant you can trust. Every answer cited: document, version, exact quote. Answers as of any date. It knows what is active, superseded, or retired. It spots conflicts and says which source wins. It calculates business-day deadlines with a real tool. It queries the case database. And when the answer isn't there... it says so.

## What the data looks like

Here's what you get. Three hundred sixty-four bank documents from five systems: policies, procedures, wiki pages, memos and emails, in six file types. A document registry. A disputes case database with thousands of cases and hundreds of thousands of transactions. Real regulations with their full version history, real CFPB guidance and enforcement orders, and more than fifty thousand real consumer complaints. Plus live government APIs.

## The change feed

And the library won't sit still. During the project, change releases arrive. New versions. Retired pages. Deleted files. Your system has to absorb them... and its answers have to change with them.

## What we expect you to build

What do we expect you to build? An ingestion pipeline for every source. An index, plus a knowledge graph that links documents to regulations. An agent loop that plans, retrieves, and calls tools. A change feed processor. An evaluation harness. And a simple interface to ask questions.

## How you are evaluated

You get one hundred seventeen public questions across ten types. As-of questions, conflicts, deadline math, database lookups, multi-hop chains, and questions with no answer at all. Your system will also face hidden questions. So build for the problem... not for the test.

## What to submit

What do you submit? Your code repository, with a README that runs end to end. Predictions for every public question. An architecture write-up. An evaluation report, before and after each change release. A change feed log. And a five to eight minute demo video.

## Close

Everything is in the project repository: the problem statement, the data guide, the live APIs, and the submission rules. Read it. Explore the data. Start building. Welcome to Project One... let's build PolicyPilot.
