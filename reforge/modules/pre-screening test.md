**Objective**: Probable candidates would be given a pre-screening test to check them for motivation, general abilities, numeracy, and IQ.

Flow would be:
 - Administrator go to admin portal
 - Can see candidates there, or can add one more candidates
	 - The candidates who apply from site, would also be visible here
- For a candidate he can assign a test and define valid till (default coming Sunday)
	- Drop mails to candidate for test
- Candidate on his mail get a signed link, valid till specified date to do the exam
- Candidate opens the link before expiry
	- Opens a page in reforge.academy site (like reforge.academy/pre-screening/xzAD1212s)
	- Page do have quick info to fill, disclaimer, exam terms and instructions to follow
	- And a Start Test CTA
- Candidate clicks on Start CTA
	- Opens a new window, with very less control
	- The windows looks a lot like how an actual JFT Basic test online looks like
	- Loads test (backend deliver a random set from multiple sets in that test)
	- Test have sections and set of question in each section
	- Candidate can go back to all sections and see which all Qs he has marked, and he has not marked. He can jump quickly to a question

Rules
 - Candidate can only start a test once
 - If a window is killed, he cannot redo same test
 - Test are time-bound, after which they auto-submit. Re-attempting same test would display a message. Your test is submitted

Flow to create a test is:
 - Administrator go to admin portal
 - See tests
 - Create a new test
	 - Generate using AI
		 - Upload a md file
		 - Provide Gemini API key (stored in session storage)
		 - Parses and creates the JSON for test and setup all questions locally in UI
		 - Admin review questions
		 - Questions are splitted across sections
		 - There are different type of questions
		 - Few section can also have a reading page first, and then question basis that
		 - Some section's reading page can only be made visible only once (even if candidate jumps back to this section)
	- Or can create entire thing manually
	- Can create multiple sets by shuffling or by adding more md files

Rules:
 - Administrator portal is only visible to few specified email IDs and require gmail login