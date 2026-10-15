# Getting started with Prodigy

Implementation details: [ERP service — first-version tech spec](prodigy/services/erp.md).

Prodigy should be easy for an adult to set up and easy for a child to return to. Parents and teachers sign in with Google and verify their mobile number. Students do not need a Google account or their own phone number.

Each child has one student profile and one student access code. Their profile brings together all their classes, progress, and lesson notebooks.

## Two codes, two purposes

- **Student access code:** identifies the child and opens their learning space. It is private and should not be shared with classmates.
- **Class code:** identifies a teacher's class. The teacher can share it as a code or a link so students can join. It does not give access to anyone's profile.

A parent creates a student profile, not a class code. A teacher creates a class code for each class.

### Code format

Use short, case-insensitive alphanumeric codes with no vowels. Codes may be 4 or 6 characters; prefer 6 for student access because it opens a private profile. Display them in uppercase, for example `K7M9R2`. Avoid easily confused characters such as `0` and `1`. Generate codes randomly and check uniqueness within each code type. Keep student access codes separate from class invitation codes.

Four-character codes should be reserved for class invitations rather than student login. Student-code login needs server-side attempt limits and a way for an authorized adult to reset access.

## Welcome screen

Offer two clear paths:

- **I'm a student** — enter a student access code, or join using a class code.
- **I'm a parent or teacher** — continue with Google.

After an adult signs in for the first time, ask: **“How will you use Prodigy?”** with **Parent**, **Teacher**, and **Both** as options. Returning adults go straight to their dashboard. They can add another role later without creating another account.

## First time: parent

1. Continue with Google.
2. Verify a mobile number. Ask: **“What mobile number can we use for your account?”** Explain: “We'll send a code to verify it's yours.”
3. Choose the parent role and select **Add a child**.
4. Ask for the child's details:
   - **“What should we call your child?”** — name.
   - **“How old are they?”** — age.
   - **“Which grade are they in?”** — include “Not in school yet” and “Other.”
   - **“Which school board or curriculum do they follow?”** — include “I'm not sure.”
   - **“Would you like to add a photo?”** — optional; offer an avatar instead.
5. Ask what they want to work on:
   - **“Which subject would you like to start with?”**
   - **“How does your child feel about this subject?”** — “Finds it difficult,” “Comfortable with some parts,” “Enjoys it and wants a challenge,” or “I'm not sure yet.”
   - **“What would you most like us to help with?”** — understanding the basics, homework, confidence, exam preparation, or a new challenge.
   - **“Anything else you'd like the tutor to know?”** — optional free text, with an example such as “They understand the ideas but get nervous answering questions.”
6. Create the profile and show the child's **student access code**. Let the parent copy or print it, with a reminder to keep it private.
7. Offer **Start learning** and **Add another child**.

Keep the longer goal questions skippable and editable later. These answers guide the first conversation; they are not an assessment of the child's ability.

A child can start learning with Prodigy without joining a teacher's class. Their learning space shows **Learn with your tutor** alongside any classes they join later.

## First time: teacher

1. Continue with Google, verify a mobile number, and choose the teacher role.
2. Ask **“What should students call you?”**
3. Ask **“Where do you teach?”** — school or institute name, with “I teach independently” as an option.
4. Select **Create a class** and ask:
   - **“What would you like to call this class?”** — for example, “Grade 7 Maths.”
   - **“Which subject will you teach?”**
   - **“Which grade is this for?”** — allow a mixed-grade class.
   - **“Which board or curriculum does the class follow?”** — include “Not tied to one board.”
5. Show the class code and invitation link, with **Copy invitation** and **Add students** actions.

There are two ways to bring students in:

- **Students who already use Prodigy:** share the class invitation. They join using their existing student access code, keeping their current profile and progress. Teachers do not need to collect their private access codes.
- **Students who are new:** let the teacher add names quickly, including several students at once. Create a profile and student access code for each new child. Provide individual access slips to hand out privately, rather than a class-wide list of codes.

Before creating a profile, remind the teacher: **“Already using Prodigy? Ask the student to join with their existing access code.”** Do not assume two children with the same name are the same person.

A child's mobile number is not required. If parent contact details are collected, label them clearly as a parent's or guardian's number.

## Student: enter with an access code

1. Choose **I'm a student**.
2. Ask **“What's your student access code?”** with an **Enter** button.
3. Show **“Hi, Aarav. Ready to keep learning?”** and the child's learning space:
   - **Continue learning** — return to their current lesson.
   - **My classes** — all classes they belong to.
   - **Join a class** — enter another class code.
4. Ask **“Remember me on this device?”** with “Only choose this on a device you use yourself.” Leave it off by default on shared devices.

No Google sign-in or name selection is needed.

## Student: enter through a class invitation

1. Open the teacher's invitation link or choose **Join with a class code**.
2. Show the class name and teacher: **“Join Grade 7 Maths with Ms Meera.”** Do not show the student roster.
3. Ask for the student's access code to identify them. If already signed in, use their current profile and offer **Not you? Switch student**.
4. If they already belong to the class, open it directly.
5. Otherwise, show **Join this class**. Complete enrollment according to the class's joining setting.
6. The class now appears in **My classes** alongside their other classes.

If the child has no access code, offer **I don't have a code** and explain: **“Ask your parent or teacher to help you get started.”** Provide a way to return to adult setup. Do not leave the child facing a login form they cannot complete.

## Returning users

### Parent

Sign in with Google, then see their children, recent progress, and classes. Select a child to view their learning or help them get started. Do not ask them to choose a role again.

### Teacher

Sign in with Google, then see their classes. Open a class to see enrolled students, their progress, and what they are working on.

### Student

On a remembered personal device, offer **Continue as Aarav** and **Switch student**. Otherwise, ask for the student access code. Open the child's existing learning space rather than creating a new profile or restarting their progress.

## Other situations to cover

### Shared tablets and siblings

Keep **Switch student** easy to find. Switching signs out the previous child before another enters their code. A parent can select among their own children's profiles from the parent dashboard. Never show an entire class roster as a login shortcut.

### Lost or incorrect access code

For an invalid code, say **“That code didn't work. Check it and try again.”** Offer **Need help finding your code?** and direct the child to their parent or teacher.

A linked parent or authorized teacher can help reset access from their dashboard. Resetting a code must retain the same profile, classes, and progress and invalidate the old code. Adult recovery requires adult sign-in; knowing a child's name or class code is not enough.

### Invalid or expired class invitation

Say **“We couldn't find that class. Check the code with your teacher.”** Keep the student signed in and offer **Back to my classes**. Opening a class invitation twice must not create duplicate membership.

### Joining another class

Reuse the same student profile and access code. Each class has its own membership; joining a new class does not replace existing classes or erase learning progress.

### Linking a parent later

A teacher-created student profile may later be linked to a parent's account. Use a verified linking flow, not a name match, and retain the existing profile and progress. If duplicate profiles already exist, provide a support path rather than silently merging them.

### Leaving or archiving a class

Removing class membership must not delete the child's profile or personal learning history. An archived class should be clearly marked and should not accept new joins.

### Interrupted setup

Save completed setup steps so adults can return without entering everything again. If mobile verification fails, offer **Resend code** and **Change number** without restarting Google sign-in.

## Decisions still to make

- **Class enrollment:** should a valid invitation admit a student immediately, or should the teacher approve new joins? If approval is required, show “Your teacher will let you in soon” and let the child continue other learning.
- **Adult permissions:** define which linked adults can reset access, link a parent, or manage a child's profile. Teachers should see progress relevant to their own classes, not automatically every class a child attends.

These decisions should be settled before building enrollment and account recovery. The core journey stays the same: adults help establish access, students use one profile, and class codes connect that profile to classes.
