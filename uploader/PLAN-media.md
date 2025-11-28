TODO: migrate media upload material from PLAN.md to here.

## 2025-11-28 improvements

Update the upload media (`uploadMedia.js` etc) to in command line mode:

- [ ] have a total list of files to upload (calculate at start)
- [ ] have a progress counter at the top showing total files uploaded and percentage complete
- [ ] just show the latest file processed and current file(s) (if multiple files) being processed (rather than log each file to console)
- [ ] write to map as we go along ... (rather than just at the end and ensure we write if the process exits badly)

Investigate how to parallelize upload without compromising the integrity of the map and propose if this possible (probably parallelize no more than 5-10 files at a time)

- [ ] parallelize upload (may be a tension with writing the map ... but if we have an overall process that is delegating files to upload should not be a problem)

## 2025-11-28 part 2 improvements

- [x] Progress updates must redraw in place (single-line status with spinner) instead of spooling the terminal.
  - Use `stdout.isTTY` guard; fallback to simple logging if not TTY.
  - Show spinner + counts: `⟳ uploading 3/42 (7%) :: current: foo.png`.
  - When logging a completed upload/skip/failure, temporarily write a newline, then resume spinner on the next tick.
  - Stop the spinner cleanly on exit (success or error) and print a final summary line.
  - Keep overall progress counters consistent with the totals calculated at start.
  - Track and display ongoing totals (uploaded, skipped, failed) in the spinner line so it’s always visible without scrolling.

Ask me to clarify what i mean if you need help.

## 2025-11-28 part 3 improvements

- [x] log errors specifically to terminal in a different color and log them in background to a simple log file e.g. `upload_media_errors.log`
