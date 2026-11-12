# Frontend device verification — 10 November 2026

Build and Android lint passed. Six matching/progress unit tests passed with zero failures.

Verified in an isolated QA package on the connected Android emulator:

- Welcome, three intro pages, sign-up, login and password reset are reachable.
- Invalid email feedback appears; onboarding accepts profile details, skill choices and a placement goal.
- A profile with HTML, CSS and Git receives 75% for a four-skill frontend role. The next visible role ranks lower at 25%.
- Role details scroll to responsibilities, requirements, eligibility and final preparation actions. The Requirements shortcut jumps to its section.
- Selecting a role focuses Growth on its missing skills.
- Saving a learning reflection updates completion, XP, streak and You. The revised footer remains available and saves back to Growth.
- The floating coach explains the current match correctly and accepts text while the keyboard is open; Send remains reachable.
- The You page scrolls to the completed learning evidence.
- The CV form scrolls to Preview and displays the entered contact/education/skills data.
- Saved roles appear in the RecyclerView screen.

QA uses a separate app ID; the main app's profile was not overwritten by test data. Screenshots are in output/screenshots. The debug APK is in output/apk.

Not claimed as verified: production account creation, model-generated recommendations/chat, real applications, physical-device performance, comprehensive TalkBack or large-font coverage. These require the corresponding integration/device testing.

## Additional verification: course links / scrolling / PDF

Eight unit tests passed, including coverage of every learning skill's HTTPS programme mapping and cache invalidation after editing a profile.

On the emulator: the main opportunities list reached its lower items and retained its position when switching to Growth and back. The course button dispatched an official Coursera programme URI to Chrome; Chrome's initial first-use setup requires the user's choice, so enrolment was not performed. Direct PDF saving opened Android's native picker, saved a uniquely named QA PDF, showed success and produced a readable one-page PDF with the entered fictional name, email, location, education and skills. The PDF was extracted and rendered for inspection.

Optimized APK size is approximately 2 MB (previous debug package approximately 10 MB). Package size reduction is not itself a frame-time or startup benchmark. First-run timings observed while Gradle was compiling are not used for performance claims.

### Local startup measurement

With Gradle idle, the installed optimized preview's three force-stopped Activity launches reported first-display times of 10,602 / 4,422 / 4,355 ms (median 4,422 ms). After explicitly precompiling only this package on the emulator using `cmd package compile -m speed -f ke.upshift.app`, three launches reported 2,297 / 2,271 / 2,961 ms (median 2,297 ms). These are local `am start -W` Activity display times, not fully-interactive, physical-device or first-install benchmarks. The ART compilation step changes the emulator's compilation state and is not automatically reproduced simply by installing the APK on another device.
