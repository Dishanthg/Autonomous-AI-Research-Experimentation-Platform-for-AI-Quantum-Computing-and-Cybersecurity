# Lessons Learned

1. **Structural constraints are testable; good intentions are not.** The
   difference between "the LLM is instructed not to fabricate claims" and
   "a unit test proves an ungrounded claim gets dropped" is the difference
   this whole project is about. Every rule in the spec (Rule 1-13) was only
   as real as the test that could falsify it.
2. **Deterministic code should own the parts of the pipeline where being
   wrong is unacceptable.** Statistics, conclusions, and the critic's
   blocking checks were built with zero LLM involvement specifically so
   their correctness doesn't depend on a model's mood.
3. **Environment failures are still failures worth recording.** The
   disk-space incident wasn't a design flaw, but pretending the Docker/Neo4j
   paths were verified when they weren't would have been exactly the kind of
   overclaiming this project exists to prevent. Writing "IMPLEMENTED — NOT
   VERIFIED" honestly is more useful than a green checkmark that isn't true.
4. **A generated script that "looks right" needs to actually run.** Two of
   the codegen templates had zero bugs when read, but running them
   (`test_codegen.py`) is what actually confirmed the metrics they produce
   are real numbers in valid ranges, not just plausible-looking code.
5. **Pinning matters more than usual when composing security-relevant
   libraries.** The bcrypt/passlib incompatibility was silent until the
   moment a real password was hashed — a reminder that a security-critical
   dependency pair needs its own compatibility test, not just "pip install
   and move on."
