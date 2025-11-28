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

- [ ] log errors specifically to terminal in a different color and log them in background to a simple log file e.g. `upload_media_errors.log`
