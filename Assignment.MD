Snowflake Applied AI:
Candidate homework assignment
Overview
Your task is to build a production-quality, interactive chat agent that can answer natural language questions about the US population. This is not a prototype exercise — we are evaluating how you approach building something you would be comfortable deploying and handing off to a customer.


You have 24 hours from the time you receive this assignment to submit your work.


⚠️ Note

We intentionally leave several technical decisions open-ended. Your choices — and your ability to explain and defend them — are a core part of what we are evaluating.

Data
Using a free Snowflake trial account, connect to the US Open Census dataset available on the Snowflake Marketplace. This is your required data source. How you query, transform, and serve that data is entirely up to you.

Requirements
Core Functionality
Build an interactive, chat-based agent that answers natural language questions grounded in the US Census dataset.

Provide a web-based interface accessible on the public internet (no local setup required to evaluate your submission).

The agent must preserve conversation context across multiple turns.

Complete responses must be returned within 60 seconds under normal conditions.

Apply guardrails to prevent off-topic or inappropriate responses.


Production Quality Bar
Your submission should reflect the standards you would apply to code being handed off to a customer. 

Specifically:

The agent must degrade gracefully. If a query cannot be answered given the available data, the agent should say so clearly and helpfully rather than hallucinating, returning an empty response, or throwing an unhandled error.

Consider and handle ambiguous queries, queries that partially match available data, conflicting or underspecified questions, and queries that are reasonable but unanswerable given the dataset.

Include meaningful tests that give us confidence in your implementation. You decide the scope and approach — but be prepared to explain your testing strategy and its tradeoffs.

Your README should make it easy for a new engineer to understand your architecture and for us to evaluate your running demo.


💡 Tip

We are not expecting perfection across every dimension given the time constraint. We are evaluating your judgment about where to invest and your self-awareness about the tradeoffs you made.

Deliverables
Within 24 hours, email a link to a private GitHub repository shared with sfc-gh-sgolebiewski, sfc-gh-setli and sfc-gh-nwiegand.

The repository must include:
All code written to implement your solution.

Instructions for accessing your running web application, including credentials if authentication is required.

A written reflection (markdown) covering:

Your development process and key architectural decisions.

What you would improve or do differently with more time.

Any edge cases or failure modes you identified but did not fully address.

How you approached testing and what you would add to the test suite.

What We Are Evaluating
We review submissions across four dimensions:

Dimension

What we look for

LLM / AI Engineering

Does the solution demonstrate genuine understanding of how to build data-grounded chat agents? Are the architectural choices defensible?

Production Quality

Is the code something you would ship? How does the agent behave under ambiguous, incomplete, or adversarial inputs?

Judgment Under Constraints

Given 24 hours, where did you invest your time? What did you deliberately leave out and why?

Reflection & Self-Awareness

Does the written reflection show honest assessment of tradeoffs and clear thinking about what could be improved?


FAQs
Q: Do I need to build and run my solution exclusively on the Snowflake platform?

A: No. The data is available through Snowflake Marketplace but you are free to develop your application however you wish.


Q: Is it ok if viewing the demo requires authentication?

A: Yes, provided you include credentials in your submission so we can access it.


Q: Can I use AI coding tools to help build the solution?

A: Yes, and we encourage it. Part of what we are evaluating is how effectively you use the tools available to you. Be prepared to discuss how you used them during the follow-up review.


Q: What if I cannot finish everything in 24 hours?

A: Submit what you have. Use your written reflection to explain what you would have done with more time. Incomplete submissions that show strong judgment and self-awareness will score better than complete submissions that lack them.


Questions?

If you have a clarifying question about the requirements, use your best judgment and document your interpretation in your README. This is itself a signal we evaluate.



Jeśli potrzebujesz więcej informacji, daj znać!
