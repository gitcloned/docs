## Questions
1. How should spaced repetition be done with product? How does child sees that journey? How does it work with gaps where child is not studying regularly - what is a fair mix of learning and practice

## Points to improve

 - [ ] Simplify code flow for agent harness
	 - [ ] More pure functions
	 - [ ] very simple logs

## Modules to add

1. Question bank
2. Content creation pipeline
	1. How does the concept graph being made
	2. How does content links to concept graph - is it lesson plan
		1. Content could be video resources, questions
3. Ask anything and link it to content we have, what child have studied and his memory
	1. How does this link back to teaching or practice

#### Adaptive Retrieval Policies for Remediation and Scaffolding

Building on the curriculum graph and benchmark, this outcome will develop adaptive retrieval policies that dynamically select among different classes of content - 

(a) direct answer or explanation sources, 
(b) prerequisite or bridging concept material, and 
(c) worked examples or guided practice items. 

The selection will be conditioned on the student's query, inferred skill level, prior error patterns, and curriculum position. 

Rather than always retrieving the 'best match,' the system will decide what kind of content best supports learning in that moment. 

Evaluation will emphasize learning-oriented outcomes, including reduction in repeated misconceptions, improved performance on follow-up questions, and smoother progression through prerequisite chains.

#### Benchmark for Citation Correctness in Educational RAG

This outcome will create a benchmark where generated answers are required to cite precise supporting evidence from retrieved sources, such as text spans in textbooks, timestamps in educational videos, or spatial regions in scanned pages and diagrams. 

Each answer will be annotated with gold citation targets and acceptable citation alternatives.

Evaluation will go beyond surface citation presence to measure support faithfulness-whether the cited evidence genuinely justifies the corresponding claim in the answer. 

Metrics will include citation precision and recall, span/timestamp accuracy, and penalties for hallucinated, mismatched, or overly generic citations. 

The benchmark will enable systematic comparison of citation-aware generation methods and discourage superficial or symbolic grounding.